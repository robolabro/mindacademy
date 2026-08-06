"""
Date de test (demo) pentru scenariile de testare — NU ating sincronizarea.

Creează un profesor + câțiva copii + o grupă online + înscrieri + câteva lecții,
toate marcate „demo" (username prefix `demo_`, grupă „DEMO ..."). Nu au
airtable_record_id, deci pull-ul nu le arhivează și push-ul le ignoră — sunt
strict pentru testarea fluxurilor din platformă.

    python manage.py seed_test_data          # creează / actualizează
    python manage.py seed_test_data --wipe    # șterge tot ce e demo

Parola pentru toți userii demo: Test1234!
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


DEMO_PASSWORD = "Test1234!"
GROUP_NAME = "DEMO · Grupă Online (test)"
STUDENTS = [
    ("demo_elev_ana", "Ana", "Demo", "F"),
    ("demo_elev_bogdan", "Bogdan", "Demo", "M"),
    ("demo_elev_carla", "Carla", "Demo", "F"),
    ("demo_elev_david", "David", "Demo", "M"),
]


class Command(BaseCommand):
    help = "Creează date demo pentru testarea platformei (profesor + copii + grupă online)."

    def add_arguments(self, parser):
        parser.add_argument('--wipe', action='store_true', help="Șterge datele demo.")

    def handle(self, *args, **opts):
        from accounts.models import User, StudentProfile, TeacherProfile
        from teacher_platform.models import Group, Enrollment, Lesson

        if opts['wipe']:
            Group.objects.filter(name=GROUP_NAME).delete()  # cascade lecții/înscrieri
            n, _ = User.objects.filter(username__startswith='demo_').delete()
            self.stdout.write(self.style.SUCCESS(f"Date demo șterse ({n} obiecte)."))
            return

        # --- Profesor ---
        prof, _ = User.objects.get_or_create(username='demo_prof', defaults=dict(
            role='teacher', first_name='Profesor', last_name='Demo', email='demo.prof@example.com'))
        prof.role = 'teacher'
        prof.set_password(DEMO_PASSWORD)
        prof.must_change_password = False
        prof.save()
        TeacherProfile.objects.get_or_create(user=prof)

        # --- Grupă online ---
        today = timezone.now().date()
        group, _ = Group.objects.get_or_create(name=GROUP_NAME, defaults=dict(
            teacher=prof, weekday=2, start_time='17:30', start_date=today - timedelta(days=28),
            duration_minutes=90, lesson_type='online',
            meeting_link='https://meet.example.com/demo-grupa'))
        group.teacher = prof
        group.lesson_type = 'online'
        group.meeting_link = 'https://meet.example.com/demo-grupa'
        group.save()

        # --- Copii + înscrieri ---
        students = []
        for uname, first, last, sex in STUDENTS:
            u, _ = User.objects.get_or_create(username=uname, defaults=dict(
                role='student', first_name=first, last_name=last))
            u.role = 'student'
            u.set_password(DEMO_PASSWORD)
            u.must_change_password = False
            u.save()
            StudentProfile.objects.get_or_create(user=u, defaults=dict(sex=sex))
            sp = u.student_profile
            sp.group = group
            sp.sex = sex or sp.sex
            sp.save()
            Enrollment.objects.get_or_create(group=group, student=u, defaults=dict(
                is_active=True, status='activ'))
            students.append(u)

        # --- Câteva lecții (una trecută/finalizată, una viitoare) ---
        Lesson.objects.get_or_create(
            group=group, date=today - timedelta(days=7), defaults=dict(
                start_time='17:30', status='completed',
                topic='R1 · Recapitulare', lesson_takeaways=''))
        Lesson.objects.get_or_create(
            group=group, date=today + timedelta(days=1), defaults=dict(
                start_time='17:30', status='scheduled', topic='R2 · Prietenul mic'))

        self.stdout.write(self.style.SUCCESS(
            f"Date demo create: profesor + {len(students)} copii + grupa {GROUP_NAME} (online)."))
        self.stdout.write("\nConturi (parolă pentru toți: %s):" % DEMO_PASSWORD)
        self.stdout.write(f"  Profesor: demo_prof")
        for uname, first, last, _ in STUDENTS:
            self.stdout.write(f"  Elev:     {uname}  ({first} {last})")
        self.stdout.write(self.style.WARNING(
            "\nȘterge cu: python manage.py seed_test_data --wipe"))
