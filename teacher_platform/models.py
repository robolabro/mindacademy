from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from courses.models import Course, Location, Module, LessonTemplate
from django.utils import timezone
from django.utils.text import slugify


class Group(models.Model):
    """
    Grupă de elevi creată de profesor
    """
    WEEKDAY_CHOICES = [
        (0, 'Luni'),
        (1, 'Marți'),
        (2, 'Miercuri'),
        (3, 'Joi'),
        (4, 'Vineri'),
        (5, 'Sâmbătă'),
        (6, 'Duminică'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nume Grupă")
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='taught_groups',
        limit_choices_to={'role': 'teacher'},
        verbose_name="Profesor"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Curs"
    )

    # Modul din curs
    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups',
        verbose_name="Modul",
        help_text="Modulul din curs pe care îl parcurge această grupă"
    )

    # Locație
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups',
        verbose_name="Locație"
    )

    # Cod auto-generat (ex: ARITMETICA-12-001)
    code = models.CharField(
        max_length=100,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Cod Grupă",
        help_text="Generat automat: CURS-MODUL-NUMĂR"
    )

    # Data creare editabilă
    created_date = models.DateField(
        default=timezone.now,
        verbose_name="Data Creare",
        help_text="Data la care a fost creată grupa (editabilă)"
    )

    # Program recurent
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, verbose_name="Zi Săptămână")
    start_time = models.TimeField(verbose_name="Ora Start")
    duration_minutes = models.IntegerField(default=90, verbose_name="Durată (minute)")

    # Periodicitate
    start_date = models.DateField(verbose_name="Data Start")
    end_date = models.DateField(null=True, blank=True, verbose_name="Data Sfârșit")
    max_occurrences = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Număr Maximum Lecții",
        help_text="Lasă gol pentru recurență nelimitată"
    )

    # Detalii
    max_students = models.IntegerField(default=8, verbose_name="Număr Maxim Elevi")
    description = models.TextField(blank=True, verbose_name="Descriere")

    # Status
    is_active = models.BooleanField(default=True, verbose_name="Activ")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Grupă"
        verbose_name_plural = "Grupe"
        ordering = ['weekday', 'start_time']

    def generate_code(self):
        """
        Generează cod unic pentru grupă în formatul: CURS-MODUL-NUMĂR
        Ex: ARITMETICA-12-001
        """
        if self.code:  # Dacă deja are cod, nu-l regenera
            return self.code

        course_slug = slugify(self.course.slug if self.course else 'CURS').upper()
        module_id = str(self.module.id) if self.module else '0'

        # Găsește numărul următor pentru acest curs și modul
        existing_groups = Group.objects.filter(
            code__startswith=f"{course_slug}-{module_id}-"
        ).count()

        next_number = existing_groups + 1
        return f"{course_slug}-{module_id}-{next_number:03d}"

    def save(self, *args, **kwargs):
        """Override save pentru a genera cod automat"""
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.code:
            return f"{self.name} ({self.code})"
        return f"{self.name} - {self.get_weekday_display()} {self.start_time}"

    def get_current_students_count(self):
        """Returnează numărul curent de elevi din grupă"""
        return self.students.filter(is_active=True).count()

    def has_available_spots(self):
        """Verifică dacă mai sunt locuri disponibile"""
        return self.get_current_students_count() < self.max_students

    def get_next_lesson_date(self):
        """Calculează data următoarei lecții"""
        from datetime import datetime, timedelta
        today = timezone.now().date()

        # Găsește următoarea zi care se potrivește cu weekday
        days_ahead = self.weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        next_date = today + timedelta(days=days_ahead)

        # Verifică dacă este înainte de end_date
        if self.end_date and next_date > self.end_date:
            return None

        return next_date


