from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from courses.models import Course, Location, Module, LessonTemplate
from crm_sync.models import AirtableSyncMixin
from django.utils import timezone
from django.utils.text import slugify


class Group(AirtableSyncMixin, models.Model):
    """
    Grupă de elevi creată de profesor.
    Mapată din tabelul „Grupe" din Airtable (cheie de business: „Cod Grupa").
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

    # Tip lecție: cu prezență fizică sau online
    LESSON_TYPE_CHOICES = [
        ('fizic', 'Fizic'),
        ('online', 'Online'),
    ]
    lesson_type = models.CharField(
        max_length=10,
        choices=LESSON_TYPE_CHOICES,
        default='fizic',
        verbose_name="Tip Lecție"
    )
    meeting_link = models.URLField(
        blank=True,
        verbose_name="Link Videoconferință",
        help_text="Link-ul de Zoom/Google Meet pentru grupele online (trimis părinților)"
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

    # „Cod Grupa" din Airtable — cheia de business a tabelului „Grupe".
    # Distinct de `code` (cod intern generat de platformă).
    airtable_cod_grupa = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="Cod Grupa (Airtable)",
        help_text="Codul grupei din Airtable (cheia de business din tabelul Grupe)."
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


class Enrollment(AirtableSyncMixin, models.Model):
    """
    Înscrierea unui elev la o grupă (fostul „GroupStudent").
    Mapată din tabelul „Inscrieri" din Airtable — modelul care leagă
    Elev de Grupă. Doar înscrierile cu status „Inscris" sunt mapate activ.
    """
    # Valori aliniate cu tabelul „Inscrieri" din Airtable (câmpul Status).
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('activ', 'Activ'),
        ('inactiv', 'Inactiv'),
        ('finalizat', 'Finalizat'),
    ]

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

    # Status înscriere (din Airtable „Inscrieri") + data încheierii.
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='activ',
        db_index=True,
        verbose_name="Status Înscriere"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data Sfârșit Înscriere",
        help_text="Data la care înscrierea a fost încheiată (din Airtable)."
    )

    # Progres în cadrul grupei
    lessons_attended = models.IntegerField(default=0, verbose_name="Lecții Prezenți")
    lessons_missed = models.IntegerField(default=0, verbose_name="Lecții Absente")

    # Progres calculat în Airtable (read-only, adus la pull din Inscrieri):
    # „Prezente in Modul Curent (from Elev)" și „Lectii Ramase (from Elev)".
    # Airtable rămâne sursa acestui calcul — noi doar îl reflectăm.
    airtable_prezente_modul = models.IntegerField(
        null=True, blank=True, verbose_name="Prezențe în modulul curent (Airtable)")
    airtable_lectii_ramase = models.IntegerField(
        null=True, blank=True, verbose_name="Lecții rămase din modul (Airtable)")

    class Meta:
        verbose_name = "Înscriere"
        verbose_name_plural = "Înscrieri"
        unique_together = ['group', 'student']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.group.name}"

    def get_attendance_rate(self):
        """Calculează procentul de prezență"""
        total = self.lessons_attended + self.lessons_missed
        if total == 0:
            return 0
        return round((self.lessons_attended / total) * 100, 2)


class Lesson(AirtableSyncMixin, models.Model):
    """
    Lecție programată sau desfășurată.
    Mapată din tabelul „Lectii" din Airtable — generat de automatizări Airtable.
    Sincronizarea face DOAR UPDATE pe lecțiile existente (găsite după
    airtable_record_id), niciodată CREATE.
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

    # Tip lecție (din Airtable): marcate distinct în UI ca profesorul să le
    # recunoască ușor. Setate la pull din câmpurile „Lectie Recuperare" /
    # „Lectie Individuala" ale tabelului Lectii.
    is_recuperare = models.BooleanField(default=False, verbose_name="Lecție de recuperare")
    is_individual = models.BooleanField(default=False, verbose_name="Lecție individuală")

    # Conținut lecție
    topic = models.CharField(max_length=300, blank=True, verbose_name="Subiect")
    description = models.TextField(blank=True, verbose_name="Descriere")
    homework = models.TextField(blank=True, verbose_name="Temă pentru Acasă")

    # Materiale
    materials = models.FileField(upload_to='lesson_materials/', blank=True, null=True, verbose_name="Materiale")

    # Notițe profesor
    teacher_notes = models.TextField(blank=True, verbose_name="Notițe Profesor")

    # Ce s-a lucrat efectiv la lecție (împins către Airtable la finalizare).
    lesson_takeaways = models.TextField(
        blank=True,
        verbose_name="Ce s-a lucrat (takeaways)",
        help_text="Rezumatul a ceea ce s-a parcurs efectiv la lecție."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lecție"
        verbose_name_plural = "Lecții"
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.group.name} - {self.date} {self.start_time}"


class Attendance(AirtableSyncMixin, models.Model):
    """
    Prezență elev la lecție.
    Sursa de adevăr pentru EXECUȚIE — se face PUSH către tabelul „Prezente"
    din Airtable. NU scriem niciodată în „Progres Lectii" (generat de
    automatizarea Airtable pe baza Prezențelor cu Attended=true).
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances', verbose_name="Lecție")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendances',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )

    # Legătura către înscrierea corespunzătoare (elev × grupă). Nullabil —
    # se completează la sincronizare / creare prezență.
    enrollment = models.ForeignKey(
        'Enrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        verbose_name="Înscriere"
    )

    is_present = models.BooleanField(default=False, verbose_name="Prezent")
    notes = models.TextField(blank=True, verbose_name="Observații")

    # Absență anunțată în prealabil (afectează generarea recuperării).
    absenta_anuntata = models.BooleanField(
        default=False,
        verbose_name="Absență anunțată"
    )
    # Marchează dacă absența trebuie să genereze o lecție de recuperare.
    genereaza_recuperare = models.BooleanField(
        default=False,
        verbose_name="Generează recuperare"
    )

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

class SimulatorAssignment(models.Model):
    """
    Temă pe simulatoare pentru o grupă, cu perioadă de lucru.
    Dacă `student` este setat, tema este personalizată pentru acel elev
    (suprascrie tema de grupă pentru el); altfel se aplică întregii grupe.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='simulator_assignments', verbose_name="Grupă")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='personal_simulator_assignments',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev (doar pentru temă personalizată)"
    )

    title = models.CharField(max_length=200, verbose_name="Titlu", default="Temă de casă")
    start_date = models.DateField(verbose_name="De la data")
    end_date = models.DateField(verbose_name="Până la data")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creată la")

    class Meta:
        verbose_name = "Temă Simulatoare"
        verbose_name_plural = "Teme Simulatoare"
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        target = self.student.get_full_name() if self.student else self.group.name
        return f"{self.title} · {target} ({self.start_date} → {self.end_date})"

    @property
    def is_active(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class SimulatorTask(models.Model):
    """
    O sarcină dintr-o temă: un simulator + setările lui + ținta
    (număr de exerciții sau minute de lucru).
    Setările sunt stocate ca JSON și corespund parametrilor simulatoarelor:
    complexity, digits (listă), difficulty, speed, terms, columns etc.
    """
    SIMULATOR_CHOICES = [
        ('anzan', 'Calcul mental (Anzan)'),
        ('flashcards', 'Cartonașe flash'),
        ('flashcard-exercises', 'Exerciții'),
        ('worksheet', 'Fișă de lucru'),
    ]
    TARGET_CHOICES = [
        ('count', 'Număr de exerciții'),
        ('minutes', 'Minute de lucru'),
    ]

    assignment = models.ForeignKey(SimulatorAssignment, on_delete=models.CASCADE,
                                   related_name='tasks', verbose_name="Temă")
    order = models.PositiveIntegerField(default=1, verbose_name="Ordine")

    simulator = models.CharField(max_length=30, choices=SIMULATOR_CHOICES, verbose_name="Simulator")
    settings = models.JSONField(default=dict, verbose_name="Setări simulator")

    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES,
                                   default='count', verbose_name="Tip țintă")
    target_value = models.PositiveIntegerField(default=5, verbose_name="Valoare țintă")

    class Meta:
        verbose_name = "Sarcină Simulator"
        verbose_name_plural = "Sarcini Simulator"
        ordering = ['assignment', 'order']

    def __str__(self):
        return f"{self.get_simulator_display()} ({self.get_target_display()})"

    def get_target_display(self):
        if self.target_type == 'minutes':
            return f"{self.target_value} min"
        return f"{self.target_value} exerciții"


