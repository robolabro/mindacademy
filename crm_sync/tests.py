"""
Teste pentru contractul cu Airtable — cine deține ce câmp.

Regula: Airtable e sursa de adevăr pentru STRUCTURĂ (orar, grupe, înscrieri),
Mind.academy pentru EXECUȚIE (prezențe, „ce s-a lucrat", finalizare). Testele
de aici păzesc granița, ca o modificare din platformă să nu fie anulată de
sincronizarea de noapte (și invers).

Rulare:
    python manage.py test crm_sync
"""
import datetime

from django.conf import settings
from django.test import TestCase

from accounts.models import User
from courses.models import AgeGroup, Course
from crm_sync.push_sync import build_content_fields
from teacher_platform.models import Group, Lesson

COMPLETED_FIELD = getattr(settings, 'AIRTABLE_LESSON_COMPLETED_FIELD', 'Completed')
TEACHER_FIELD = getattr(settings, 'AIRTABLE_LESSON_TEACHER_PRESENT_FIELD', 'Prezente profesor')


class BuildContentFieldsTests(TestCase):
    """Ce trimite push-ul pentru o lecție."""

    def setUp(self):
        teacher = User.objects.create_user(
            username='prof_push', password='Test1234!', role='teacher')
        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-p', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        self.group = Group.objects.create(
            name='Y0129 · Modul Y', teacher=teacher, course=course, weekday=3,
            start_time=datetime.time(17, 30), start_date=datetime.date(2026, 1, 12))

    def _lesson(self, **kw):
        return Lesson.objects.create(
            group=self.group, date=datetime.date(2026, 9, 10),
            start_time=datetime.time(17, 30), **kw)

    def test_lectie_finalizata_bifeaza_in_airtable(self):
        fields = build_content_fields(self._lesson(status='completed'))
        self.assertIs(fields[COMPLETED_FIELD], True)
        self.assertIs(fields[TEACHER_FIELD], True)

    def test_definalizarea_debifeaza_in_airtable(self):
        """Regresie: push-ul era one-way, deci debifarea nu ajungea niciodată
        în Airtable, iar pull-ul de noapte repunea lecția pe „Finalizată"."""
        fields = build_content_fields(self._lesson(status='scheduled'))
        self.assertIs(fields[COMPLETED_FIELD], False)
        self.assertIs(fields[TEACHER_FIELD], False)

    def test_takeaways_si_tema_se_trimit_mereu(self):
        fields = build_content_fields(
            self._lesson(status='scheduled', lesson_takeaways='## Ce am lucrat',
                         homework='2 fișe'))
        self.assertEqual(fields['Lesson Takeaways'], '## Ce am lucrat')
        self.assertEqual(fields['Homework'], '2 fișe')

    def test_orarul_se_trimite_doar_pentru_recuperari(self):
        """Platforma deține data DOAR la recuperări; restul e al Airtable."""
        self.assertNotIn('Schedule', build_content_fields(self._lesson()))
        self.assertIn('Schedule', build_content_fields(self._lesson(is_recuperare=True)))


class LessonDisplayTests(TestCase):
    """Cum se prezintă lecțiile în calendar."""

    def setUp(self):
        teacher = User.objects.create_user(
            username='prof_disp', password='Test1234!', role='teacher')
        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-d', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        self.group = Group.objects.create(
            name='A0131 · Modul A', teacher=teacher, course=course, weekday=1,
            start_time=datetime.time(18, 0), start_date=datetime.date(2026, 1, 12))

    def _lesson(self, **kw):
        # în viitor, ca să nu fie „de completat" (etichetă pentru restanțe)
        from django.utils import timezone
        return Lesson.objects.create(
            group=self.group, date=timezone.localdate() + datetime.timedelta(days=5),
            start_time=datetime.time(18, 0), **kw)

    def test_recuperarile_au_eticheta_lor(self):
        self.assertEqual(self._lesson(is_recuperare=True).status_label, 'Recuperare')
        self.assertEqual(
            self._lesson(is_recuperare=True, status='completed').status_label,
            'Recuperată')

    def test_lectiile_obisnuite_pastreaza_statusul(self):
        self.assertEqual(self._lesson(status='scheduled').status_label, 'Programată')
        self.assertEqual(self._lesson(status='completed').status_label, 'Finalizată')

    def test_anulata_nu_mai_e_o_optiune(self):
        """Lecțiile nu se anulează — Airtable le reprogramează."""
        self.assertNotIn('cancelled', dict(Lesson.STATUS_CHOICES))

    def test_codul_scurt_pentru_calendar(self):
        self.assertEqual(self.group.short_name, 'A0131')


