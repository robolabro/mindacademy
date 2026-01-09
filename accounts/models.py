from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class User(AbstractUser):
    """
    Model custom pentru utilizatori cu roluri multiple
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Profesor'),
        ('parent', 'Părinte'),
        ('student', 'Elev'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, verbose_name="Telefon")

    # Informații suplimentare
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Data Nașterii")
    parent_email = models.EmailField(blank=True, verbose_name="Email Părinte")
    parent_phone = models.CharField(max_length=15, blank=True, verbose_name="Telefon Părinte")

    # Flag pentru prima autentificare
    must_change_password = models.BooleanField(default=False, verbose_name="Trebuie să schimbe parola")

    # Relație părinte-copil
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Părinte"
    )

    # Avatar/Fotografie
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")

    class Meta:
        verbose_name = "Utilizator"
        verbose_name_plural = "Utilizatori"

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def is_teacher(self):
        return self.role == 'teacher'

    def is_parent(self):
        return self.role == 'parent'

    def is_student(self):
        return self.role == 'student'

    def get_children_list(self):
        """Returnează lista copiilor pentru un părinte"""
        if self.is_parent():
            return self.children.all()
        return []


class TeacherProfile(models.Model):
    """
    Profil extins pentru profesori
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    bio = models.TextField(blank=True, verbose_name="Biografie")
    specialization = models.CharField(max_length=200, blank=True, verbose_name="Specializare")
    experience_years = models.IntegerField(default=0, verbose_name="Ani Experiență")

    # Disponibilitate
    is_active = models.BooleanField(default=True, verbose_name="Activ")

    class Meta:
        verbose_name = "Profil Profesor"
        verbose_name_plural = "Profile Profesori"

    def __str__(self):
        return f"Profil: {self.user.get_full_name()}"


class StudentProfile(models.Model):
    """
    Profil extins pentru elevi
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')

    # Informații școlare
    school_name = models.CharField(max_length=200, blank=True, verbose_name="Școala")
    grade = models.CharField(max_length=50, blank=True, verbose_name="Clasa")

    # Progres
    total_lessons_attended = models.IntegerField(default=0, verbose_name="Lecții Absolvite")
    total_points = models.IntegerField(default=0, verbose_name="Puncte Totale")

    # Setări soroban
    soroban_level = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)],
                                        verbose_name="Nivel Soroban")

    class Meta:
        verbose_name = "Profil Elev"
        verbose_name_plural = "Profile Elevi"

    def __str__(self):
        return f"Profil: {self.user.get_full_name()}"
