"""
Pull Airtable → Django (Epic 7, Faza 2).

Airtable = sursa de adevăr pentru STRUCTURĂ. Aici DOAR CITIM din Airtable și
scriem în Django. Nu scriem nimic în Airtable în această fază.

Reguli dure (din specificație):
  - Upsert ÎNTOTDEAUNA după `airtable_record_id` (niciodată după nume — copiii
    pot avea nume identice).
  - Fără ștergeri automate: înregistrările care dispar din Airtable se
    marchează `is_archived=True`.
  - „Lectii" (Lesson) = doar UPDATE, niciodată CREATE (lecțiile sunt generate
    de automatizări Airtable). Dacă nu găsim lecția după record_id, logăm
    eroare și mergem mai departe — NU creăm.
  - Doar înscrierile cu status „Inscris" sunt considerate active.
  - Câmpurile formula/lookup/rollup/count din Airtable sunt read-only — nu le
    scriem niciodată înapoi (irelevant aici, doar citim).
  - `--dry-run` nu scrie nimic în DB. `--grupa=COD` restrânge la o singură
    grupă (pilotul obligatoriu înainte de rularea pe toată baza).

NOTĂ despre numele câmpurilor: numele exacte ale coloanelor din bază nu au fost
încă confirmate pe viu. Toate accesele trec prin `pick()` / `pick_link()` cu
mai mulți candidați și pot fi ajustate rapid după `--show-schema`. Logica de
sincronizare (upsert/archive/update-only/filtrare) este independentă de aceste
nume și este acoperită de teste cu client simulat.
"""
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import User, StudentProfile
from courses.models import Course, Module, LessonTemplate
from teacher_platform.models import Group, Enrollment, Lesson
from crm_sync.models import SyncLog


# ---------------------------------------------------------------------------
# Helpers de citire tolerantă a câmpurilor Airtable
# ---------------------------------------------------------------------------
def pick(fields, *names, default=None):
    """Prima valoare non-goală dintre câmpurile candidate."""
    for n in names:
        if n in fields:
            v = fields[n]
            if v not in (None, '', []):
                return v
    return default


def pick_link(fields, *names):
    """Lista de record-id-uri dintr-un câmp de tip linked-record (sau [])."""
    for n in names:
        v = fields.get(n)
        if isinstance(v, list) and v:
            return [x for x in v if isinstance(x, str) and x.startswith('rec')]
    return []


def first_link(fields, *names):
    links = pick_link(fields, *names)
    return links[0] if links else None


# ---------------------------------------------------------------------------
# Sursa implicită de date (Airtable live). Injectabilă în teste.
# ---------------------------------------------------------------------------
def _live_fetch(table_id):
    from crm_sync.airtable_client import fetch_all
    return fetch_all(table_id)