class FantomeTests(TestCase):
    """Lecțiile șterse în Airtable: nu se recreează, se arhivează, nu se văd.

    Ciclul care producea fantomele: o lecție din platformă indica spre un record
    șters în Airtable → push-ul primea 404 → CREA un record nou, doar cu dată și
    takeaways (fără grupă) → profesorul îl ștergea → noaptea următoare, iar.
    """

    def setUp(self):
        from teacher_platform.models import Attendance, Enrollment
        self.teacher = User.objects.create_user(
            username='prof_f', password='Test1234!', role='teacher')
        self.student = User.objects.create_user(
            username='elev_f', password='Test1234!', role='student',
            airtable_record_id='recELEV')
        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-f', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        self.group = Group.objects.create(
            name='S0130 · Modul S', teacher=self.teacher, course=course, weekday=3,
            start_time=datetime.time(17, 30), start_date=datetime.date(2026, 1, 12),
            airtable_record_id='recGRUPA')
        Enrollment.objects.create(group=self.group, student=self.student, is_active=True)
        # fantoma-mamă: recuperare al cărei record a fost șters în Airtable
        self.lesson = Lesson.objects.create(
            group=self.group, date=datetime.date(2026, 9, 17),
            start_time=datetime.time(17, 30), is_recuperare=True,
            airtable_record_id='recMORT', status='scheduled')
        self.att = Attendance.objects.create(
            lesson=self.lesson, student=self.student, is_present=False,
            airtable_record_id='recPREZMORT')

    def _push(self, **kw):
        from crm_sync.push_sync import PushSync
        self.created, self.updated = [], []

        def update(table, rec_id, fields):
            self.updated.append(rec_id)
            raise Exception('404 NOT_FOUND')          # orice record: șters

        def create(table, fields):
            self.created.append((table, fields))
            return {'id': 'recNOU%d' % len(self.created)}

        push = PushSync(create_fn=create, update_fn=update, delete_fn=lambda *a: None,
                        fetch_fn=lambda *a, **k: [], content_all=True, **kw)
        return push, push.run()

    def _lectii_create(self):
        return [f for t, f in self.created if t == settings.AIRTABLE_TABLE_LECTII]

    def test_lectia_stearsa_nu_se_mai_recreeaza(self):
        self._push()
        self.assertEqual(self._lectii_create(), [],
                         'push-ul a creat o lecție fantomă în Airtable')

    def test_lectia_stearsa_se_arhiveaza(self):
        self._push()
        self.lesson.refresh_from_db()
        self.assertTrue(self.lesson.is_archived)

    def test_a_doua_noapte_nici_macar_nu_mai_incearca(self):
        self._push()
        self.updated.clear()
        self._push()
        self.assertNotIn('recMORT', self.updated)

    def test_nici_prezenta_lectiei_sterse_nu_mai_e_trimisa(self):
        """Prezența ar indica spre o lecție inexistentă."""
        self.lesson.is_archived = True
        self.lesson.save()
        self._push()
        self.assertEqual([t for t, f in self.created], [])

    def test_prezenta_stearsa_a_unei_lectii_vii_se_recreeaza_in_continuare(self):
        """Fallback-ul de recreare rămâne valabil pentru prezențe."""
        from crm_sync import push_sync
        # lecția există în Airtable; doar prezența a dispărut
        orig = push_sync.PushSync._load_existing_prezente
        push_sync.PushSync._load_existing_prezente = lambda self, ids: {}
        try:
            from crm_sync.push_sync import PushSync

            def update(table, rec_id, fields):
                if table == settings.AIRTABLE_TABLE_PREZENTE:
                    raise Exception('404 NOT_FOUND')
                return {'id': rec_id}

            created = []
            PushSync(create_fn=lambda t, f: created.append(t) or {'id': 'recP2'},
                     update_fn=update, delete_fn=lambda *a: None,
                     fetch_fn=lambda *a, **k: [], content_all=True).run()
        finally:
            push_sync.PushSync._load_existing_prezente = orig
        self.assertEqual(created, [settings.AIRTABLE_TABLE_PREZENTE])


