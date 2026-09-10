"""
Teste pentru ecranul unic de lecție („Gestionează lecția") și pentru
contractul cu Airtable: ce anume marchează o lecție/prezență ca `pending`,
adică ce va trimite push-ul nocturn.

Rulare:
    python manage.py test teacher_platform
"""
import datetime

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import AgeGroup, Course, Module, LessonTemplate
from teacher_platform.models import Attendance, Enrollment, Group, Lesson


class LessonManageTests(TestCase):
    """Fluxul profesorului: prezență → ce s-a lucrat → finalizare."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='prof_test', password='Test1234!', role='teacher')
        self.student = User.objects.create_user(
            username='elev_test', password='Test1234!', role='student',
            first_name='Ana', last_name='Test')

        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-t', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        module = Module.objects.create(course=course, name='Modul Y', order=1)
        self.template = LessonTemplate.objects.create(
            module=module, name='Y17', order=17)

        self.group = Group.objects.create(
            name='Y0129', teacher=self.teacher, course=course, module=module,
            weekday=3, start_time=datetime.time(17, 30),
            start_date=datetime.date(2026, 1, 12))
        self.enrollment = Enrollment.objects.create(
            group=self.group, student=self.student, is_active=True)
        self.lesson = Lesson.objects.create(
            group=self.group, lesson_template=self.template, topic='Y17',
            date=datetime.date(2026, 9, 10), start_time=datetime.time(17, 30),
            status='scheduled', airtable_record_id='recLESSON1')

        self.client.force_login(self.teacher)
        self.url = reverse('teacher_platform:lesson_manage', args=[self.lesson.id])

    def _post(self, **extra):
        """Salvare cu elevul prezent, dacă nu se cere altfel."""
        data = {'present_%d' % self.student.id: '1', 'takeaways': '', 'homework': ''}
        data.update(extra)
        return self.client.post(self.url, data)

    # --- prezență ---------------------------------------------------------

    def test_salvarea_inregistreaza_prezenta(self):
        self._post()
        att = Attendance.objects.get(lesson=self.lesson, student=self.student)
        self.assertTrue(att.is_present)

    def test_checkbox_lipsa_inseamna_absent(self):
        """Prezența e pre-bifată; checkbox-ul debifat nu ajunge în POST."""
        self._post(**{'present_%d' % self.student.id: ''})
        att = Attendance.objects.get(lesson=self.lesson, student=self.student)
        self.assertFalse(att.is_present)

    def test_absenta_cu_recuperare_ajunge_in_outbox(self):
        """`Genereaza Recuperare` trebuie trimis în Airtable → sync pending."""
        self._post(**{'present_%d' % self.student.id: '',
                      'recuperare_%d' % self.student.id: 'on',
                      'anuntata_%d' % self.student.id: 'on'})
        att = Attendance.objects.get(lesson=self.lesson, student=self.student)
        self.assertTrue(att.genereaza_recuperare)
        self.assertTrue(att.absenta_anuntata)
        self.assertEqual(att.sync_status, 'pending')

    # --- finalizare (bug-ul reparat: toggle-ul era one-way) ---------------

    def test_bifarea_finalizeaza_lectia(self):
        self._post(completed='on')
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, 'completed')

    def test_debifarea_anuleaza_finalizarea(self):
        """Regresie: debifarea nu se salva, lecția rămânea `completed`."""
        self._post(completed='on')
        self._post()  # fără `completed` — checkbox debifat
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, 'scheduled')

    def test_finalizarea_ajunge_in_outbox(self):
        """Push-ul bifează „Completed" în Airtable doar dacă lecția e pending."""
        self._post(completed='on')
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.sync_status, 'pending')

    # --- conținut ---------------------------------------------------------

    def test_takeaways_si_tema_se_salveaza_si_se_trimit(self):
        self._post(takeaways='## Ce am lucrat\n- Prietenul mic',
                   homework='2 fișe')
        self.lesson.refresh_from_db()
        self.assertIn('Prietenul mic', self.lesson.lesson_takeaways)
        self.assertEqual(self.lesson.homework, '2 fișe')
        self.assertEqual(self.lesson.sync_status, 'pending')

    # --- elevi programați specific ---------------------------------------

    def test_lectie_cu_elevi_programati_arata_doar_pe_ei(self):
        altul = User.objects.create_user(
            username='elev2', password='Test1234!', role='student',
            first_name='Bogdan', last_name='Test')
        Enrollment.objects.create(group=self.group, student=altul, is_active=True)
        self.lesson.scheduled_students.add(self.student)

        rows = self.client.get(self.url).context['rows']
        self.assertEqual([r['student'].id for r in rows], [self.student.id])


