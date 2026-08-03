from django.contrib import admin
from .models import Location, AgeGroup, Course, Testimonial, DemoLesson, ContactMessage, Module, LessonTemplate, LessonMilestone


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'is_online', 'is_active']
    list_filter = ['is_active', 'is_online']
    search_fields = ['name', 'address']


@admin.register(AgeGroup)
class AgeGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_age', 'max_age']
    ordering = ['min_age']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    change_list_template = 'admin/courses/course/change_list.html'
    list_display = ['title', 'age_group', 'price', 'featured', 'is_active']
    list_filter = ['featured', 'is_active', 'age_group']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['locations']

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('sync-curriculum/', self.admin_site.admin_view(self.sync_curriculum_view),
                 name='courses_sync_curriculum'),
        ]
        return custom + urls

    def sync_curriculum_view(self, request):
        """Buton admin: sincronizează curriculumul din Airtable (doar staff)."""
        from django.conf import settings
        from django.contrib import messages
        from django.shortcuts import redirect
        from courses.curriculum_sync import fetch_airtable_records, upsert_curriculum

        token = getattr(settings, 'AIRTABLE_TOKEN', '')
        base_id = getattr(settings, 'AIRTABLE_BASE_ID', '')
        if not token or not base_id:
            messages.error(request, 'Lipsesc AIRTABLE_TOKEN / AIRTABLE_BASE_ID din configurare.')
            return redirect('admin:courses_course_changelist')
        try:
            courses, modules, lessons = fetch_airtable_records(token, base_id)
            stats = upsert_curriculum(courses, modules, lessons)
        except ImportError:
            messages.error(request, 'pyairtable nu este instalat (pip install pyairtable).')
            return redirect('admin:courses_course_changelist')
        except Exception as exc:
            messages.error(request, f'Eroare la sincronizare: {exc}')
            return redirect('admin:courses_course_changelist')

        messages.success(
            request,
            f"Curriculum sincronizat din Airtable — "
            f"Cursuri: +{stats['courses'][0]}/~{stats['courses'][1]}, "
            f"Module: +{stats['modules'][0]}/~{stats['modules'][1]}, "
            f"Lecții: +{stats['lessons'][0]}/~{stats['lessons'][1]}.")
        return redirect('admin:courses_course_changelist')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['parent_name', 'course', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'course']
    search_fields = ['parent_name', 'text']
    actions = ['approve_testimonials']

    def approve_testimonials(self, request, queryset):
        queryset.update(is_approved=True)

    approve_testimonials.short_description = "Aprobă testimoniale selectate"


@admin.register(DemoLesson)
class DemoLessonAdmin(admin.ModelAdmin):
    list_display = ['parent_name', 'parent_email', 'course', 'location', 'child_age', 'contacted', 'created_at']
    list_filter = ['contacted', 'course', 'location', 'created_at']
    search_fields = ['parent_name', 'parent_email']
    actions = ['mark_contacted']

    def mark_contacted(self, request, queryset):
        queryset.update(contacted=True)

    mark_contacted.short_description = "Marchează ca și contactat"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'responded', 'created_at']
    list_filter = ['responded', 'created_at']
    search_fields = ['name', 'email', 'message']
    actions = ['mark_responded']

    def mark_responded(self, request, queryset):
        queryset.update(responded=True)

    mark_responded.short_description = "Marchează ca și răspuns"


class LessonTemplateInline(admin.TabularInline):
    """Inline pentru lecții template în ModuleAdmin"""
    model = LessonTemplate
    extra = 1
    fields = ['order', 'name', 'description', 'lesson_steps', 'lesson_plan_file', 'is_active']
    ordering = ['order']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'order', 'color_badge', 'is_active']
    list_filter = ['is_active', 'course']
    search_fields = ['name', 'course__title']
    ordering = ['course', 'order']
    inlines = [LessonTemplateInline]

    fieldsets = (
        ('Informații Principale', {
            'fields': ('course', 'name', 'description', 'order')
        }),
        ('Setări Calendar', {
            'fields': ('color',),
            'description': 'Culoarea în care va apărea acest modul în calendar (format hex, ex: #4A90E2)'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def color_badge(self, obj):
        """Afișează o pastilă colorată cu culoarea modulului"""
        return f'<span style="background-color: {obj.color}; padding: 5px 15px; border-radius: 3px; color: white;">{obj.color}</span>'

    color_badge.short_description = 'Culoare Calendar'
    color_badge.allow_tags = True


class LessonMilestoneInline(admin.TabularInline):
    """Milestones (structura lecției) definite de admin per lecție."""
    model = LessonMilestone
    extra = 3
    fields = ['order', 'title', 'is_active']
    ordering = ['order']


@admin.register(LessonTemplate)
class LessonTemplateAdmin(admin.ModelAdmin):
    inlines = [LessonMilestoneInline]
    list_display = ['name', 'module', 'order', 'milestone_count', 'is_active']

    def milestone_count(self, obj):
        return obj.milestones.count()
    milestone_count.short_description = 'Milestones'
    list_filter = ['is_active', 'module__course', 'module']
    search_fields = ['name', 'description', 'module__name']
    ordering = ['module', 'order']

    readonly_fields = ['airtable_id']

    fieldsets = (
        ('Informații Principale', {
            'fields': ('module', 'name', 'description', 'order')
        }),
        ('Conținut Lecție', {
            'fields': ('objectives', 'materials', 'lesson_steps', 'lesson_plan_file'),
            'description': 'Obiective, materiale elevi, pașii lecției și planul de lecție (PDF/document)'
        }),
        ('Status & Sincronizare', {
            'fields': ('is_active', 'airtable_id'),
            'description': 'airtable_id se completează automat la sincronizarea din Airtable.'
        }),
    )