class PullArhiveazaLectiiTests(TestCase):
    """Pull-ul arhivează lecțiile care nu mai există în Airtable."""

    def setUp(self):
        teacher = User.objects.create_user(
            username='prof_pa', password='Test1234!', role='teacher')
        self.group = Group.objects.create(
            name='S0130 · Modul S', teacher=teacher, weekday=3,
            start_time=datetime.time(17, 30), start_date=datetime.date(2026, 1, 12),
            airtable_record_id='recGRUPA')
        self.alta = Group.objects.create(
            name='A0131 · Modul A', teacher=teacher, weekday=1,
            start_time=datetime.time(18, 0), start_date=datetime.date(2026, 1, 12),
            airtable_record_id='recALTA')
        mk = lambda g, rid: Lesson.objects.create(
            group=g, date=datetime.date(2026, 9, 17), start_time=datetime.time(17, 30),
            airtable_record_id=rid)
        self.vie = mk(self.group, 'recVIE')
        self.stearsa = mk(self.group, 'recSTEARSA')
        self.din_alta_grupa = mk(self.alta, 'recALTALECTIE')

    def _pull(self, records):
        from crm_sync.pull_sync import PullSync
        pull = PullSync(fetch=lambda *a, **k: records)
        pull.map_group = {'recGRUPA': self.group}
        pull.sync_lectii({'recGRUPA'})     # doar S0130 e sincronizată acum
        for l in (self.vie, self.stearsa, self.din_alta_grupa):
            l.refresh_from_db()

    def _rec(self, rid):
        return {'id': rid, 'fields': {'Nume Grupa': ['recGRUPA'],
                                      'Schedule': '2026-09-17T14:30:00.000Z'}}

    def test_lectia_care_lipseste_din_airtable_se_arhiveaza(self):
        self._pull([self._rec('recVIE')])
        self.assertTrue(self.stearsa.is_archived)
        self.assertFalse(self.vie.is_archived)

    def test_nu_atinge_lectiile_grupelor_nesincronizate(self):
        """O rulare-pilot pe o grupă nu are voie să arhiveze restul."""
        self._pull([self._rec('recVIE')])
        self.assertFalse(self.din_alta_grupa.is_archived)

    def test_un_raspuns_gol_nu_arhiveaza_nimic(self):
        """Dacă Airtable nu întoarce nimic (eroare, filtru), nu golim calendarul."""
        self._pull([])
        self.assertFalse(self.vie.is_archived)
        self.assertFalse(self.stearsa.is_archived)

    def test_lectia_care_reapare_se_dezarhiveaza(self):
        self._pull([self._rec('recVIE')])
        self._pull([self._rec('recVIE'), self._rec('recSTEARSA')])
        self.assertFalse(self.stearsa.is_archived)


class PauzaTests(TestCase):
    """O înscriere trecută pe Inactiv în Airtable iese și din platformă.

    Până acum sync-ul doar o sărea, deci elevul pus pe pauză rămânea în lista
    de prezență a profesorului la nesfârșit.
    """

    def setUp(self):
        from teacher_platform.models import Enrollment
        teacher = User.objects.create_user(
            username='prof_pz', password='Test1234!', role='teacher')
        self.student = User.objects.create_user(
            username='mara', password='Test1234!', role='student',
            airtable_record_id='recMARA')
        self.group = Group.objects.create(
            name='M0134 · Modul M', teacher=teacher, weekday=0,
            start_time=datetime.time(17, 30), start_date=datetime.date(2026, 1, 12),
            airtable_record_id='recGRUPA')
        self.enr = Enrollment.objects.create(
            group=self.group, student=self.student, is_active=True,
            airtable_record_id='recINSCR')

    def _pull(self, status):
        from crm_sync.pull_sync import PullSync
        tables = {
            settings.AIRTABLE_TABLE_INSCRIERI: [{'id': 'recINSCR', 'fields': {
                'Grupa': ['recGRUPA'], 'Elev': ['recMARA'], 'Status': status}}],
            settings.AIRTABLE_TABLE_ELEVI: [{'id': 'recMARA', 'fields': {
                'Prenume Copil': 'Mara', 'Nume Familie Copil': 'Nistor'}}],
        }
        pull = PullSync(fetch=lambda t: tables.get(t, []))
        pull.map_group = {'recGRUPA': self.group}
        pull.sync_inscrieri({'recGRUPA'})
        self.enr.refresh_from_db()

    def test_pauza_in_airtable_scoate_elevul_din_platforma(self):
        self._pull('Inactiv')
        self.assertFalse(self.enr.is_active)
        self.assertEqual(self.enr.status, 'inactiv')

    def test_revenirea_il_readuce(self):
        self._pull('Inactiv')
        self._pull('Activ')
        self.assertTrue(self.enr.is_active)

    def test_finalizat_se_pastreaza_ca_atare(self):
        self._pull('Finalizat')
        self.assertFalse(self.enr.is_active)
        self.assertEqual(self.enr.status, 'finalizat')