class GroupStudent(models.Model):
    """
    Relație dintre elev și grupă (membru)
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students', verbose_name="Grupă")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrolled_groups',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )

    enrolled_date = models.DateField(auto_now_add=True, verbose_name="Data Înrolare")
    is_active = models.BooleanField(default=True, verbose_name="Activ")

    # Progres în cadrul grupei
    lessons_attended = models.IntegerField(default=0, verbose_name="Lecții Prezenți")
    lessons_missed = models.IntegerField(default=0, verbose_name="Lecții Absente")

    class Meta:
        verbose_name = "Elev în Grupă"
        verbose_name_plural = "Elevi în Grupe"
        unique_together = ['group', 'student']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.group.name}"

    def get_attendance_rate(self):
        """Calculează procentul de prezență"""
        total = self.lessons_attended + self.lessons_missed
        if total == 0:
            return 0
        return round((self.lessons_attended / total) * 100, 2)


class Lesson(models.Model):
    """
    Lecție programată sau desfășurată
    """
    STATUS_CHOICES = [
        ('scheduled', 'Programată'),
        ('ongoing', 'În Desfășurare'),
        ('completed', 'Finalizată'),
        ('cancelled', 'Anulată'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='lessons', verbose_name="Grupă")

    # Șablon de lecție (opțional, pentru a lega lecția programată de șablonul din modul)
    lesson_template = models.ForeignKey(
        LessonTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scheduled_lessons',
        verbose_name="Șablon Lecție",
        help_text="Lecția template din modul (opțional)"
    )

    date = models.DateField(verbose_name="Data")
    start_time = models.TimeField(verbose_name="Ora Start")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Ora Sfârșit")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name="Status")

    # Conținut lecție
    topic = models.CharField(max_length=300, blank=True, verbose_name="Subiect")
    description = models.TextField(blank=True, verbose_name="Descriere")
    homework = models.TextField(blank=True, verbose_name="Temă pentru Acasă")

    # Materiale
    materials = models.FileField(upload_to='lesson_materials/', blank=True, null=True, verbose_name="Materiale")

    # Notițe profesor
    teacher_notes = models.TextField(blank=True, verbose_name="Notițe Profesor")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lecție"
        verbose_name_plural = "Lecții"
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.group.name} - {self.date} {self.start_time}"


class Attendance(models.Model):
    """
    Prezență elev la lecție
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances', verbose_name="Lecție")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendances',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )

    is_present = models.BooleanField(default=False, verbose_name="Prezent")
    notes = models.TextField(blank=True, verbose_name="Observații")

    # Evaluare pentru lecție
    performance_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Evaluare Performanță (1-5)",
        help_text="Cum a performat elevul în această lecție"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prezență"
        verbose_name_plural = "Prezențe"
        unique_together = ['lesson', 'student']

    def __str__(self):
        status = "Prezent" if self.is_present else "Absent"
        return f"{self.student.get_full_name()} - {self.lesson.date} ({status})"


class Assignment(models.Model):
    """
    Temă/Exercițiu asignat unei grupe
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='assignments', verbose_name="Grupă")
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments',
        verbose_name="Lecție Asociată"
    )

    title = models.CharField(max_length=300, verbose_name="Titlu")
    description = models.TextField(verbose_name="Descriere")

    # Termene
    assigned_date = models.DateField(auto_now_add=True, verbose_name="Data Asignare")
    due_date = models.DateField(verbose_name="Termen Limită")

    # Fișiere
    attachment = models.FileField(upload_to='assignments/', blank=True, null=True, verbose_name="Fișier Atașat")

    # Punctaj maxim
    max_points = models.IntegerField(default=100, verbose_name="Punctaj Maxim")

    class Meta:
        verbose_name = "Temă"
        verbose_name_plural = "Teme"
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - {self.group.name}"


class AssignmentSubmission(models.Model):
    """
    Predare temă de către elev
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions',
                                   verbose_name="Temă")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )

    # Conținut predare
    text_response = models.TextField(blank=True, verbose_name="Răspuns Text")
    file_response = models.FileField(upload_to='submissions/', blank=True, null=True, verbose_name="Fișier Răspuns")

    # Evaluare
    score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Punctaj Obținut"
    )
    feedback = models.TextField(blank=True, verbose_name="Feedback Profesor")

    # Status
    is_graded = models.BooleanField(default=False, verbose_name="Evaluat")

    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Predare")
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name="Data Evaluare")

    class Meta:
        verbose_name = "Predare Temă"
        verbose_name_plural = "Predări Teme"
        unique_together = ['assignment', 'student']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"

    def is_late(self):
        """Verifică dacă tema a fost predată târziu"""
        return self.submitted_at.date() > self.assignment.due_date


class LessonNote(models.Model):
    """
    Notițe ale profesorului pentru o lecție template dintr-o grupă
    Profesorii pot adăuga notițe specifice pentru fiecare lecție din modul
    """
    lesson_template = models.ForeignKey(
        LessonTemplate,
        on_delete=models.CASCADE,
        related_name='teacher_notes',
        verbose_name="Șablon Lecție"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='lesson_notes',
        verbose_name="Grupă"
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='lesson_notes',
        verbose_name="Profesor"
    )

    notes = models.TextField(verbose_name="Notițe", help_text="Notițe și observații pentru această lecție")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notiță Lecție"
        verbose_name_plural = "Notițe Lecții"
        unique_together = ['lesson_template', 'group', 'teacher']

    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.lesson_template.name} ({self.group.name})"