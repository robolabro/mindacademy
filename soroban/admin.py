from django.contrib import admin
from .models import SorobanExercise, SorobanSession, SorobanProgress


@admin.register(SorobanExercise)
class SorobanExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'operation_type', 'number_count', 'points_per_correct', 'is_active')
    list_filter = ('difficulty', 'operation_type', 'is_active')
    search_fields = ('title', 'description')

    fieldsets = (
        ('Informații Generale', {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Configurare Exercițiu', {
            'fields': ('difficulty', 'operation_type', 'number_count', 'time_limit_seconds')
        }),
        ('Configurare Numere', {
            'fields': ('min_number', 'max_number')
        }),
        ('Punctaj', {
            'fields': ('points_per_correct',)
        }),
    )


@admin.register(SorobanSession)
class SorobanSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'started_at', 'completed_at', 'problems_attempted', 'problems_correct',
                    'points_earned', 'get_accuracy')
    list_filter = ('started_at', 'completed_at')
    search_fields = ('student__first_name', 'student__last_name', 'student__email')
    readonly_fields = ('started_at', 'completed_at', 'total_time_seconds', 'answers_detail')
    date_hierarchy = 'started_at'

    fieldsets = (
        ('Sesiune', {
            'fields': ('student', 'exercise', 'started_at', 'completed_at', 'total_time_seconds')
        }),
        ('Performanță', {
            'fields': ('problems_attempted', 'problems_correct', 'points_earned')
        }),
        ('Detalii Răspunsuri', {
            'fields': ('answers_detail',),
            'classes': ('collapse',)
        }),
    )

    def get_accuracy(self, obj):
        return f"{obj.calculate_accuracy()}%"

    get_accuracy.short_description = 'Acuratețe'


@admin.register(SorobanProgress)
class SorobanProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'current_level', 'total_sessions', 'total_problems_solved', 'total_correct_answers',
                    'get_overall_accuracy', 'total_points', 'last_practice_date')
    list_filter = ('current_level', 'last_practice_date')
    search_fields = ('student__first_name', 'student__last_name', 'student__email')
    readonly_fields = ('total_sessions', 'total_problems_solved', 'total_correct_answers', 'total_points',
                       'best_accuracy', 'fastest_problem_time', 'achievements', 'last_practice_date')

    fieldsets = (
        ('Elev', {
            'fields': ('student',)
        }),
        ('Nivel', {
            'fields': ('current_level',)
        }),
        ('Statistici Totale', {
            'fields': ('total_sessions', 'total_problems_solved', 'total_correct_answers', 'total_points')
        }),
        ('Recorduri', {
            'fields': ('best_accuracy', 'fastest_problem_time')
        }),
        ('Realizări', {
            'fields': ('achievements',),
            'classes': ('collapse',)
        }),
        ('Ultima Activitate', {
            'fields': ('last_practice_date',)
        }),
    )

    def get_overall_accuracy(self, obj):
        return f"{obj.get_overall_accuracy()}%"

    get_overall_accuracy.short_description = 'Acuratețe Generală'

    actions = ['reset_progress']

    def reset_progress(self, request, queryset):
        """Resetează progresul selectat"""
        for progress in queryset:
            progress.current_level = 1
            progress.total_sessions = 0
            progress.total_problems_solved = 0
            progress.total_correct_answers = 0
            progress.total_points = 0
            progress.best_accuracy = 0.0
            progress.fastest_problem_time = None
            progress.achievements = []
            progress.save()

        self.message_user(request, f'{queryset.count()} progrese resetate.')

    reset_progress.short_description = "Resetează progresul selectat"