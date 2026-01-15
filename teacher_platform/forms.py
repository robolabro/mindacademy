from django import forms
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import Group, GroupStudent
from accounts.models import User, StudentProfile
from courses.models import Course, Module, Location


class GroupForm(forms.ModelForm):
    """
    Formular pentru crearea și editarea grupelor de către profesor
    """
    class Meta:
        model = Group
        fields = [
            'name', 'course', 'module', 'location',
            'weekday', 'start_time', 'duration_minutes',
            'start_date', 'end_date', 'max_occurrences',
            'max_students', 'description', 'created_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Grupa Aritmetică Avansată'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'module': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'weekday': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '90'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_occurrences': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Opțional'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '8'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descriere opțională'}),
            'created_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher

        # Filtrează locațiile la cele ale profesorului
        if teacher and hasattr(teacher, 'teacher_profile'):
            self.fields['location'].queryset = teacher.teacher_profile.locations.all()

        # Permite selectarea modulului în funcție de curs
        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['module'].queryset = Module.objects.filter(course_id=course_id, is_active=True)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.course:
            self.fields['module'].queryset = Module.objects.filter(course=self.instance.course, is_active=True)


class StudentForm(forms.ModelForm):
    """
    Formular pentru crearea conturilor de elev de către profesor
    """
    # Câmpuri din User
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Prenume",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prenumele elevului'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nume",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numele de familie'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username unic pentru login'})
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Data Nașterii",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    parent_email = forms.EmailField(
        required=False,
        label="Email Părinte",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@parinte.ro'})
    )
    parent_phone = forms.CharField(
        max_length=15,
        required=False,
        label="Telefon Părinte",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0712345678'})
    )

    # Câmpuri din StudentProfile
    sex = forms.ChoiceField(
        choices=[('', '-- Selectează --')] + list(StudentProfile.SEX_CHOICES),
        required=False,
        label="Sex",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    avatar = forms.ChoiceField(
        choices=StudentProfile.AVATAR_CHOICES,
        required=True,
        label="Avatar",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    account_created_date = forms.DateField(
        required=True,
        label="Data Creare Cont",
        initial=timezone.now,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    school_name = forms.CharField(
        max_length=200,
        required=False,
        label="Școala",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numele școlii'})
    )
    grade = forms.CharField(
        max_length=50,
        required=False,
        label="Clasa",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Clasa a 3-a'})
    )

    # Câmp pentru grupă
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        required=False,
        label="Grupă",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Opțional: alege grupa în care să fie înscris elevul"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'date_of_birth', 'parent_email', 'parent_phone']

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher

        # Filtrează grupele la cele ale profesorului
        if teacher:
            self.fields['group'].queryset = Group.objects.filter(teacher=teacher, is_active=True)

    def clean_username(self):
        """Verifică dacă username-ul este unic"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Acest username este deja folosit. Te rog alege altul.')
        return username

    def save(self, commit=True):
        """Creează User și StudentProfile"""
        user = super().save(commit=False)
        user.role = 'student'

        # Generează o parolă temporară (username-ul elevului)
        user.password = make_password(self.cleaned_data['username'])
        user.must_change_password = True

        if commit:
            user.save()

            # Creează StudentProfile
            student_profile = StudentProfile.objects.create(
                user=user,
                sex=self.cleaned_data.get('sex', ''),
                avatar=self.cleaned_data['avatar'],
                account_created_date=self.cleaned_data['account_created_date'],
                school_name=self.cleaned_data.get('school_name', ''),
                grade=self.cleaned_data.get('grade', ''),
                teacher=self.teacher,
                location=self.teacher.teacher_profile.locations.first() if hasattr(self.teacher, 'teacher_profile') else None
            )

            # Adaugă elevul în grupă dacă a fost selectată
            group = self.cleaned_data.get('group')
            if group:
                GroupStudent.objects.create(
                    group=group,
                    student=user,
                    is_active=True
                )
                student_profile.group = group
                student_profile.save()

        return user


class EditStudentForm(forms.ModelForm):
    """
    Formular pentru editarea informațiilor elevului
    """
    # Câmpuri din User
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="Prenume",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nume",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Data Nașterii",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    parent_email = forms.EmailField(
        required=False,
        label="Email Părinte",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    parent_phone = forms.CharField(
        max_length=15,
        required=False,
        label="Telefon Părinte",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Câmpuri din StudentProfile
    sex = forms.ChoiceField(
        choices=[('', '-- Selectează --')] + list(StudentProfile.SEX_CHOICES),
        required=False,
        label="Sex",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    avatar = forms.ChoiceField(
        choices=StudentProfile.AVATAR_CHOICES,
        required=True,
        label="Avatar",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    school_name = forms.CharField(
        max_length=200,
        required=False,
        label="Școala",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    grade = forms.CharField(
        max_length=50,
        required=False,
        label="Clasa",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'date_of_birth', 'parent_email', 'parent_phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inițializează câmpurile din StudentProfile dacă există
        if self.instance.pk and hasattr(self.instance, 'student_profile'):
            profile = self.instance.student_profile
            self.fields['sex'].initial = profile.sex
            self.fields['avatar'].initial = profile.avatar
            self.fields['school_name'].initial = profile.school_name
            self.fields['grade'].initial = profile.grade

    def save(self, commit=True):
        """Salvează User și StudentProfile"""
        user = super().save(commit=commit)

        if commit and hasattr(user, 'student_profile'):
            profile = user.student_profile
            profile.sex = self.cleaned_data.get('sex', '')
            profile.avatar = self.cleaned_data['avatar']
            profile.school_name = self.cleaned_data.get('school_name', '')
            profile.grade = self.cleaned_data.get('grade', '')
            profile.save()

        return user


class LessonForm(forms.ModelForm):
    """
    Formular pentru crearea lecțiilor (recurente sau ad-hoc)
    """
    LESSON_TYPE_CHOICES = [
        ('single', 'Lecție unică (ad-hoc)'),
        ('recurring', 'Lecții recurente (serie)'),
    ]

    lesson_type = forms.ChoiceField(
        choices=LESSON_TYPE_CHOICES,
        initial='single',
        label="Tip Lecție",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    # Pentru lecții recurente
    recurrence_count = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=52,
        initial=8,
        label="Număr de lecții",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 8 (pentru 8 săptămâni)'
        }),
        help_text="Câte lecții să fie create automat (săptămânal)"
    )

    recurrence_weekday = forms.ChoiceField(
        required=False,
        choices=[
            (0, 'Luni'),
            (1, 'Marți'),
            (2, 'Miercuri'),
            (3, 'Joi'),
            (4, 'Vineri'),
            (5, 'Sâmbătă'),
            (6, 'Duminică'),
        ],
        label="Zi săptămână",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="În ce zi a săptămânii să se repete lecțiile"
    )

    class Meta:
        model = Lesson
        fields = ['group', 'lesson_template', 'date', 'start_time', 'end_time',
                  'topic', 'description', 'homework', 'teacher_notes']
        widgets = {
            'group': forms.Select(attrs={'class': 'form-select'}),
            'lesson_template': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Introducere în fracții'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'homework': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'teacher_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'group': 'Grupă',
            'lesson_template': 'Template Lecție (opțional)',
            'date': 'Data primei lecții',
            'start_time': 'Ora de început',
            'end_time': 'Ora de sfârșit',
            'topic': 'Subiect',
            'description': 'Descriere',
            'homework': 'Temă pentru acasă',
            'teacher_notes': 'Notițe profesor',
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher

        # Filtrează grupele la cele ale profesorului
        if teacher:
            self.fields['group'].queryset = Group.objects.filter(
                teacher=teacher,
                is_active=True
            ).select_related('course', 'module')

            # Filtrează template-urile la cele din cursurile profesorului
            from courses.models import LessonTemplate
            teacher_courses = Group.objects.filter(
                teacher=teacher
            ).values_list('course_id', flat=True).distinct()

            self.fields['lesson_template'].queryset = LessonTemplate.objects.filter(
                module__course_id__in=teacher_courses
            ).select_related('module', 'module__course')

        # Fă template-ul opțional
        self.fields['lesson_template'].required = False
        self.fields['end_time'].required = False

    def clean(self):
        cleaned_data = super().clean()
        lesson_type = cleaned_data.get('lesson_type')

        if lesson_type == 'recurring':
            if not cleaned_data.get('recurrence_count'):
                self.add_error('recurrence_count', 'Te rog specifică numărul de lecții pentru seria recurentă.')
            if not cleaned_data.get('recurrence_weekday'):
                self.add_error('recurrence_weekday', 'Te rog selectează ziua săptămânii.')

        # Verifică că start_time < end_time
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'Ora de sfârșit trebuie să fie după ora de început.')

        return cleaned_data