class SimulatorTaskResult(models.Model):
    """
    Rezultatul ZILNIC al unui elev la o sarcină de simulator.
    Temele sunt zilnice: ținta sarcinii trebuie atinsă în fiecare zi
    din perioada temei; fiecare zi are propriul rând de rezultat.
    """
    task = models.ForeignKey(SimulatorTask, on_delete=models.CASCADE,
                             related_name='results', verbose_name="Sarcină")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='simulator_results',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )
    date = models.DateField(default=timezone.localdate, verbose_name="Ziua")

    completed_exercises = models.PositiveIntegerField(default=0, verbose_name="Exerciții rezolvate")
    correct = models.PositiveIntegerField(default=0, verbose_name="Corecte")
    incorrect = models.PositiveIntegerField(default=0, verbose_name="Greșite")
    time_spent_seconds = models.PositiveIntegerField(default=0, verbose_name="Timp lucrat (sec)")

    completed = models.BooleanField(default=False, verbose_name="Finalizată (ziua)")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Finalizată la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")

    class Meta:
        verbose_name = "Rezultat Sarcină (zi)"
        verbose_name_plural = "Rezultate Sarcini (zile)"
        unique_together = ['task', 'student', 'date']

    def __str__(self):
        return f"{self.student.get_full_name()} · {self.task} · {self.date} · {self.correct}/{self.completed_exercises}"


