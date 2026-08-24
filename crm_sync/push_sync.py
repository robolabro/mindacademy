"""
Push Django → Airtable (Epic 7, Faza 4).

Mind.academy = sursa de adevăr pentru EXECUȚIE. Împingem în Airtable:
  - Prezențele (tabelul „Prezente") — create/update după (Elev, Lecție), cu
    reconciliere ca să nu creăm duplicate;
  - „Ce s-a lucrat" (câmpul „Lesson Takeaways" din „Lectii") — DOAR update, doar
    acest câmp. Restul lecției (orar, „Completed") rămâne al Airtable.

Reguli dure:
  - NU scriem NICIODATĂ în „Progres Lectii" (generat de automatizarea Airtable
    din Prezențe cu Attended=true).
  - Scriem doar câmpuri editabile — niciodată formula/lookup/rollup/count.
  - Idempotent prin coada `AirtablePushJob` (dedupe pe sursă) + scrierea
    record-id-ului Airtable înapoi pe obiectul Django după CREATE.
  - `--dry-run` nu scrie nimic (nici în Airtable, nici în coadă).
  - `--grupa=COD` restrânge la o singură grupă (pilotul obligatoriu).
"""
from collections import defaultdict

from django.conf import settings
from django.utils import timezone

from teacher_platform.models import Group, Lesson, Attendance
from crm_sync.models import AirtablePushJob, SyncLog


def build_prezenta_fields(att):
    """Câmpuri editabile pentru tabelul „Prezente" (doar cele scriabile)."""
    student = att.student
    lesson = att.lesson
    group = lesson.group if lesson else None
    fields = {
        'Attended': bool(att.is_present),
        'Absenta': not att.is_present,
        'Absenta Anuntata': bool(att.absenta_anuntata),
        'Genereaza Recuperare': bool(att.genereaza_recuperare),
    }
    if student and student.airtable_record_id:
        fields['Elev'] = [student.airtable_record_id]
    if lesson and lesson.airtable_record_id:
        fields['Lectie'] = [lesson.airtable_record_id]
    if group and group.airtable_record_id:
        fields['Grupa'] = [group.airtable_record_id]
    if att.enrollment and att.enrollment.airtable_record_id:
        fields['Inscriere'] = [att.enrollment.airtable_record_id]
    if att.notes:
        fields['Notes'] = att.notes
    return fields


