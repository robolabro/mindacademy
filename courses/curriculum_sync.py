"""
Sincronizare curriculum Airtable → Django (unidirecțional).

Airtable e sursa de adevăr pentru CONȚINUTUL curriculumului (cursuri, module,
lecții cu obiective/materiale). Django păstrează o copie locală pentru afișare
rapidă și robustă. Comportamentul de aplicație (milestones bifate, progres)
rămâne în Django.

Structura oglindește 1:1:  Airtable Course → Module → Lessons Template
                           Django   Course → Module → LessonTemplate

Maparea de câmpuri e izolată în `FIELD_MAP` de mai jos — singurul loc de
ajustat după ce se confirmă numele exacte din Airtable.

`fetch_airtable_records()` face doar I/O (pyairtable); `upsert_curriculum()`
e logică pură, testabilă cu date simulate (fără Airtable live).
"""
from django.db import transaction
from django.utils.text import slugify

from .models import Course, Module, LessonTemplate


# ── Maparea Airtable → Django ────────────────────────────────────────────────
# Numele de TABELE și CÂMPURI din Airtable. De confirmat/ajustat o singură dată
# după reconectarea Airtable (schema bazei cu tabelul Module).
FIELD_MAP = {
    'course_table': 'Courses',
    'module_table': 'Module',
    'lesson_table': 'Lessons Template',
    'course': {
        'name': 'Course Name',        # → Course.title
        'description': 'Description',  # → Course.description
    },
    'module': {
        'name': 'Name',               # → Module.name
        'description': 'Description',
        'order': 'Order',             # numeric (opțional)
        'course_link': 'Course',      # link către Courses (listă de record id-uri)
    },
    'lesson': {
        'name': 'Topic',              # → LessonTemplate.name
        'objectives': 'Objectives',   # → LessonTemplate.objectives (text liber)
        'materials': 'Materials',     # → LessonTemplate.materials
        'order': 'Lesson #',          # → LessonTemplate.order (numeric sau „Lecția 3")
        'module_link': 'Module',      # link către Module
    },
}


def fetch_airtable_records(token, base_id, field_map=FIELD_MAP):
    """
    Aduce înregistrările din Airtable. Returnează (courses, modules, lessons),
    fiecare o listă de dict-uri { 'id': <airtable_id>, 'fields': {...} }.
    Importat lazy ca aplicația să pornească și fără pyairtable instalat.
    """
    from pyairtable import Api  # lazy import

    api = Api(token)

    def all_rows(table_name):
        table = api.table(base_id, table_name)
        return [{'id': r['id'], 'fields': r.get('fields', {})} for r in table.all()]

    return (
        all_rows(field_map['course_table']),
        all_rows(field_map['module_table']),
        all_rows(field_map['lesson_table']),
    )


def _first(value):
    """Airtable link/lookup fields sunt liste — luăm primul element."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _order_int(value, fallback):
    """Extrage un întreg din „Lesson #" (poate fi 3, '3', 'Lecția 3')."""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        digits = ''.join(ch for ch in value if ch.isdigit())
        if digits:
            return int(digits)
    return fallback


