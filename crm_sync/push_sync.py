"""
Push Django → Airtable (Epic 7, Faza 4).

Mind.academy = sursa de adevăr pentru EXECUȚIE. Împingem în Airtable:
  - Prezențele (tabelul „Prezente") — create sau update după airtable_record_id;
  - Lecția finalizată (tabelul „Lectii") — DOAR update (după airtable_record_id).

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


def build_lectie_fields(lesson):
    """Câmpuri editabile pentru update în tabelul „Lectii"."""
    fields = {'Completed': lesson.status == 'completed'}
    if lesson.lesson_takeaways:
        fields['Lesson Takeaways'] = lesson.lesson_takeaways
    if lesson.homework:
        fields['Homework'] = lesson.homework
    return fields


class PushSync:
    def __init__(self, dry_run=False, grupa=None, log=None,
                 create_fn=None, update_fn=None):
        self.dry_run = dry_run
        self.grupa = (grupa or '').strip()
        self.log = log or (lambda m: None)
        # Injectabile pentru teste; implicit clientul REST de scriere.
        if create_fn is None or update_fn is None:
            from crm_sync.airtable_push import create_record, update_record
            create_fn = create_fn or create_record
            update_fn = update_fn or update_record
        self._create = create_fn
        self._update = update_fn
        self.stats = defaultdict(lambda: dict(created=0, updated=0, skipped=0, errors=0))
        self.errors = []

    def _t(self, key):
        return getattr(settings, key)

    def _err(self, entity, ref, message):
        self.stats[entity]['errors'] += 1
        self.errors.append(f"[{entity}] {ref}: {message}")
        self.log(f"  ! EROARE {entity} {ref}: {message}")

    def _target_groups(self):
        qs = Group.objects.exclude(airtable_record_id__isnull=True).exclude(airtable_record_id='')
        if self.grupa:
            qs = qs.filter(airtable_cod_grupa=self.grupa)
        return qs

    def _build_specs(self):
        """Construiește lista de scrieri (fără a atinge Airtable/DB)."""
        specs = []
        groups = list(self._target_groups())
        group_ids = [g.id for g in groups]

        # --- Prezențe (create/update) ---
        atts = (Attendance.objects
                .filter(lesson__group_id__in=group_ids)
                .select_related('student', 'lesson', 'lesson__group', 'enrollment'))
        for att in atts:
            if not (att.student and att.student.airtable_record_id
                    and att.lesson and att.lesson.airtable_record_id):
                # Fără elev/lecție mapați în Airtable nu putem lega prezența.
                self.stats['Prezente']['skipped'] += 1
                continue
            specs.append(dict(
                entity='Prezente',
                table=self._t('AIRTABLE_TABLE_PREZENTE'),
                record_id=att.airtable_record_id or '',
                payload=build_prezenta_fields(att),
                source_kind='prezenta', source_id=att.id,
                dedupe_key=f"prezenta:{att.id}",
            ))

        # --- Lecție finalizată (doar update; doar lecțiile finalizate) ---
        lessons = (Lesson.objects
                   .filter(group_id__in=group_ids, status='completed')
                   .exclude(airtable_record_id__isnull=True).exclude(airtable_record_id=''))
        for lesson in lessons:
            specs.append(dict(
                entity='Lectii',
                table=self._t('AIRTABLE_TABLE_LECTII'),
                record_id=lesson.airtable_record_id,
                payload=build_lectie_fields(lesson),
                source_kind='lectie', source_id=lesson.id,
                dedupe_key=f"lectie:{lesson.id}",
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
            entity = 'Lectii' if job.source_kind == 'lectie' else 'Prezente'
            self.stats[entity]['created' if op == 'create' else 'updated'] += 1
        except Exception as exc:  # pragma: no cover - depinde de rețea
            job.status = 'error'
            job.attempts = job.attempts + 1
            job.last_error = str(exc)[:2000]
            job.save()
            self._err('Lectii' if job.source_kind == 'lectie' else 'Prezente',
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
            return self._finish(specs)

        for s in specs:
            job = self._upsert_job(s)
            self._process_job(job)
        return self._finish(specs)

    def _finish(self, specs):
        totals = dict(created=0, updated=0, skipped=0, errors=0)
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
                records_skipped=totals['skipped'], errors_count=totals['errors'],
                details=details, finished_at=timezone.now())
        self.log("\n" + details)
        return dict(totals=totals, stats={e: dict(v) for e, v in self.stats.items()},
                    errors=self.errors, status=status, synclog=synclog, specs=specs)