class SimulatorPracticeLog(models.Model):
    """
    Jurnal ZILNIC de antrenament liber pe simulatoare (în afara temelor).
    Un rând per elev × simulator × zi; contoarele se acumulează.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='practice_logs',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )
    simulator = models.CharField(max_length=30, choices=SimulatorTask.SIMULATOR_CHOICES,
                                 verbose_name="Simulator")
    date = models.DateField(default=timezone.localdate, verbose_name="Ziua")

    exercises = models.PositiveIntegerField(default=0, verbose_name="Exerciții")
    correct = models.PositiveIntegerField(default=0, verbose_name="Corecte")
    incorrect = models.PositiveIntegerField(default=0, verbose_name="Greșite")
    time_spent_seconds = models.PositiveIntegerField(default=0, verbose_name="Timp (sec)")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")

    class Meta:
        verbose_name = "Antrenament Liber (zi)"
        verbose_name_plural = "Antrenamente Libere (zile)"
        unique_together = ['student', 'simulator', 'date']

    def __str__(self):
        return f"{self.student.get_full_name()} · {self.get_simulator_display()} · {self.date}"


class LiveSession(models.Model):
    """
    O lecție live (online) pornită de profesor pentru o grupă.
    O singură sesiune activă per grupă la un moment dat.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='live_sessions', verbose_name="Grupă")
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='live_sessions',
        limit_choices_to={'role': 'teacher'},
        verbose_name="Profesor"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='live_sessions',
        verbose_name="Lecție programată (opțional)"
    )

    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Pornită la")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Închisă la")

    class Meta:
        verbose_name = "Lecție Live"
        verbose_name_plural = "Lecții Live"
        ordering = ['-started_at']

    @property
    def is_active(self):
        return self.ended_at is None

    def __str__(self):
        state = 'activă' if self.is_active else 'închisă'
        return f"Live {self.group.name} · {self.started_at:%d.%m.%Y %H:%M} ({state})"


