from django.contrib import admin
from .models import Group, GroupStudent, Lesson, Attendance, Assignment, AssignmentSubmission, LessonNote


class GroupStudentInline(admin.TabularInline):
    """Inline pentru elevi în grupă"""
    model = GroupStudent
    extra = 0
    fields = ['student', 'enrolled_date', 'is_active', 'lessons_attended', 'lessons_missed']
    readonly_fields = ['enrolled_date']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'teacher', 'course', 'module', 'location', 'weekday', 'start_time', 'is_active']
    list_filter = ['is_active', 'course', 'module', 'location', 'weekday', 'teacher']
    search_fields = ['name', 'code', 'teacher__first_name', 'teacher__last_name', 'course__title']
    readonly_fields = ['code', 'created_at', 'updated_at']
    inlines = [GroupStudentInline]

    fieldsets = (
        ('Informații Principale', {
            'fields': ('name', 'code', 'teacher', 'course', 'module', 'location')
        }),
        ('Program', {
            'fields': ('weekday', 'start_time', 'duration_minutes', 'start_date', 'end_date', 'max_occurrences')
        }),
        ('Detalii', {
            'fields': ('max_students', 'description', 'created_date')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Codul este readonly întotdeauna"""
        if obj:  # Editare
            return self.readonly_fields
        return self.readonly_fields


@admin.register(GroupStudent)
class GroupStudentAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'enrolled_date', 'is_active', 'lessons_attended', 'lessons_missed', 'get_attendance_rate']
    list_filter = ['is_active', 'group', 'enrolled_date']
    search_fields = ['student__first_name', 'student__last_name', 'group__name']
    readonly_fields = ['enrolled_date', 'get_attendance_rate']

    fieldsets = (
        ('Elev și Grupă', {
            'fields': ('student', 'group', 'enrolled_date', 'is_active')
        }),
        ('Progres', {
            'fields': ('lessons_attended', 'lessons_missed', 'get_attendance_rate')
        }),
    )

    def get_attendance_rate(self, obj):
        """Afișează procentul de prezență"""
        return f"{obj.get_attendance_rate()}%"

    get_attendance_rate.short_description = 'Rată Prezență'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['group', 'lesson_template', 'date', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'date', 'group__course', 'group']
    search_fields = ['group__name', 'topic', 'lesson_template__name']
    date_hierarchy = 'date'

    fieldsets = (
        ('Grupă și Template', {
            'fields': ('group', 'lesson_template')
        }),
        ('Programare', {
            'fields': ('date', 'start_time', 'end_time', 'status')
        }),
        ('Conținut', {
            'fields': ('topic', 'description', 'homework', 'materials')
        }),
        ('Notițe', {
            'fields': ('teacher_notes',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_present', 'performance_rating', 'created_at']
    list_filter = ['is_present', 'performance_rating', 'lesson__date', 'lesson__group']
    search_fields = ['student__first_name', 'student__last_name', 'lesson__group__name']
    date_hierarchy = 'lesson__date'

    fieldsets = (
        ('Lecție și Elev', {
            'fields': ('lesson', 'student')
        }),
        ('Prezență', {
            'fields': ('is_present', 'performance_rating', 'notes')
        }),
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'lesson', 'due_date', 'max_points']
    list_filter = ['group__course', 'group', 'due_date']
    search_fields = ['title', 'description', 'group__name']
    date_hierarchy = 'due_date'

    fieldsets = (
        ('Informații Principale', {
            'fields': ('title', 'description', 'group', 'lesson')
        }),
        ('Termene și Punctaj', {
            'fields': ('due_date', 'max_points')
        }),
        ('Fișiere', {
            'fields': ('attachment',)
        }),
    )


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'submitted_at', 'is_graded', 'score']
    list_filter = ['is_graded', 'submitted_at', 'assignment__group']
    search_fields = ['student__first_name', 'student__last_name', 'assignment__title']
    readonly_fields = ['submitted_at']
    date_hierarchy = 'submitted_at'

    fieldsets = (
        ('Temă și Elev', {
            'fields': ('assignment', 'student')
        }),
        ('Predare', {
            'fields': ('text_response', 'file_response', 'submitted_at')
        }),
        ('Evaluare', {
            'fields': ('is_graded', 'score', 'feedback', 'graded_at')
        }),
    )


@admin.register(LessonNote)
class LessonNoteAdmin(admin.ModelAdmin):
    list_display = ['lesson_template', 'group', 'teacher', 'created_at']
    list_filter = ['group__course', 'group__module', 'teacher', 'created_at']
    search_fields = ['lesson_template__name', 'group__name', 'teacher__first_name', 'teacher__last_name', 'notes']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Lecție și Grupă', {
            'fields': ('lesson_template', 'group', 'teacher')
        }),
        ('Notițe', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
