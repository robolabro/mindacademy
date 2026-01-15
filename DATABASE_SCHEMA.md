# Schema Bază de Date - Platformă Educațională Interactivă

## Ierarhie și Relații

```
Admin
  ├── Locations (Centre)
  ├── Teachers (alocați la Location-uri)
  ├── Courses (Cursuri - ex: Aritmetică Mentală)
  │   └── Modules (Module)
  │       └── Lessons (Lecții preset cu PDF-uri)
  ├── Students (opțional, creare directă)
  └── Groups (opțional, vizibilitate)

Teacher Dashboard
  ├── Students (creare și gestionare)
  ├── Groups (creare și gestionare)
  │   ├── Alocare Module (cu lecții incluse)
  │   ├── Cod automat: CURS-MODUL-NR
  │   └── Lesson Notes (notițe per lecție)
  └── Calendar (programare lecții recurente)
      └── Schedule View (orar filtrat după grupele proprii)
```

## Modele Existente (A Modifica)

### 1. TeacherProfile (accounts/models.py)
**Adăugare:**
- `locations = ManyToManyField(Location)` - profesor alocat la multiple centre

### 2. StudentProfile (accounts/models.py)
**Adăugare:**
- `sex = CharField(choices=[('M', 'Băiat'), ('F', 'Fată')])`
- `avatar = CharField(choices=[('boy', 'Avatar Băiat'), ('girl', 'Avatar Fată')])`
- `group = ForeignKey('teacher_platform.Group', null=True, blank=True)`
- `location = ForeignKey('courses.Location')`
- `teacher = ForeignKey(User, related_name='students_managed')`
- `account_created_date = DateField(editable=True)` - data creare cont editabilă

### 3. Group (teacher_platform/models.py)
**Adăugare:**
- `course = ForeignKey('courses.Course')`
- `module = ForeignKey('courses.Module')`
- `location = ForeignKey('courses.Location')`
- `code = CharField(unique=True, editable=False)` - format: CURS-MODUL-001
- `created_date = DateField(editable=True)`
- `teacher = ForeignKey(User)` - (verifică dacă există deja)

**Metodă:**
- `generate_code()` - auto-generează cod la salvare

## Modele Noi (A Crea)

### 4. Module (courses/models.py)
```python
class Module(models.Model):
    course = ForeignKey(Course, related_name='modules')
    name = CharField(max_length=200)
    description = TextField()
    order = PositiveIntegerField(default=0)  # pentru sortare
    color = CharField(max_length=7, default='#4A90E2')  # hex color pentru calendar
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
```

### 5. LessonTemplate (courses/models.py)
**Notă:** Redenumim/creăm model separat pentru lecții template (diferit de Lesson care e pentru lecții programate)
```python
class LessonTemplate(models.Model):
    module = ForeignKey(Module, related_name='lessons')
    name = CharField(max_length=200)
    description = TextField()
    lesson_steps = TextField()  # pași lecție (sau JSONField pentru structurare)
    lesson_plan_file = FileField(upload_to='lesson_plans/', blank=True)  # PDF ne-descărcabil
    order = PositiveIntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
```

### 6. LessonNote (teacher_platform/models.py)
```python
class LessonNote(models.Model):
    lesson_template = ForeignKey('courses.LessonTemplate', related_name='teacher_notes')
    group = ForeignKey(Group, related_name='lesson_notes')
    teacher = ForeignKey(User, related_name='lesson_notes')
    notes = TextField()
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['lesson_template', 'group', 'teacher']
```

### 7. CalendarLesson (teacher_platform/models.py)
**Notă:** Model pentru lecții programate recurent în calendar
```python
class CalendarLesson(models.Model):
    RECURRENCE_CHOICES = [
        ('weekly', 'Săptămânal'),
        ('biweekly', 'La două săptămâni'),
    ]

    group = ForeignKey(Group, related_name='calendar_lessons')
    lesson_template = ForeignKey('courses.LessonTemplate', null=True, blank=True)

    # Programare
    day_of_week = IntegerField(choices=[(0, 'Luni'), (1, 'Marți'), ...])  # 0-6
    start_time = TimeField()
    end_time = TimeField()
    start_date = DateField()  # data de începere
    recurrence = CharField(max_length=20, choices=RECURRENCE_CHOICES, default='weekly')

    # Pentru generare lecții
    end_date = DateField(null=True, blank=True)  # opțional
    max_occurrences = PositiveIntegerField(null=True, blank=True)  # opțional

    created_at = DateTimeField(auto_now_add=True)

    def generate_lesson_instances(self):
        """Generează instanțe Lesson pentru recurență"""
        pass
```

## Admin Configuration

### Admin - Capabilities:
1. **LocationAdmin** - Gestionare centre/locații
2. **CourseAdmin** - Gestionare cursuri
3. **ModuleAdmin** - Creare module cu:
   - Color picker pentru culoare calendar
   - Inline pentru LessonTemplate (adăugare lecții direct)
4. **LessonTemplateAdmin** - Gestionare lecții template cu upload PDF
5. **TeacherProfileAdmin** - Creare profesori cu:
   - Alocare multiple locații (filter_horizontal)
6. **StudentProfileAdmin** - Creare elevi cu toate câmpurile
7. **GroupAdmin** - Vizibilitate grupe (cod auto-generat vizibil readonly)

### Teacher Dashboard - Capabilities:
1. **Student Management:**
   - Creare cont elev (formular cu: nume, dată naștere, sex, avatar, grupă, modul)
   - Vizualizare elevi proprii
   - Editare informații elevi

2. **Group Management:**
   - Creare grupă (selectare curs, modul, locație)
   - Cod auto-generat vizibil
   - Vizualizare lecții din modul selectat
   - Adăugare notițe per lecție

3. **Calendar:**
   - Programare lecții recurente (zi, oră, dată început, recurență)
   - Vizualizare orar personal (doar grupele proprii)
   - Color-coding după modul (culoarea din admin)

## Fluxuri de Lucru

### Flux 1: Admin creează structura
1. Admin creează Location (Centre)
2. Admin creează Course (ex: Aritmetică Mentală)
3. Admin creează Module pentru curs (cu culori pentru calendar)
4. Admin creează LessonTemplate pentru fiecare modul (cu PDF-uri)
5. Admin creează Teacher și alocă la Location-uri

### Flux 2: Teacher creează grupă și elevi
1. Teacher se autentifică
2. Teacher creează Group:
   - Selectează curs și modul
   - Sistem generează cod automat
   - Data creare editabilă
3. Teacher creează Student:
   - Completează informații personale
   - Selectează avatar
   - Alocă la grupă
   - Location și Teacher pre-completate
4. Teacher vede lecțiile modulului și poate adăuga notițe

### Flux 3: Teacher programează lecții
1. Teacher selectează grupa
2. Teacher setează: zi săptămână, interval orar, dată început, recurență
3. Sistem generează lecții în calendar
4. Teacher vede orarul cu color-coding după modul

## Reguli de Business

1. **Cod Grupă:** Format `{CURS_SLUG}-{MODUL_ID}-{AUTONUMBER}` (ex: `ARITMETICA-12-001`)
2. **Avatar:** 2 opțiuni fixe (băiat.png, fată.png)
3. **Elev:** Poate fi în o singură grupă
4. **Profesor:** Poate fi la multiple locații
5. **Modul:** NU apare în HTML public (doar în admin și dashboard profesor)
6. **PDF Lecție:** Fișier ne-descărcabil (view only în browser)
7. **Calendar:** Recurență săptămânală cu color-coding după culoarea modulului
