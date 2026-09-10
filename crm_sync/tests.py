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
        return Lesson.objects.create(
            group=self.group, date=datetime.date(2026, 9, 15),
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