@transaction.atomic
def upsert_curriculum(courses, modules, lessons, field_map=FIELD_MAP,
                      dry_run=False, log=None):
    """
    Upsert idempotent după `airtable_id`. Logică pură (fără I/O de rețea),
    testabilă cu liste de dict-uri simulate.

    Returnează un dict cu contoare: created/updated per nivel.
    """
    log = log or (lambda *a, **k: None)
    stats = {'courses': [0, 0], 'modules': [0, 0], 'lessons': [0, 0]}  # [created, updated]

    cmap = field_map['course']
    mmap = field_map['module']
    lmap = field_map['lesson']

    # index airtable_id → obiect Django, ca să legăm modulele/lecțiile de părinți
    course_by_air = {}
    module_by_air = {}

    # ── Cursuri ──────────────────────────────────────────────────────────
    for rec in courses:
        f = rec['fields']
        title = (f.get(cmap['name']) or '').strip()
        if not title:
            continue
        obj = Course.objects.filter(airtable_id=rec['id']).first()
        if obj is None:
            # prima sincronizare: adoptă un curs existent cu același titlu
            # (care nu e deja legat de alt record Airtable), ca să nu dublăm
            obj = Course.objects.filter(title__iexact=title, airtable_id='').first()
            if obj is not None:
                obj.airtable_id = rec['id']
        created = obj is None
        if obj is None:
            # nu suprascriem cursuri publice existente fără airtable_id;
            # creăm doar dacă lipsește complet
            obj = Course(airtable_id=rec['id'])
            obj.slug = _unique_course_slug(title)
            obj.price = 0
            obj.frequency = ''
            obj.group_size = 8
        obj.title = title
        obj.description = f.get(cmap.get('description'), '') or obj.description or ''
        if not dry_run:
            obj.save()
        course_by_air[rec['id']] = obj
        stats['courses'][0 if created else 1] += 1
        log(f"  {'+ creat' if created else '~ actualizat'} curs: {title}")

    # ── Module ───────────────────────────────────────────────────────────
    for idx, rec in enumerate(modules, start=1):
        f = rec['fields']
        name = (f.get(mmap['name']) or '').strip()
        parent_air = _first(f.get(mmap['course_link']))
        parent = course_by_air.get(parent_air)
        if not name or parent is None:
            log(f"  ! modul sărit (nume sau curs lipsă): {rec['id']}")
            continue
        obj = Module.objects.filter(airtable_id=rec['id']).first()
        if obj is None and not dry_run and parent.pk is not None:
            obj = Module.objects.filter(course=parent, name__iexact=name, airtable_id='').first()
            if obj is not None:
                obj.airtable_id = rec['id']
        created = obj is None
        if obj is None:
            obj = Module(airtable_id=rec['id'])
        obj.course = parent
        obj.name = name
        obj.description = f.get(mmap.get('description'), '') or ''
        obj.order = _order_int(f.get(mmap.get('order')), idx)
        obj.order = _dedupe_order(Module, parent, obj, dry_run=dry_run)
        if not dry_run:
            obj.save()
        module_by_air[rec['id']] = obj
        stats['modules'][0 if created else 1] += 1
        log(f"  {'+ creat' if created else '~ actualizat'} modul: {parent.title} / {name}")

    # ── Lecții ───────────────────────────────────────────────────────────
    for idx, rec in enumerate(lessons, start=1):
        f = rec['fields']
        name = (f.get(lmap['name']) or '').strip()
        parent_air = _first(f.get(lmap['module_link']))
        parent = module_by_air.get(parent_air)
        if not name or parent is None:
            log(f"  ! lecție sărită (nume sau modul lipsă): {rec['id']}")
            continue
        obj = LessonTemplate.objects.filter(airtable_id=rec['id']).first()
        if obj is None and not dry_run and parent.pk is not None:
            obj = LessonTemplate.objects.filter(module=parent, name__iexact=name, airtable_id='').first()
            if obj is not None:
                obj.airtable_id = rec['id']
        created = obj is None
        if obj is None:
            obj = LessonTemplate(airtable_id=rec['id'])
        obj.module = parent
        obj.name = name
        obj.objectives = f.get(lmap.get('objectives'), '') or ''
        obj.materials = f.get(lmap.get('materials'), '') or ''
        obj.order = _order_int(f.get(lmap.get('order')), idx)
        obj.order = _dedupe_order(LessonTemplate, parent, obj, parent_field='module', dry_run=dry_run)
        if not dry_run:
            obj.save()
        stats['lessons'][0 if created else 1] += 1
        log(f"  {'+ creat' if created else '~ actualizat'} lecție: {name}")

    return stats


def _unique_course_slug(title):
    base = slugify(title) or 'curs'
    slug, i = base, 1
    while Course.objects.filter(slug=slug).exists():
        i += 1
        slug = f"{base}-{i}"
    return slug


def _dedupe_order(model, parent, obj, parent_field='course', dry_run=False):
    """
    `Module` și `LessonTemplate` au unique_together=(parent, order). Dacă
    ordinea din Airtable se ciocnește cu alt obiect (nu al nostru), alegem
    următoarea valoare liberă ca să nu pice save(). În dry-run părinții pot fi
    nesalvați, așa că sărim verificarea în DB (oricum nu se scrie nimic).
    """
    order = obj.order
    if dry_run or parent.pk is None:
        return order
    filt = {parent_field: parent, 'order': order}
    clash = model.objects.filter(**filt).exclude(pk=obj.pk or -1).exists()
    if not clash:
        return order
    taken = set(model.objects.filter(**{parent_field: parent}).values_list('order', flat=True))
    n = order
    while n in taken:
        n += 1
    return n