def lesson_schedule_iso(lesson):
    """Orarul Django (dată+oră locală Europe/Bucharest) → „Schedule" în UTC ISO."""
    from datetime import datetime
    if not (lesson.date and lesson.start_time):
        return None
    try:
        from zoneinfo import ZoneInfo
        local = datetime.combine(lesson.date, lesson.start_time,
                                 tzinfo=ZoneInfo('Europe/Bucharest'))
        return local.astimezone(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    except Exception:
        return f"{lesson.date}T{lesson.start_time}"


def build_content_fields(lesson):
    """Conținutul editat de profesor la lecție: „ce s-a lucrat" + tema pentru
    acasă. NU trimitem „Completed"/orar — acelea rămân ale Airtable.

    Excepție: pentru lecțiile de RECUPERARE, orarul e proprietatea platformei
    (profesorul stabilește data reală a recuperării), deci trimitem și
    „Schedule"."""
    fields = {
        'Lesson Takeaways': lesson.lesson_takeaways,
        'Homework': lesson.homework,
    }
    if getattr(lesson, 'is_recuperare', False):
        sched = lesson_schedule_iso(lesson)
        if sched is not None:
            fields['Schedule'] = sched
    return fields


def build_new_lesson_fields(lesson):
    """
    Câmpuri pentru o lecție CREATĂ în Mind.academy (§4/A) → nouă în „Lectii".
    Orarul din Django (dată+oră locală) → „Schedule" în UTC ISO. Flag-urile care
    suprimă auto-prezențele automatizării vin din AIRTABLE_NEW_LESSON_FIELDS.
    """
    fields = {}
    group = lesson.group
    if group and group.airtable_record_id:
        fields['Nume Grupa'] = [group.airtable_record_id]
    sched = lesson_schedule_iso(lesson)
    if sched is not None:
        fields['Schedule'] = sched
    tpl = lesson.lesson_template
    if tpl is not None and getattr(tpl, 'airtable_record_id', ''):
        fields['Lectie Template'] = [tpl.airtable_record_id]
    if lesson.homework:
        fields['Homework'] = lesson.homework
    if lesson.lesson_takeaways:
        fields['Lesson Takeaways'] = lesson.lesson_takeaways
    extra = getattr(settings, 'AIRTABLE_NEW_LESSON_FIELDS', {}) or {}
    fields.update(extra)
    return fields


class PushSync:
    def __init__(self, dry_run=False, grupa=None, log=None,
                 create_fn=None, update_fn=None, delete_fn=None, fetch_fn=None,
                 cleanup_duplicates=False, only_pending=False, push_new_lessons=False):
        self.dry_run = dry_run
        # Filtru pe „Cod Grupa": una sau mai multe (separate prin virgulă).
        self.grupa = (grupa or '').strip()
        self.grupa_codes = {c.strip() for c in self.grupa.split(',') if c.strip()}
        self.log = log or (lambda m: None)
        self.cleanup_duplicates = cleanup_duplicates
        self.only_pending = only_pending
        self.push_new_lessons = push_new_lessons
        # Injectabile pentru teste; implicit clientul REST de scriere/citire.
        if create_fn is None or update_fn is None or delete_fn is None:
            from crm_sync.airtable_push import create_record, update_record, delete_record
            create_fn = create_fn or create_record
            update_fn = update_fn or update_record
            delete_fn = delete_fn or delete_record
        if fetch_fn is None:
            from crm_sync.airtable_client import fetch_all
            fetch_fn = fetch_all
        self._create = create_fn
        self._update = update_fn
        self._delete = delete_fn
        self._fetch = fetch_fn
        self.stats = defaultdict(lambda: dict(created=0, updated=0, skipped=0,
                                              deleted=0, errors=0))
        self.errors = []
        self._orphans = []  # (att_id, orphan_record_id) de șters (cleanup)
        self._dupes = []    # id-uri de prezențe duplicate detectate (avertisment)

    def _t(self, key):
        return getattr(settings, key)

    def _err(self, entity, ref, message):
        self.stats[entity]['errors'] += 1
        self.errors.append(f"[{entity}] {ref}: {message}")
        self.log(f"  ! EROARE {entity} {ref}: {message}")

    def _target_groups(self):
        qs = Group.objects.exclude(airtable_record_id__isnull=True).exclude(airtable_record_id='')
        if self.grupa_codes:
            qs = qs.filter(airtable_cod_grupa__in=list(self.grupa_codes))
        return qs

    def _load_existing_prezente(self, lesson_recids):
        """
        Reconciliere: citește Prezențele existente din Airtable pentru lecțiile
        vizate și le indexează după (Elev, Lecție), ca să NU creăm duplicate —
        actualizăm prezența existentă. Câmpurile linkate vin din REST ca liste
        de record-id-uri. Returnează {(elev_id, lectie_id): [prezenta_id, ...]}.
        """
        index = defaultdict(list)
        if not lesson_recids:
            return index
        try:
            records = self._fetch(self._t('AIRTABLE_TABLE_PREZENTE'))
        except Exception as exc:  # pragma: no cover
            self._err('Prezente', 'reconciliere', exc)
            return index
        for r in records:
            f = r.get('fields', {})
            elevs = [x for x in (f.get('Elev') or []) if isinstance(x, str)]
            lectii = [x for x in (f.get('Lectie') or []) if isinstance(x, str)]
            if not elevs or not lectii:
                continue
            lectie = lectii[0]
            if lectie not in lesson_recids:
                continue
            index[(elevs[0], lectie)].append(r['id'])
        return index

    def _build_specs(self):
        """Construiește lista de scrieri (fără a atinge Airtable/DB)."""
        specs = []
        groups = list(self._target_groups())
        group_ids = [g.id for g in groups]

        atts = (Attendance.objects
                .filter(lesson__group_id__in=group_ids)
                .select_related('student', 'lesson', 'lesson__group', 'enrollment'))
        if self.only_pending:
            atts = atts.filter(sync_status='pending')
        atts = list(atts)
        # Reconciliere prezențe existente (după lecțiile implicate).
        lesson_recids = {a.lesson.airtable_record_id for a in atts
                         if a.lesson and a.lesson.airtable_record_id}
        prez_index = self._load_existing_prezente(lesson_recids)

        # --- Prezențe (create/update, cu evitarea duplicatelor) ---
        for att in atts:
            if not (att.student and att.student.airtable_record_id
                    and att.lesson and att.lesson.airtable_record_id):
                # Fără elev/lecție mapați în Airtable nu putem lega prezența.
                self.stats['Prezente']['skipped'] += 1
                continue
            key = (att.student.airtable_record_id, att.lesson.airtable_record_id)
            existing = prez_index.get(key, [])
            ptr = att.airtable_record_id
            orphan = None   # prezența „a noastră" de șters (doar cu cleanup)
            dupe = None     # prezența duplicată detectată (pentru avertisment)
            if ptr and ptr in existing:
                # att pointează deja spre o prezență reală. Dacă mai există și
                # altele (duplicate), o păstrăm pe a lui att și avertizăm; doar
                # cu --cleanup-duplicates convergem spre cealaltă și o ștergem
                # pe a noastră.
                centers = [r for r in existing if r != ptr]
                if centers and self.cleanup_duplicates:
                    record_id = centers[0]
                    orphan = ptr
                else:
                    record_id = ptr
                    dupe = centers[0] if centers else None
            elif existing:
                # att nu pointează spre nimic valid → adoptăm prezența existentă
                # (evităm crearea unui duplicat). Cazul normal: prezență marcată
                # în Django pentru o lecție care are deja o Prezenta în Airtable.
                record_id = existing[0]
            else:
                record_id = ptr or ''   # nimic în Airtable → create
            specs.append(dict(
                entity='Prezente',
                table=self._t('AIRTABLE_TABLE_PREZENTE'),
                record_id=record_id,
                payload=build_prezenta_fields(att),
                source_kind='prezenta', source_id=att.id,
                dedupe_key=f"prezenta:{att.id}",
                orphan=orphan, dupe=dupe,
            ))

        # --- Conținut lecție („ce s-a lucrat" + temă) → update în „Lectii" ---
        # Doar lecțiile deja mapate în Airtable (au airtable_record_id). Orarul/
        # „Completed" rămân ale Airtable; noi scriem doar Lesson Takeaways + Homework.
        from django.db.models import Q
        lessons = (Lesson.objects
                   .filter(group_id__in=group_ids)
                   .exclude(airtable_record_id__isnull=True).exclude(airtable_record_id=''))
        if self.only_pending:
            lessons = lessons.filter(sync_status='pending')
        else:
            # Trimitem lecțiile cu conținut SAU recuperările (au și orarul de
            # trimis, chiar dacă n-au încă „ce s-a lucrat"/temă).
            lessons = lessons.exclude(
                Q(lesson_takeaways='') & Q(homework='') & Q(is_recuperare=False))
        for lesson in lessons:
            specs.append(dict(
                entity='Lectii',
                table=self._t('AIRTABLE_TABLE_LECTII'),
                record_id=lesson.airtable_record_id,
                payload=build_content_fields(lesson),
                source_kind='lectie', source_id=lesson.id,
                dedupe_key=f"lectie:{lesson.id}",
            ))

        # --- Lecții CREATE în Mind.academy (§4/A) → nouă în „Lectii" (opt-in) ---
        # Doar lecțiile fără airtable_record_id (originare din platformă). După
        # create primesc id și nu se mai recreează. Flag-urile de suprimare a
        # auto-prezențelor vin din AIRTABLE_NEW_LESSON_FIELDS.
        if self.push_new_lessons:
            from django.db.models import Q
            new_lessons = (Lesson.objects
                           .filter(group_id__in=group_ids)
                           .filter(Q(airtable_record_id__isnull=True) | Q(airtable_record_id='')))
            for lesson in new_lessons:
                if not (lesson.group and lesson.group.airtable_record_id):
                    self.stats['Lectii']['skipped'] += 1
                    continue
                specs.append(dict(
                    entity='Lectii',
                    table=self._t('AIRTABLE_TABLE_LECTII'),
                    record_id='',   # create
                    payload=build_new_lesson_fields(lesson),
                    source_kind='lectie_nou', source_id=lesson.id,
                    dedupe_key=f"lectie_nou:{lesson.id}",
                ))
        return specs

    def _writeback_source(self, spec, new_record_id):
        """După un CREATE, scrie record-id-ul Airtable înapoi pe obiectul Django."""
        if spec['source_kind'] == 'prezenta':
            Attendance.objects.filter(pk=spec['source_id']).update(
                airtable_record_id=new_record_id, sync_status='synced',
                airtable_synced_at=timezone.now())

    def _upsert_job(self, spec):
        """Un singur job per sursă (reutilizat între rulări); îi reîmprospătăm
        payload-ul. Istoricul rămâne în attempts/processed_at."""
        job = AirtablePushJob.objects.filter(dedupe_key=spec['dedupe_key']).first()
        if job is None:
            job = AirtablePushJob(dedupe_key=spec['dedupe_key'])
        job.target_table = spec['table']
        job.target_record_id = spec['record_id']
        job.payload = spec['payload']
        job.source_kind = spec['source_kind']
        job.source_id = spec['source_id']
        job.status = 'pending'
        job.last_error = ''
        job.save()
        return job

    def _process_job(self, job):
        op = 'update' if job.target_record_id else 'create'
        try:
            if op == 'create':
                rec = self._create(job.target_table, job.payload)
                new_id = rec['id']
                job.target_record_id = new_id
                self._writeback_source(
                    dict(source_kind=job.source_kind, source_id=job.source_id), new_id)
            else:
                self._update(job.target_table, job.target_record_id, job.payload)
            job.status = 'done'
            job.processed_at = timezone.now()
            job.attempts = job.attempts + 1
            job.last_error = ''
            job.save()
            entity = 'Prezente' if job.source_kind == 'prezenta' else 'Lectii'
            self.stats[entity]['created' if op == 'create' else 'updated'] += 1
        except Exception as exc:  # pragma: no cover - depinde de rețea
            job.status = 'error'
            job.attempts = job.attempts + 1
            job.last_error = str(exc)[:2000]
            job.save()
            self._err('Prezente' if job.source_kind == 'prezenta' else 'Lectii',
                      job.dedupe_key, exc)

    def run(self):
        self.log(f"== Push Django → Airtable "
                 f"{'(DRY-RUN)' if self.dry_run else ''} "
                 f"{'grupa=' + self.grupa if self.grupa else '(toate grupele)'} ==")
        specs = self._build_specs()

        if self.dry_run:
            for s in specs:
                entity = s['entity']
                self.stats[entity]['created' if not s['record_id'] else 'updated'] += 1
                if s.get('orphan'):
                    self._orphans.append((s['source_id'], s['orphan']))
                if s.get('dupe'):
                    self._dupes.append(s['dupe'])
            self._report_dupes()
            return self._finish(specs)

        for s in specs:
            job = self._upsert_job(s)
            self._process_job(job)
            if job.status != 'done':
                continue
            if s['source_kind'] == 'prezenta':
                # Pointer corect pe att (record_id final: existent/creat) + synced.
                Attendance.objects.filter(pk=s['source_id']).update(
                    airtable_record_id=job.target_record_id, sync_status='synced',
                    airtable_synced_at=timezone.now())
                if s.get('orphan') and s['orphan'] != job.target_record_id:
                    self._orphans.append((s['source_id'], s['orphan']))
                if s.get('dupe'):
                    self._dupes.append(s['dupe'])
            elif s['source_kind'] == 'lectie':
                Lesson.objects.filter(pk=s['source_id']).update(
                    sync_status='synced', airtable_synced_at=timezone.now())
            elif s['source_kind'] == 'lectie_nou':
                # Lecție nou-creată în Airtable → salvăm record-id-ul pe lecția
                # Django (devine „mapată"; nu se mai recreează).
                Lesson.objects.filter(pk=s['source_id']).update(
                    airtable_record_id=job.target_record_id, sync_status='synced',
                    airtable_synced_at=timezone.now())

        # Curățarea duplicatelor pe care le-am creat noi (ireversibil → opt-in).
        if self.cleanup_duplicates:
            for att_id, orphan in self._orphans:
                try:
                    self._delete(self._t('AIRTABLE_TABLE_PREZENTE'), orphan)
                    self.stats['Prezente']['deleted'] += 1
                except Exception as exc:  # pragma: no cover
                    self._err('Prezente', f'delete {orphan}', exc)
        self._report_dupes()
        return self._finish(specs)

    def _report_dupes(self):
        if self._dupes:
            self.log(f"  ATENȚIE: {len(self._dupes)} prezențe au duplicate în Airtable "
                     f"(am păstrat-o pe cea din Django). Rulează cu "
                     f"--cleanup-duplicates ca să convergem și să ștergem duplicatul.")

    def _finish(self, specs):
        totals = dict(created=0, updated=0, skipped=0, deleted=0, errors=0)
        for v in self.stats.values():
            for k in totals:
                totals[k] += v[k]
        status = 'dry_run' if self.dry_run else ('partial' if totals['errors'] else 'success')
        details = "\n".join(f"{e}: {dict(v)}" for e, v in self.stats.items())
        if self.errors:
            details += "\nERORI:\n" + "\n".join(self.errors[:50])

        synclog = None
        if not self.dry_run:
            synclog = SyncLog.objects.create(
                direction='push', status=status, scope=self.grupa or 'all', dry_run=False,
                records_created=totals['created'], records_updated=totals['updated'],
                records_archived=totals['deleted'], records_skipped=totals['skipped'],
                errors_count=totals['errors'], details=details, finished_at=timezone.now())
        self.log("\n" + details)
        return dict(totals=totals, stats={e: dict(v) for e, v in self.stats.items()},
                    errors=self.errors, status=status, synclog=synclog, specs=specs,
                    dupes=list(self._dupes), orphans=list(self._orphans))