class PullSync:
    """
    Orchestrează pull-ul în ordinea dependențelor și ține un map
    airtable_record_id → obiect Django per entitate pentru rezolvarea link-urilor.
    """

    def __init__(self, dry_run=False, grupa=None, fetch=None, log=None,
                 create_missing_teachers=False):
        self.dry_run = dry_run
        self.grupa = (grupa or '').strip()  # filtru pilot pe „Cod Grupa"
        self.fetch = fetch or _live_fetch
        self.log = log or (lambda msg: None)
        self.create_missing_teachers = create_missing_teachers
        self._profesori_by_id = None
        self._unmatched_teachers = set()
        self.active_statuses = set(
            getattr(settings, 'AIRTABLE_GROUP_ACTIVE_STATUSES', ['Active']))

        self.stats = defaultdict(lambda: dict(created=0, updated=0, archived=0,
                                              skipped=0, errors=0))
        self.errors = []
        # map-uri de rezolvare a link-urilor
        self.map_module = {}       # rec -> Module
        self.map_lesson_tpl = {}   # rec -> LessonTemplate
        self.map_group = {}        # rec -> Group
        self.map_student = {}      # rec -> User(student)
        self.map_teacher = {}      # rec -> User(teacher)

    # -- utilitare -----------------------------------------------------------
    def _t(self, key):
        return getattr(settings, key)

    def _err(self, entity, rec_id, message):
        self.stats[entity]['errors'] += 1
        self.errors.append(f"[{entity}] {rec_id}: {message}")
        self.log(f"  ! EROARE {entity} {rec_id}: {message}")

    def _upsert(self, entity, model, rec_id, values, id_map=None):
        """
        Găsește după airtable_record_id și actualizează, sau creează.
        În dry_run nu scrie; simulează find (pentru rezolvarea link-urilor
        folosește obiectul existent dacă e găsit, altfel un obiect ne-salvat).
        Returnează (obj, action) unde action ∈ {'created','updated','noop'}.
        """
        existing = model.objects.filter(airtable_record_id=rec_id).first()
        if existing:
            action = 'updated'
            obj = existing
        else:
            action = 'created'
            obj = model(airtable_record_id=rec_id)

        for k, v in values.items():
            setattr(obj, k, v)
        obj.is_archived = False
        obj.sync_status = 'synced'
        obj.sync_error = ''
        obj.airtable_synced_at = timezone.now()

        if not self.dry_run:
            obj.save()

        self.stats[entity][action] += 1
        if id_map is not None:
            id_map[rec_id] = obj
        return obj, action

    def _archive_missing(self, entity, model, seen_ids, base_qs=None):
        """Marchează is_archived=True înregistrările cu record_id care nu mai
        apar în Airtable (nu șterge niciodată)."""
        qs = base_qs if base_qs is not None else model.objects.all()
        qs = qs.exclude(airtable_record_id='').exclude(airtable_record_id__isnull=True)
        qs = qs.exclude(airtable_record_id__in=list(seen_ids)).exclude(is_archived=True)
        count = qs.count()
        if count and not self.dry_run:
            qs.update(is_archived=True, sync_status='synced',
                      airtable_synced_at=timezone.now())
        self.stats[entity]['archived'] += count

    # -- rezolvarea profesorului pentru grupele nou-create ------------------
    def _default_teacher(self):
        """
        Profesorul atribuit grupelor create din Airtable când nu putem rezolva
        unul din legături. Ordine: username din setări → primul role=teacher →
        primul superuser. Rezultatul e cache-uit.
        """
        if hasattr(self, '_teacher_cache'):
            return self._teacher_cache
        teacher = None
        uname = getattr(settings, 'AIRTABLE_SYNC_DEFAULT_TEACHER_USERNAME', '')
        if uname:
            teacher = User.objects.filter(username=uname).first()
        if teacher is None:
            teacher = User.objects.filter(role='teacher').first()
        if teacher is None:
            teacher = User.objects.filter(is_superuser=True).first()
        self._teacher_cache = teacher
        return teacher

    @staticmethod
    def _parse_time(value):
        from datetime import time as _t
        if not value:
            return None
        s = str(value)
        # acceptă „HH:MM" sau „HH:MM:SS" sau ISO cu „T"
        if 'T' in s:
            s = s.split('T', 1)[1]
        parts = s.split(':')
        try:
            h = int(parts[0]); m = int(parts[1]) if len(parts) > 1 else 0
            return _t(h % 24, m % 60)
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_datetime(value):
        """Parsează un dateTime ISO Airtable → datetime aware (sau None)."""
        if not value:
            return None
        from django.utils.dateparse import parse_datetime, parse_date
        s = str(value)
        dt = parse_datetime(s)
        if dt is not None:
            return dt
        d = parse_date(s)
        if d is not None:
            from datetime import datetime, time as _t
            return datetime.combine(d, _t(0, 0))
        return None

    # -- rezolvarea profesorilor (lazy, doar cei folosiți de grupele sincronizate) --
    @staticmethod
    def _norm_name(s):
        """Normalizează un nume pentru potrivire: fără diacritice, lowercase."""
        import unicodedata
        s = unicodedata.normalize('NFKD', str(s or ''))
        s = ''.join(c for c in s if not unicodedata.combining(c))
        return ' '.join(s.lower().split())

    def _load_profesori(self):
        """Încarcă o singură dată tabelul Profesori într-un dict {rec_id: fields}."""
        if getattr(self, '_profesori_by_id', None) is not None:
            return
        self._profesori_by_id = {}
        try:
            for r in self.fetch(self._t('AIRTABLE_TABLE_PROFESORI')):
                self._profesori_by_id[r['id']] = r.get('fields', {})
        except Exception as exc:  # pragma: no cover
            self._err('Profesori', '-', exc)

    def _match_teacher(self, rec_id, first, last, email):
        """Găsește profesorul Django existent: airtable_record_id → email →
        nume normalizat → (nume de familie identic + prenume prefix, dacă e unic)."""
        user = User.objects.filter(airtable_record_id=rec_id).first()
        if user is not None:
            return user
        if email:
            user = User.objects.filter(role='teacher', email__iexact=email).first()
            if user is not None:
                return user
        target_full = self._norm_name(f"{first} {last}")
        target_last = self._norm_name(last)
        target_first = self._norm_name(first)
        if not (target_first or target_last):
            return None
        prefix_matches = []
        for cand in User.objects.filter(role='teacher'):
            cf, cl = self._norm_name(cand.first_name), self._norm_name(cand.last_name)
            if target_full and target_full in (f"{cf} {cl}".strip(), self._norm_name(cand.get_full_name())):
                return cand
            # Nume de familie identic + prenume prefix (ex: „Cristi"/„Cristian").
            if target_last and cl == target_last and target_first and cf and \
               (cf.startswith(target_first) or target_first.startswith(cf)):
                prefix_matches.append(cand)
        # Prefixul se acceptă doar dacă identifică UN singur profesor (fără ambiguitate).
        return prefix_matches[0] if len(prefix_matches) == 1 else None

    def _resolve_teacher(self, prof_rec_id):
        """
        Rezolvă profesorul unei grupe din legătura „Profesor". Cache în
        map_teacher. Adoptă profesorul Django existent (îi setează
        airtable_record_id); dacă nu găsește și `create_missing_teachers` e
        activ, creează cont nou; altfel îl raportează ca nepotrivit și
        returnează None (grupa cade pe profesorul implicit).
        """
        if not prof_rec_id:
            return None
        if prof_rec_id in self.map_teacher:
            return self.map_teacher[prof_rec_id]
        entity = 'Profesori'
        self._load_profesori()
        f = self._profesori_by_id.get(prof_rec_id, {})
        first = str(pick(f, 'Prenume', 'First Name', default='')).strip()
        last = str(pick(f, 'Nume', 'Last Name', default='')).strip()
        email = str(pick(f, 'Email', default='')).strip()

        user = self._match_teacher(prof_rec_id, first, last, email)
        if user is not None:
            if not user.airtable_record_id:
                user.airtable_record_id = prof_rec_id
            user.sync_status = 'synced'
            user.is_archived = False
            user.airtable_synced_at = timezone.now()
            if not self.dry_run:
                user.save()
            self.stats[entity]['updated'] += 1
        elif self.create_missing_teachers:
            user = User(username=f"prof_{prof_rec_id}", role='teacher',
                        first_name=first, last_name=last, email=email,
                        airtable_record_id=prof_rec_id, sync_status='synced',
                        airtable_synced_at=timezone.now())
            user.set_unusable_password()
            if not self.dry_run:
                user.save()
            self.stats[entity]['created'] += 1
        else:
            # Nepotrivit și fără creare → raportăm (o dată) și cădem pe implicit.
            self.stats[entity]['skipped'] += 1
            self._unmatched_teachers.add(f"{first} {last}".strip() or prof_rec_id)
            self.map_teacher[prof_rec_id] = None
            return None
        self.map_teacher[prof_rec_id] = user
        return user

    def sync_grupe(self):
        entity = 'Grupe'
        from datetime import time as _time
        records = self.fetch(self._t('AIRTABLE_TABLE_GRUPE'))
        seen = set()
        for r in records:
            rec_id, f = r['id'], r.get('fields', {})
            cod = pick(f, 'Cod Grupa', 'Cod Grupă', 'Cod', default='')
            if self.grupa:
                # Pilot explicit pe o grupă: ignoră filtrul de status.
                if str(cod) != self.grupa:
                    continue
            else:
                # Rulare pe toată baza: doar grupele active (Graduated/Merged sărite).
                status_grupa = str(pick(f, 'Status Grupa', 'Status', default='')).strip()
                if self.active_statuses and status_grupa and status_grupa not in self.active_statuses:
                    self.stats[entity]['skipped'] += 1
                    continue
            # Nume curat: „Cod Grupa · Nume Modul" (ex: R0133 · Modul R + ...).
            modul_nume = pick(f, 'Nume Modul (from Module)', 'Nume Modul')
            if isinstance(modul_nume, list):
                modul_nume = modul_nume[0] if modul_nume else ''
            modul_nume = str(modul_nume or '').strip()
            cod_s = str(cod or '').strip()
            name = ' · '.join([p for p in (cod_s, modul_nume) if p]) or cod_s or rec_id
            module = self.map_module.get(first_link(f, 'Modul (link)', 'Module', 'Modul'))
            values = dict(
                name=str(name),
                airtable_cod_grupa=str(cod or ''),
            )
            if module is not None:
                values['module'] = module

            existing = Group.objects.filter(airtable_record_id=rec_id).first()
            if existing is None:
                # La CREARE trebuie completate câmpurile obligatorii ale modelului
                # (Airtable e sursa pentru orar/profesor). Profesorul din Airtable
                # („Profesor") e legat de tabelul Profesori, nu de userii Django;
                # până mapăm profesorii, folosim profesorul implicit. Orarul îl
                # derivăm din „Start date". La UPDATE nu atingem aceste câmpuri —
                # nu suprascriem orarul/profesorul stabilit în platformă.
                teacher = self._resolve_teacher(
                    first_link(f, 'Profesor', 'Trainer', 'Teacher')) or self._default_teacher()
                if teacher is None:
                    self._err(entity, rec_id,
                              "niciun profesor disponibil pentru grupa nouă "
                              "(setează AIRTABLE_SYNC_DEFAULT_TEACHER_USERNAME "
                              "sau creează un profesor)")
                    continue
                start_dt = self._parse_datetime(pick(f, 'Start date', 'Start Date', 'Data Start'))
                if start_dt is not None:
                    # Airtable stochează dateTime în UTC; ora reală a clasei e în
                    # fusul local (Europe/Bucharest). Convertim înainte de a
                    # extrage ziua/ora, altfel 17:30 local apare ca 15:30 UTC.
                    if timezone.is_aware(start_dt):
                        try:
                            from zoneinfo import ZoneInfo
                            start_dt = start_dt.astimezone(ZoneInfo('Europe/Bucharest'))
                        except Exception:
                            start_dt = timezone.localtime(start_dt)
                    weekday = start_dt.weekday()
                    start_time = start_dt.time()
                    start_date = start_dt.date()
                else:
                    weekday = 0
                    start_time = self._parse_time(pick(f, 'Start time', 'Ora', 'Ora Start')) or _time(0, 0)
                    start_date = timezone.now().date()
                values.update(teacher=teacher, weekday=weekday,
                              start_time=start_time, start_date=start_date)
            try:
                self._upsert(entity, Group, rec_id, values, self.map_group)
                seen.add(rec_id)
            except Exception as exc:  # pragma: no cover - defensiv
                self._err(entity, rec_id, exc)
        # Arhivarea grupelor se face doar la rularea completă (fără --grupa),
        # ca să nu arhivăm restul bazei în timpul unui pilot.
        if not self.grupa:
            self._archive_missing(entity, Group, seen)
        return seen

    def sync_module(self):
        entity = 'Module'
        records = self.fetch(self._t('AIRTABLE_TABLE_MODULE'))
        seen = set()
        for r in records:
            rec_id, f = r['id'], r.get('fields', {})
            name = pick(f, 'Nume', 'Name', 'Modul', default=rec_id)
            # Module.course este obligatoriu în model — dacă nu putem rezolva
            # un curs, sărim (nu creăm module orfane).
            course = None
            course_name = pick(f, 'Curs', 'Course')
            if isinstance(course_name, str) and course_name:
                course = Course.objects.filter(title=course_name).first()
            if course is None:
                self.stats[entity]['skipped'] += 1
                continue
            order = pick(f, 'Ordine', 'Order', 'Nr', default=0)
            try:
                self._upsert(entity, Module, rec_id, dict(
                    name=str(name), course=course,
                    order=int(order) if str(order).isdigit() else 0,
                ), self.map_module)
                seen.add(rec_id)
            except Exception as exc:  # pragma: no cover
                self._err(entity, rec_id, exc)
        return seen

    def sync_lectii_template(self):
        entity = 'Lectii Template'
        records = self.fetch(self._t('AIRTABLE_TABLE_LECTII_TEMPLATE'))
        seen = set()
        for r in records:
            rec_id, f = r['id'], r.get('fields', {})
            module = self.map_module.get(first_link(f, 'Module', 'Modul'))
            if module is None:
                self.stats[entity]['skipped'] += 1
                continue
            name = pick(f, 'Topic', 'Nume', 'Name', 'Lectie', default=rec_id)
            order = pick(f, 'Lesson #', 'Ordine', 'Order', 'Nr', default=0)
            try:
                self._upsert(entity, LessonTemplate, rec_id, dict(
                    module=module, name=str(name),
                    order=int(order) if str(order).isdigit() else 0,
                    objectives=str(pick(f, 'Objectives', 'Obiective', default='')),
                    materials=str(pick(f, 'Materials', 'Materiale', default='')),
                ), self.map_lesson_tpl)
                seen.add(rec_id)
            except Exception as exc:  # pragma: no cover
                self._err(entity, rec_id, exc)
        return seen

    def sync_elevi(self, allowed_ids=None):
        """
        Creează/actualizează User(role=student) + StudentProfile.
        `allowed_ids` (opțional): restrânge la elevii înscriși în grupele
        pilotului. Username derivat din record_id (unic, stabil, idempotent).
        Parola: unusable — profesorul o resetează prin fluxul existent.
        """
        entity = 'Elevi'
        records = self.fetch(self._t('AIRTABLE_TABLE_ELEVI'))
        seen = set()
        for r in records:
            rec_id, f = r['id'], r.get('fields', {})
            if allowed_ids is not None and rec_id not in allowed_ids:
                continue
            first = str(pick(f, 'Prenume Copil', 'Prenume', 'First Name', default='')).strip()
            last = str(pick(f, 'Nume Familie Copil', 'Nume de familie', 'Last Name', default='')).strip()
            full = str(pick(f, 'Nume copil', 'Name', 'Nume complet', default='')).strip()
            if not (first or last) and full:
                parts = full.split(' ', 1)
                first = parts[0]
                last = parts[1] if len(parts) > 1 else ''
            try:
                existing = User.objects.filter(airtable_record_id=rec_id).first()
                if existing:
                    existing.first_name = first or existing.first_name
                    existing.last_name = last or existing.last_name
                    existing.is_archived = False
                    existing.sync_status = 'synced'
                    existing.sync_error = ''
                    existing.airtable_synced_at = timezone.now()
                    if not self.dry_run:
                        existing.save()
                    self.stats[entity]['updated'] += 1
                    self.map_student[rec_id] = existing
                else:
                    # Username derivat direct din record_id (alfanumeric, unic,
                    # stabil). Nu folosim numele — copiii pot avea nume identice.
                    username = f"elev_{rec_id}"
                    user = User(
                        username=username, role='student',
                        first_name=first, last_name=last,
                        airtable_record_id=rec_id, must_change_password=True,
                        sync_status='synced', airtable_synced_at=timezone.now(),
                    )
                    user.set_unusable_password()
                    if not self.dry_run:
                        user.save()
                        StudentProfile.objects.get_or_create(user=user)
                    self.stats[entity]['created'] += 1
                    self.map_student[rec_id] = user
                seen.add(rec_id)
            except Exception as exc:  # pragma: no cover
                self._err(entity, rec_id, exc)
        return seen

    def sync_inscrieri(self, group_ids):
        """
        Inscrieri → Enrollment. Doar cele cu status „Inscris" și care aparțin
        grupelor sincronizate (`group_ids` = set de record-id-uri Airtable de
        grupă). Returnează setul de record-id-uri de elevi înscriși.
        """
        entity = 'Inscrieri'
        records = self.fetch(self._t('AIRTABLE_TABLE_INSCRIERI'))
        enrolled_student_recs = set()
        rows = []
        for r in records:
            rec_id, f = r['id'], r.get('fields', {})
            grp_rec = first_link(f, 'Grupa', 'Grupă', 'Group')
            if grp_rec not in group_ids:
                continue
            status = str(pick(f, 'Status', 'Stare', default='')).strip().lower()
            # Doar înscrierile ACTIVE sunt mapate (decizia A). În Airtable
            # statusul activ este „Activ" (opțiunile: Draft/Activ/Inactiv/Finalizat).
            if status not in ('activ', 'inscris', 'înscris'):
                self.stats[entity]['skipped'] += 1
                continue
            stud_rec = first_link(f, 'Elev', 'Elevi', 'Student')
            if stud_rec:
                enrolled_student_recs.add(stud_rec)
            rows.append((rec_id, f, grp_rec, stud_rec))
        # Elevii se sincronizează abia acum (doar cei înscriși în pilot).
        self.sync_elevi(allowed_ids=enrolled_student_recs)
        seen = set()
        for rec_id, f, grp_rec, stud_rec in rows:
            group = self.map_group.get(grp_rec)
            student = self.map_student.get(stud_rec)
            if group is None or student is None:
                self.stats[entity]['skipped'] += 1
                continue
            values = dict(group=group, student=student, is_active=True,
                          status='activ')
            end = pick(f, 'Data Sfarsit', 'End Date', 'Data Sfârșit')
            if end:
                values['end_date'] = end
            try:
                # Upsert după record_id; dacă lipsește (înscriere veche fără
                # mapare), cădem pe cheia naturală (group, student).
                obj = Enrollment.objects.filter(airtable_record_id=rec_id).first()
                # Fallback pe cheia naturală (group, student) doar dacă ambele
                # sunt deja salvate — în dry-run instanțele nu au pk și nu pot
                # fi folosite în filtre.
                if obj is None and group.pk and student.pk:
                    obj = Enrollment.objects.filter(group=group, student=student).first()
                    if obj is not None and not obj.airtable_record_id:
                        obj.airtable_record_id = rec_id
                if obj is None:
                    obj = Enrollment(airtable_record_id=rec_id)
                    action = 'created'
                else:
                    action = 'updated'
                for k, v in values.items():
                    setattr(obj, k, v)
                obj.is_archived = False
                obj.sync_status = 'synced'
                obj.airtable_synced_at = timezone.now()
                if not self.dry_run:
                    obj.save()
                self.stats[entity][action] += 1
                seen.add(rec_id)
            except Exception as exc:  # pragma: no cover
                self._err(entity, rec_id, exc)
        return seen

    def sync_lectii(self, group_ids):
        """
        Lectii → Lesson. DOAR UPDATE (niciodată CREATE). Dacă lecția nu e găsită
        după airtable_record_id, logăm eroare și continuăm.
        """
        entity = 'Lectii'
        records = self.fetch(self._t('AIRTABLE_TABLE_LECTII'))
        seen = set()
        for r in records:
            rec_id, f = r['id'], r.get('fields', {})
            grp_rec = first_link(f, 'Nume Grupa', 'Grupa', 'Grupă', 'Group')
            if grp_rec not in group_ids:
                continue
            lesson = Lesson.objects.filter(airtable_record_id=rec_id).first()
            if lesson is None:
                # NU creăm lecții — sunt generate de automatizarea Airtable.
                # Lecțiile Django nu sunt încă legate prin airtable_record_id,
                # deci e normal să nu le găsim: le numărăm ca „sărite", nu erori.
                self.stats[entity]['skipped'] += 1
                continue
            topic = pick(f, 'Lectie', 'Cod Lectie', 'Topic', 'Subiect')
            date_dt = self._parse_datetime(pick(f, 'Schedule', 'Data', 'Date'))
            takeaways = pick(f, 'Lesson Takeaways')
            homework = pick(f, 'Homework')
            try:
                if topic is not None:
                    lesson.topic = str(topic)
                if date_dt is not None:
                    lesson.date = date_dt.date()
                if takeaways is not None:
                    lesson.lesson_takeaways = str(takeaways)
                if homework is not None:
                    lesson.homework = str(homework)
                lesson.is_archived = False
                lesson.sync_status = 'synced'
                lesson.sync_error = ''
                lesson.airtable_synced_at = timezone.now()
                if not self.dry_run:
                    lesson.save()
                self.stats[entity]['updated'] += 1
                seen.add(rec_id)
            except Exception as exc:  # pragma: no cover
                self._err(entity, rec_id, exc)
        return seen

    # -- orchestrare ---------------------------------------------------------
    def run(self):
        self.log(f"== Pull Airtable → Django "
                 f"{'(DRY-RUN)' if self.dry_run else ''} "
                 f"{'grupa=' + self.grupa if self.grupa else '(toată baza)'} ==")

        # Profesorii se rezolvă lazy, doar pentru grupele efectiv sincronizate
        # (vezi _resolve_teacher apelat din sync_grupe) — un pilot pe o grupă
        # nu atinge toți profesorii din bază.

        # Curriculumul (Module/Lectii Template) NU se sincronizează în pilot:
        # tabelul „Module" din Airtable nu are legătură către un Curs, iar
        # `Module.course` e obligatoriu în Django. Curriculumul rămâne gestionat
        # din admin; `Group.module` e nullabil, deci grupele se creează fără el.
        # (De reactivat după ce definim maparea Categorie Curs → Course.)
        group_ids = self.sync_grupe()
        self.sync_inscrieri(group_ids)
        self.sync_lectii(group_ids)

        return self._finish()

    def _finish(self):
        totals = dict(created=0, updated=0, archived=0, skipped=0, errors=0)
        for s in self.stats.values():
            for k in totals:
                totals[k] += s[k]

        status = 'dry_run' if self.dry_run else (
            'partial' if totals['errors'] else 'success')
        details_lines = [f"{e}: {dict(v)}" for e, v in self.stats.items()]
        if self._unmatched_teachers:
            self.log("\nProfesori nepotriviți (grupele lor au primit profesorul "
                     "implicit; rulează cu --create-missing-teachers ca să le "
                     "creezi conturi): " + ", ".join(sorted(self._unmatched_teachers)))
            details_lines.append("PROFESORI NEPOTRIVIȚI: " +
                                 ", ".join(sorted(self._unmatched_teachers)))
        if self.errors:
            details_lines.append("ERORI:")
            details_lines.extend(self.errors[:50])
        details = "\n".join(details_lines)

        synclog = None
        if not self.dry_run:
            synclog = SyncLog.objects.create(
                direction='pull', status=status,
                scope=self.grupa or 'all', dry_run=False,
                records_created=totals['created'], records_updated=totals['updated'],
                records_archived=totals['archived'], records_skipped=totals['skipped'],
                errors_count=totals['errors'], details=details,
                finished_at=timezone.now(),
            )
        self.log("\n" + details)
        return dict(totals=totals, stats={e: dict(v) for e, v in self.stats.items()},
                    errors=self.errors, status=status, synclog=synclog)


def show_schema(fetch=None, log=print):
    """
    Mod de descoperire: ia câteva înregistrări din fiecare tabel și tipărește
    numele câmpurilor reale, ca să confirmăm maparea ÎNAINTE de orice scriere.
    """
    fetch = fetch or _live_fetch
    tables = [
        ('Grupe', 'AIRTABLE_TABLE_GRUPE'),
        ('Module', 'AIRTABLE_TABLE_MODULE'),
        ('Lectii Template', 'AIRTABLE_TABLE_LECTII_TEMPLATE'),
        ('Inscrieri', 'AIRTABLE_TABLE_INSCRIERI'),
        ('Elevi', 'AIRTABLE_TABLE_ELEVI'),
        ('Lectii', 'AIRTABLE_TABLE_LECTII'),
    ]
    for label, key in tables:
        table_id = getattr(settings, key)
        try:
            records = fetch(table_id)
        except Exception as exc:
            log(f"\n### {label} ({table_id}): EROARE — {exc}")
            continue
        keys = set()
        for r in records[:5]:
            keys.update(r.get('fields', {}).keys())
        log(f"\n### {label} ({table_id}) — {len(records)} înregistrări")
        for k in sorted(keys):
            log(f"    - {k}")