class LiveTask(models.Model):
    """
    O sarcină alocată în timpul lecției live: pentru toată grupa sau
    personalizată pentru un elev. Aceeași structură de setări ca la teme.
    """
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE,
                                related_name='tasks', verbose_name="Sesiune")
    order = models.PositiveIntegerField(default=1, verbose_name="Ordine")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='personal_live_tasks',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev (doar pentru sarcină individuală)"
    )

    simulator = models.CharField(max_length=30, choices=SimulatorTask.SIMULATOR_CHOICES,
                                 verbose_name="Simulator")
    settings = models.JSONField(default=dict, verbose_name="Setări simulator")

    target_type = models.CharField(max_length=10, choices=SimulatorTask.TARGET_CHOICES,
                                   default='count', verbose_name="Tip țintă")
    target_value = models.PositiveIntegerField(default=5, verbose_name="Valoare țintă")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Alocată la")

    class Meta:
        verbose_name = "Sarcină Live"
        verbose_name_plural = "Sarcini Live"
        ordering = ['session', 'order']

    def get_target_display(self):
        if self.target_type == 'minutes':
            return f"{self.target_value} min"
        return f"{self.target_value} exerciții"

    def __str__(self):
        target = self.student.get_full_name() if self.student else 'toată grupa'
        return f"{self.get_simulator_display()} · {target}"


class LiveTaskResult(models.Model):
    """Rezultatul unui elev la o sarcină live (actualizat în timp real)."""
    task = models.ForeignKey(LiveTask, on_delete=models.CASCADE,
                             related_name='results', verbose_name="Sarcină")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='live_results',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )

    completed_exercises = models.PositiveIntegerField(default=0, verbose_name="Exerciții rezolvate")
    correct = models.PositiveIntegerField(default=0, verbose_name="Corecte")
    incorrect = models.PositiveIntegerField(default=0, verbose_name="Greșite")
    time_spent_seconds = models.PositiveIntegerField(default=0, verbose_name="Timp lucrat (sec)")

    completed = models.BooleanField(default=False, verbose_name="Finalizată")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Finalizată la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")

    # Istoric detaliat: [{ex: "12 + 5 − 3", ca: 14, ua: 14, ok: true, t: 6.2}, ...]
    exercise_log = models.JSONField(default=list, blank=True, verbose_name="Istoric exerciții")

    class Meta:
        verbose_name = "Rezultat Sarcină Live"
        verbose_name_plural = "Rezultate Sarcini Live"
        unique_together = ['task', 'student']

    def __str__(self):
        return f"{self.student.get_full_name()} · {self.task} · {self.correct}/{self.completed_exercises}"


class LiveParticipant(models.Model):
    """
    Prezența unui elev într-o lecție live — actualizată prin heartbeat
    din platforma elevului; „conectat" = last_seen în ultimele ~30s.
    """
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE,
                                related_name='participants', verbose_name="Sesiune")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='live_participations',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Conectat la")
    last_seen = models.DateTimeField(auto_now=True, verbose_name="Văzut ultima dată")

    class Meta:
        verbose_name = "Participant Live"
        verbose_name_plural = "Participanți Live"
        unique_together = ['session', 'student']

    def __str__(self):
        return f"{self.student.get_full_name()} · {self.session}"


class LessonMilestoneProgress(models.Model):
    """
    Bifarea unui milestone de lecție de către profesor, în contextul unei
    grupe (cât de departe a ajuns grupa în structura lecției din curriculum).
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='milestone_progress', verbose_name="Grupă")
    milestone = models.ForeignKey('courses.LessonMilestone', on_delete=models.CASCADE,
                                  related_name='group_progress', verbose_name="Milestone")
    is_done = models.BooleanField(default=False, verbose_name="Bifat")
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name="Bifat la")
    checked_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='milestone_checks',
        limit_choices_to={'role': 'teacher'}, verbose_name="Bifat de"
    )

    class Meta:
        verbose_name = "Progres Milestone"
        verbose_name_plural = "Progres Milestones"
        unique_together = ['group', 'milestone']

    def __str__(self):
        state = '✓' if self.is_done else '○'
        return f"{state} {self.group.name} · {self.milestone.title}"