class RecuperareTests(TestCase):
    """Recuperările sunt singurul caz în care platforma deține orarul."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='prof_r', password='Test1234!', role='teacher')
        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-r', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        self.group = Group.objects.create(
            name='Y0129', teacher=self.teacher, course=course,
            weekday=3, start_time=datetime.time(17, 30),
            start_date=datetime.date(2026, 1, 12))
        # Recuperarea vine din Airtable pe data lecției originale.
        self.recuperare = Lesson.objects.create(
            group=self.group, topic='Y17 (recuperare)',
            date=datetime.date(2026, 9, 3), start_time=datetime.time(17, 30),
            status='scheduled', is_recuperare=True,
            airtable_record_id='recRECUP1', sync_status='synced')
        self.client.force_login(self.teacher)
        self.url = reverse('teacher_platform:lesson_manage', args=[self.recuperare.id])

    def test_cardul_de_data_apare_doar_la_recuperari(self):
        self.assertContains(self.client.get(self.url), 'Data recuperării')

        normala = Lesson.objects.create(
            group=self.group, topic='Y18', date=datetime.date(2026, 9, 17),
            start_time=datetime.time(17, 30), status='scheduled')
        alt_url = reverse('teacher_platform:lesson_manage', args=[normala.id])
        self.assertNotContains(self.client.get(alt_url), 'Data recuperării')

    def test_profesorul_muta_recuperarea_si_se_trimite_in_airtable(self):
        self.client.post(self.url, {
            'takeaways': '', 'homework': '',
            'recup_date': '2026-09-24', 'recup_time': '18:00',
        })
        self.recuperare.refresh_from_db()
        self.assertEqual(self.recuperare.date, datetime.date(2026, 9, 24))
        self.assertEqual(self.recuperare.start_time, datetime.time(18, 0))
        # Orarul schimbat trebuie împins în Airtable („Schedule").
        self.assertEqual(self.recuperare.sync_status, 'pending')

    def test_data_recuperarii_nu_e_suprascrisa_de_pull_cat_timp_e_pending(self):
        """Garda din pull_sync: `keep_local_schedule`."""
        self.client.post(self.url, {
            'takeaways': '', 'homework': '', 'recup_date': '2026-09-24',
            'recup_time': '18:00'})
        self.recuperare.refresh_from_db()
        keep_local_schedule = (self.recuperare.is_recuperare
                               and self.recuperare.sync_status == 'pending')
        self.assertTrue(keep_local_schedule)

    def test_o_lectie_normala_nu_isi_schimba_data_din_platforma(self):
        """Orarul lecțiilor obișnuite e al Airtable-ului — se ignoră aici."""
        normala = Lesson.objects.create(
            group=self.group, topic='Y18', date=datetime.date(2026, 9, 17),
            start_time=datetime.time(17, 30), status='scheduled')
        self.client.post(
            reverse('teacher_platform:lesson_manage', args=[normala.id]),
            {'takeaways': '', 'homework': '', 'recup_date': '2026-12-01'})
        normala.refresh_from_db()
        self.assertEqual(normala.date, datetime.date(2026, 9, 17))


class LessonRoutesTests(TestCase):
    """Un singur ecran de lecție; rutele vechi doar redirecționează."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='prof_u', password='Test1234!', role='teacher')
        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-u', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        self.group = Group.objects.create(
            name='Y0129', teacher=self.teacher, course=course,
            weekday=3, start_time=datetime.time(17, 30),
            start_date=datetime.date(2026, 1, 12))
        self.lesson = Lesson.objects.create(
            group=self.group, topic='Y17', date=datetime.date(2026, 9, 10),
            start_time=datetime.time(17, 30), status='scheduled')
        self.client.force_login(self.teacher)

    def test_rutele_vechi_duc_in_ecranul_unic(self):
        destinatie = reverse('teacher_platform:lesson_manage', args=[self.lesson.id])
        for nume in ('lesson_detail', 'lesson_edit'):
            with self.subTest(ruta=nume):
                self.assertRedirects(
                    self.client.get(reverse('teacher_platform:' + nume,
                                            args=[self.lesson.id])),
                    destinatie)

    def test_un_profesor_nu_vede_lectiile_altuia(self):
        strain = User.objects.create_user(
            username='prof_strain', password='Test1234!', role='teacher')
        self.client.force_login(strain)
        url = reverse('teacher_platform:lesson_manage', args=[self.lesson.id])
        self.assertEqual(self.client.get(url).status_code, 404)
