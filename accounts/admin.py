from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, TeacherProfile, StudentProfile


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informații Personale', {'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'avatar')}),
        ('Rol și Permisiuni',
         {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Informații Părinte/Copil', {'fields': ('parent', 'parent_email', 'parent_phone')}),
        ('Securitate', {'fields': ('must_change_password', 'last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

    actions = ['create_teacher_profiles', 'create_student_profiles']

    def create_teacher_profiles(self, request, queryset):
        """Creează profile de profesor pentru utilizatorii selectați"""
        count = 0
        for user in queryset.filter(role='teacher'):
            TeacherProfile.objects.get_or_create(user=user)
            count += 1
        self.message_user(request, f'{count} profile de profesor create.')

    create_teacher_profiles.short_description = "Creează profile profesor"

    def create_student_profiles(self, request, queryset):
        """Creează profile de elev pentru utilizatorii selectați"""
        count = 0
        for user in queryset.filter(role='student'):
            StudentProfile.objects.get_or_create(user=user)
            count += 1
        self.message_user(request, f'{count} profile de elev create.')

    create_student_profiles.short_description = "Creează profile elev"


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'get_locations', 'is_active')
    list_filter = ('is_active', 'experience_years', 'locations')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'specialization')
    filter_horizontal = ('locations',)

    fieldsets = (
        ('Utilizator', {'fields': ('user',)}),
        ('Detalii Profesionale', {'fields': ('bio', 'specialization', 'experience_years')}),
        ('Alocare Locații', {
            'fields': ('locations',),
            'description': 'Selectează locațiile/centrele la care predă acest profesor'
        }),
        ('Status', {'fields': ('is_active',)}),
    )

    def get_locations(self, obj):
        """Afișează locațiile profesorului"""
        return ", ".join([loc.name for loc in obj.locations.all()]) or "-"

    get_locations.short_description = 'Locații'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'sex', 'avatar', 'group', 'location', 'teacher', 'account_created_date', 'total_lessons_attended')
    list_filter = ('sex', 'avatar', 'group', 'location', 'teacher', 'soroban_level')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'school_name')

    fieldsets = (
        ('Utilizator', {'fields': ('user',)}),
        ('Informații Personale', {
            'fields': ('sex', 'avatar', 'account_created_date'),
            'description': 'Informații de bază ale elevului'
        }),
        ('Alocare', {
            'fields': ('location', 'teacher', 'group'),
            'description': 'Locație, profesor coordonator și grupă'
        }),
        ('Informații Școlare', {'fields': ('school_name', 'grade')}),
        ('Progres', {'fields': ('total_lessons_attended', 'total_points', 'soroban_level')}),
    )

    readonly_fields = ('total_lessons_attended', 'total_points')
