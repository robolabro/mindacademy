from django.db import models
from accounts.models import User
from django.utils import timezone


class SorobanExercise(models.Model):
    """
    Exercițiu pentru abac soroban
    """
    DIFFICULTY_CHOICES = [
        ('beginner', 'Începător'),
        ('intermediate', 'Intermediar'),
        ('advanced', 'Avansat'),
        ('expert', 'Expert'),
    ]

    OPERATION_CHOICES = [
        ('addition', 'Adunare'),
        ('subtraction', 'Scădere'),
        ('multiplication', 'Înmulțire'),
        ('division', 'Împărțire'),
        ('mixed', 'Combinat'),
    ]

    title = models.CharField(max_length=200, verbose_name="Titlu")
    description = models.TextField(blank=True, verbose_name="Descriere")

    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, verbose_name="Dificultate")
    operation_type = models.CharField(max_length=20, choices=OPERATION_CHOICES, verbose_name="Tip Operație")

    # Setări exercițiu
    number_count = models.IntegerField(default=5, verbose_name="Număr de Probleme")
    time_limit_seconds = models.IntegerField(null=True, blank=True, verbose_name="Limită Timp (secunde)")

    # Configurare numere
    min_number = models.IntegerField(default=1, verbose_name="Număr Minim")
    max_number = models.IntegerField(default=100, verbose_name="Număr Maxim")

    # Sistem puncte
    points_per_correct = models.IntegerField(default=10, verbose_name="Puncte per Răspuns Corect")

    # Status
    is_active = models.BooleanField(default=True, verbose_name="Activ")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Exercițiu Soroban"
        verbose_name_plural = "Exerciții Soroban"
        ordering = ['difficulty', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"


class SorobanSession(models.Model):
    """
    Sesiune de practică soroban pentru un elev
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='soroban_sessions',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )
    exercise = models.ForeignKey(
        SorobanExercise,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sessions',
        verbose_name="Exercițiu"
    )

    # Performanță
    problems_attempted = models.IntegerField(default=0, verbose_name="Probleme Încercate")
    problems_correct = models.IntegerField(default=0, verbose_name="Răspunsuri Corecte")

    # Timp
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Start")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Data Finalizare")
    total_time_seconds = models.IntegerField(null=True, blank=True, verbose_name="Timp Total (secunde)")

    # Punctaj
    points_earned = models.IntegerField(default=0, verbose_name="Puncte Câștigate")

    # Detalii răspunsuri (JSON)
    # Structură: [{"problem": "5+3", "answer": 8, "correct": true, "time": 12}, ...]
    answers_detail = models.JSONField(default=list, blank=True, verbose_name="Detalii Răspunsuri")

    class Meta:
        verbose_name = "Sesiune Soroban"
        verbose_name_plural = "Sesiuni Soroban"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.exercise.title if self.exercise else 'Practică Liberă'}"

    def calculate_accuracy(self):
        """Calculează procentul de acuratețe"""
        if self.problems_attempted == 0:
            return 0
        return round((self.problems_correct / self.problems_attempted) * 100, 2)

    def mark_completed(self):
        """Marchează sesiunea ca finalizată"""
        if not self.completed_at:
            self.completed_at = timezone.now()
            delta = self.completed_at - self.started_at
            self.total_time_seconds = int(delta.total_seconds())
            self.save()


class SorobanProgress(models.Model):
    """
    Progres general la soroban pentru un elev
    """
    student = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='soroban_progress',
        limit_choices_to={'role': 'student'},
        verbose_name="Elev"
    )

    # Nivel curent
    current_level = models.IntegerField(default=1, verbose_name="Nivel Curent")

    # Statistici totale
    total_sessions = models.IntegerField(default=0, verbose_name="Total Sesiuni")
    total_problems_solved = models.IntegerField(default=0, verbose_name="Total Probleme Rezolvate")
    total_correct_answers = models.IntegerField(default=0, verbose_name="Total Răspunsuri Corecte")
    total_points = models.IntegerField(default=0, verbose_name="Total Puncte")

    # Recorduri
    best_accuracy = models.FloatField(default=0.0, verbose_name="Cea mai Bună Acuratețe (%)")
    fastest_problem_time = models.IntegerField(null=True, blank=True, verbose_name="Cel mai Rapid Timp (secunde)")

    # Achievement badges (JSON)
    # Exemplu: ["speed_demon", "accuracy_master", "persistent_learner"]
    achievements = models.JSONField(default=list, blank=True, verbose_name="Realizări")

    last_practice_date = models.DateField(null=True, blank=True, verbose_name="Ultima Dată Practică")

    class Meta:
        verbose_name = "Progres Soroban"
        verbose_name_plural = "Progres Soroban"

    def __str__(self):
        return f"Progres {self.student.get_full_name()} - Nivel {self.current_level}"

    def update_stats_from_session(self, session):
        """Actualizează statisticile bazate pe o sesiune nouă"""
        self.total_sessions += 1
        self.total_problems_solved += session.problems_attempted
        self.total_correct_answers += session.problems_correct
        self.total_points += session.points_earned

        # Actualizează recorduri
        accuracy = session.calculate_accuracy()
        if accuracy > self.best_accuracy:
            self.best_accuracy = accuracy

        self.last_practice_date = timezone.now().date()
        self.save()

        # Verifică level up
        self.check_level_up()

    def check_level_up(self):
        """Verifică dacă elevul trebuie să avanseze la nivel superior"""
        # Criterii pentru nivel up (exemplu)
        points_threshold = self.current_level * 500

        if self.total_points >= points_threshold:
            self.current_level += 1
            self.save()
            return True
        return False

    def get_overall_accuracy(self):
        """Calculează acuratețea generală"""
        if self.total_problems_solved == 0:
            return 0
        return round((self.total_correct_answers / self.total_problems_solved) * 100, 2)