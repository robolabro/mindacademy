from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Location(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nume Locație")
    address = models.TextField(verbose_name="Adresă")
    google_maps_embed = models.TextField(verbose_name="Google Maps Embed Code", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    is_online = models.BooleanField(default=False, verbose_name="Lecții Online")

    class Meta:
        verbose_name = "Locație"
        verbose_name_plural = "Locații"
        ordering = ['name']

    def __str__(self):
        return self.name


class AgeGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name="Grupă de Vârstă")
    min_age = models.IntegerField(validators=[MinValueValidator(3)], verbose_name="Vârstă Minimă")
    max_age = models.IntegerField(validators=[MaxValueValidator(18)], verbose_name="Vârstă Maximă")

    class Meta:
        verbose_name = "Grupă de Vârstă"
        verbose_name_plural = "Grupe de Vârstă"
        ordering = ['min_age']

    def __str__(self):
        return f"{self.name} ({self.min_age}-{self.max_age} ani)"


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titlu Curs")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Descriere")
    age_group = models.ForeignKey(AgeGroup, on_delete=models.SET_NULL, null=True, verbose_name="Grupă de Vârstă")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Preț (RON)")
    frequency = models.CharField(max_length=200, verbose_name="Frecvență")
    group_size = models.IntegerField(verbose_name="Număr Copii în Grupă")
    pdf_presentation = models.FileField(upload_to='presentations/', blank=True, verbose_name="Prezentare PDF")
    projects_link = models.URLField(blank=True, verbose_name="Link Proiecte Copii")
    image = models.ImageField(upload_to='courses/', blank=True, verbose_name="Imagine Curs")
    video_url = models.URLField(blank=True, verbose_name="URL Video")
    locations = models.ManyToManyField(Location, verbose_name="Locații")
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    featured = models.BooleanField(default=False, verbose_name="Recomandat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curs"
        verbose_name_plural = "Cursuri"
        ordering = ['-featured', 'title']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='testimonials', verbose_name="Curs")
    parent_name = models.CharField(max_length=200, verbose_name="Nume Părinte")
    child_name = models.CharField(max_length=200, verbose_name="Nume Copil", blank=True)
    text = models.TextField(verbose_name="Text Testimonial")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Rating")
    is_approved = models.BooleanField(default=False, verbose_name="Aprobat")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimoniale"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.parent_name} - {self.course.title}"


class DemoLesson(models.Model):
    parent_name = models.CharField(max_length=200, verbose_name="Nume Părinte")
    parent_email = models.EmailField(verbose_name="Email Părinte")
    parent_phone = models.CharField(max_length=15, verbose_name="Telefon Părinte")
    child_age = models.IntegerField(validators=[MinValueValidator(3), MaxValueValidator(18)],
                                    verbose_name="Vârsta Copilului")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, verbose_name="Curs")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, verbose_name="Locație")
    terms_accepted = models.BooleanField(default=False, verbose_name="Termeni Acceptați")
    created_at = models.DateTimeField(auto_now_add=True)
    contacted = models.BooleanField(default=False, verbose_name="Contactat")

    class Meta:
        verbose_name = "Lecție Demo"
        verbose_name_plural = "Lecții Demo"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.parent_name} - {self.course.title if self.course else 'N/A'}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nume")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=15, verbose_name="Telefon")
    message = models.TextField(verbose_name="Mesaj")
    created_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False, verbose_name="Răspuns")

    class Meta:
        verbose_name = "Mesaj Contact"
        verbose_name_plural = "Mesaje Contact"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d.%m.%Y')}"


class Module(models.Model):
    """
    Modul dintr-un curs (ex: Modul 1, Modul 2)
    Modulele sunt create în admin și nu apar în site-ul public
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name="Curs"
    )
    name = models.CharField(max_length=200, verbose_name="Nume Modul")
    description = models.TextField(blank=True, verbose_name="Descriere")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordine")

    # Culoare pentru calendar (hex color)
    color = models.CharField(
        max_length=7,
        default='#4A90E2',
        verbose_name="Culoare Calendar",
        help_text="Culoare în format hex (ex: #4A90E2)"
    )

    is_active = models.BooleanField(default=True, verbose_name="Activ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modul"
        verbose_name_plural = "Module"
        ordering = ['course', 'order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.name}"


class LessonTemplate(models.Model):
    """
    Șablon de lecție din modul (lecții preset)
    Acestea sunt create în admin și servesc ca bază pentru lecțiile din grupe
    """
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lesson_templates',
        verbose_name="Modul"
    )
    name = models.CharField(max_length=200, verbose_name="Nume Lecție")
    description = models.TextField(blank=True, verbose_name="Descriere")

    # Pași lecție (poate fi text structurat sau JSON)
    lesson_steps = models.TextField(
        blank=True,
        verbose_name="Pași Lecție",
        help_text="Pașii necesari pentru desfășurarea lecției"
    )

    # Plan de lecție (PDF sau alt format, ne-descărcabil)
    lesson_plan_file = models.FileField(
        upload_to='lesson_plans/',
        blank=True,
        null=True,
        verbose_name="Plan de Lecție",
        help_text="PDF sau document cu planul lecției (nu poate fi descărcat)"
    )

    order = models.PositiveIntegerField(default=0, verbose_name="Ordine")
    is_active = models.BooleanField(default=True, verbose_name="Activ")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Șablon Lecție"
        verbose_name_plural = "Șabloane Lecții"
        ordering = ['module', 'order']
        unique_together = ['module', 'order']

    def __str__(self):
        return f"{self.module.name} - {self.name}"