class CursaPushTests(TestCase):
    """O prezență salvată CÂT TIMP rulează push-ul nu are voie să fie pierdută.

    Cazul real (Vlad, 2.10): platforma arăta `PREZENT · synced`, dar în Airtable
    nu ajunsese niciodată „prezent". Push-ul citea prezențele la început și le
    marca „trimise" la sfârșit — inclusiv valoarea salvată între timp.
    """

    def setUp(self):
        from teacher_platform.models import Attendance, Enrollment
        teacher = User.objects.create_user(
            username='prof_c', password='Test1234!', role='teacher')
        self.student = User.objects.create_user(
            username='vlad', password='Test1234!', role='student',
            airtable_record_id='recVLAD')
        self.group = Group.objects.create(
            name='S0136 · Modul S', teacher=teacher, weekday=0,
            start_time=datetime.time(18, 0), start_date=datetime.date(2026, 1, 12),
            airtable_record_id='recGRUPA')
        Enrollment.objects.create(group=self.group, student=self.student, is_active=True)
        self.lesson = Lesson.objects.create(
            group=self.group, date=datetime.date(2026, 10, 2),
            start_time=datetime.time(17, 0), airtable_record_id='recLECTIE')
        self.att = Attendance.objects.create(
            lesson=self.lesson, student=self.student, is_present=False,
            airtable_record_id='recPREZ')
        Attendance.objects.filter(pk=self.att.pk).update(sync_status='pending')

    def _push(self, during_update=None):
        from crm_sync import push_sync
        from crm_sync.push_sync import PushSync
        self.sent = []

        def update(table, rec_id, fields):
            self.sent.append((table, dict(fields)))
            if during_update and table == settings.AIRTABLE_TABLE_PREZENTE:
                during_update()
            return {'id': rec_id}

        orig = push_sync.PushSync._load_existing_prezente
        push_sync.PushSync._load_existing_prezente = (
            lambda self, ids: {('recVLAD', 'recLECTIE'): ['recPREZ']})
        try:
            PushSync(create_fn=lambda t, f: {'id': 'recNOU'}, update_fn=update,
                     delete_fn=lambda *a: None, fetch_fn=lambda *a, **k: [],
                     only_pending=True, content_all=True).run()
        finally:
            push_sync.PushSync._load_existing_prezente = orig
        self.att.refresh_from_db()

    def _profesorul_salveaza_prezent(self):
        from teacher_platform.models import Attendance
        a = Attendance.objects.get(pk=self.att.pk)
        a.is_present = True
        a.save()   # semnalele o marchează „pending" (deja era)

    def test_prezenta_trimisa_neschimbata_devine_synced(self):
        self._push()
        self.assertEqual(self.att.sync_status, 'synced')

    def test_salvarea_din_timpul_pushului_nu_se_pierde(self):
        self._push(during_update=self._profesorul_salveaza_prezent)
        self.assertTrue(self.att.is_present)
        self.assertEqual(self.att.sync_status, 'pending',
                         'valoarea nouă a fost marcată „trimisă" fără să plece')

    def test_rularea_urmatoare_trimite_valoarea_noua(self):
        self._push(during_update=self._profesorul_salveaza_prezent)
        self._push()
        prezente = [f for t, f in self.sent if t == settings.AIRTABLE_TABLE_PREZENTE]
        self.assertIs(prezente[-1]['Attended'], True)
        self.assertEqual(self.att.sync_status, 'synced')
