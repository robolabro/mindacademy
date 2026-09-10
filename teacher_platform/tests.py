"""
Teste pentru ecranul unic de lecție („Gestionează lecția") și pentru
contractul cu Airtable: ce anume marchează o lecție/prezență ca `pending`,
adică ce va trimite push-ul nocturn.

Rulare:
    python manage.py test teacher_platform
"""
import datetime

from django.test import TestCase
from django.utils import timezone
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


class CalendarTests(TestCase):
    """Calendarul: zi / săptămână / lună, ancorat pe azi."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='prof_cal', password='Test1234!', role='teacher')
        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-c', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        self.group = Group.objects.create(
            name='A0131 · Modul A', teacher=self.teacher, course=course, weekday=1,
            start_time=datetime.time(18, 0), start_date=datetime.date(2026, 1, 12))
        self.client.force_login(self.teacher)
        self.url = reverse('teacher_platform:calendar')

    def _lesson(self, day, **kw):
        return Lesson.objects.create(
            group=self.group, date=day, start_time=datetime.time(18, 0), **kw)

    def test_implicit_arata_saptamana_cu_ziua_de_azi(self):
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx['view_mode'], 'week')
        self.assertTrue(ctx['range_start'] <= ctx['today'] <= ctx['range_end'])
        self.assertEqual((ctx['range_end'] - ctx['range_start']).days, 6)

    def test_saptamana_incepe_luni(self):
        ctx = self.client.get(self.url, {'view': 'week', 'd': '2026-09-10'}).context
        self.assertEqual(ctx['range_start'], datetime.date(2026, 9, 7))
        self.assertEqual(ctx['range_end'], datetime.date(2026, 9, 13))

    def test_vederea_pe_zi_arata_o_singura_zi(self):
        self._lesson(datetime.date(2026, 9, 10))
        self._lesson(datetime.date(2026, 9, 11))
        ctx = self.client.get(self.url, {'view': 'day', 'd': '2026-09-10'}).context
        self.assertEqual(ctx['lesson_count'], 1)
        self.assertEqual(len(ctx['days']), 1)

    def test_grila_lunii_are_saptamani_intregi(self):
        ctx = self.client.get(self.url, {'view': 'month', 'd': '2026-09-10'}).context
        self.assertEqual(ctx['range_start'], datetime.date(2026, 9, 1))
        self.assertEqual(ctx['range_end'], datetime.date(2026, 9, 30))
        self.assertTrue(all(len(w) == 7 for w in ctx['weeks']))
        # zilele din lunile vecine sunt marcate, ca să se vadă estompate
        self.assertTrue(any(d['outside'] for d in ctx['days']))

    def test_navigarea_muta_cu_un_pas(self):
        ctx = self.client.get(self.url, {'view': 'week', 'd': '2026-09-10'}).context
        self.assertEqual(ctx['prev_anchor'], datetime.date(2026, 9, 3))
        self.assertEqual(ctx['next_anchor'], datetime.date(2026, 9, 17))

    def test_o_recuperare_se_vede_langa_lectia_cu_care_se_suprapune(self):
        """Recuperările pot fi la aceeași oră cu altă lecție — se afișează ambele."""
        day = datetime.date(2026, 9, 15)
        self._lesson(day)
        self._lesson(day, is_recuperare=True)
        ctx = self.client.get(self.url, {'view': 'day', 'd': day.isoformat()}).context
        self.assertEqual(len(ctx['days'][0]['lessons']), 2)

    def test_nu_se_creeaza_lectii_din_calendar(self):
        """Lecțiile vin din Airtable — butonul de adăugare a fost scos."""
        self.assertNotContains(self.client.get(self.url), 'Adaugă Lecție')

    def test_calendarul_arata_doar_lectiile_profesorului(self):
        strain = User.objects.create_user(
            username='prof_alt', password='Test1234!', role='teacher')
        alt_group = Group.objects.create(
            name='X0001 · Modul X', teacher=strain, weekday=1,
            start_time=datetime.time(18, 0), start_date=datetime.date(2026, 1, 12))
        Lesson.objects.create(group=alt_group, date=timezone.localdate(),
                              start_time=datetime.time(18, 0))
        self.assertEqual(self.client.get(self.url).context['lesson_count'], 0)


class CalendarListTests(TestCase):
    """Vederea „Listă": jurnal pe zile, pornit de la azi, cu lecțiile restante."""

    def setUp(self):
        self.teacher = User.objects.create_user(
            username='prof_list', password='Test1234!', role='teacher')
        age = AgeGroup.objects.create(name='7-10 ani', min_age=7, max_age=10)
        course = Course.objects.create(
            title='Soroban', slug='soroban-l', description='x', age_group=age,
            price=0, frequency='saptamanal', group_size=6)
        self.group = Group.objects.create(
            name='A0131 · Modul A', teacher=self.teacher, course=course, weekday=1,
            start_time=datetime.time(18, 0), start_date=datetime.date(2026, 1, 12))
        self.client.force_login(self.teacher)
        self.url = reverse('teacher_platform:calendar')
        self.today = timezone.localdate()

    def _lesson(self, day, **kw):
        return Lesson.objects.create(
            group=self.group, date=day, start_time=datetime.time(18, 0), **kw)

    def test_lista_e_o_vedere_valida_dar_nu_cea_implicita(self):
        self.assertEqual(self.client.get(self.url).context['view_mode'], 'week')
        self.assertEqual(
            self.client.get(self.url, {'view': 'list'}).context['view_mode'], 'list')

    def test_lista_sare_peste_zilele_goale(self):
        self._lesson(self.today)
        ctx = self.client.get(self.url, {'view': 'list',
                                         'd': self.today.isoformat()}).context
        self.assertTrue(all(d['lessons'] for d in ctx['listing']))
        self.assertEqual(len(ctx['listing']), 1)

    def test_lista_ancoreaza_ziua_curenta(self):
        self._lesson(self.today)
        html = self.client.get(self.url, {'view': 'list'}).content.decode()
        self.assertIn('id="today"', html)

    def test_lectiile_trecute_necompletate_sunt_semnalate(self):
        ieri = self.today - datetime.timedelta(days=1)
        restanta = self._lesson(ieri, status='scheduled')
        facuta = self._lesson(ieri, status='completed')
        self.assertTrue(restanta.is_overdue)
        self.assertEqual(restanta.status_label, 'De completat')
        self.assertFalse(facuta.is_overdue)

    def test_o_recuperare_netinuta_apare_tot_ca_de_completat(self):
        """Cazul real: recuperarea nu s-a ținut și trebuie reprogramată."""
        ieri = self.today - datetime.timedelta(days=1)
        recup = self._lesson(ieri, is_recuperare=True, status='scheduled')
        self.assertEqual(recup.status_kind, 'overdue')

    def test_lectiile_viitoare_nu_sunt_restante(self):
        maine = self.today + datetime.timedelta(days=1)
        self.assertFalse(self._lesson(maine).is_overdue)

    def test_contorul_de_restante(self):
        prima = self.today.replace(day=1)
        if prima < self.today:
            self._lesson(prima, status='scheduled')
            ctx = self.client.get(self.url, {'view': 'list',
                                             'd': self.today.isoformat()}).context
            self.assertEqual(ctx['overdue_count'], 1)
