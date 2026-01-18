from django.contrib import admin
from .models import Location, AgeGroup, Course, Testimonial, DemoLesson, ContactMessage, Module, LessonTemplate


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
    list_display = ['title', 'age_group', 'price', 'featured', 'is_active']
    list_filter = ['featured', 'is_active', 'age_group']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['locations']


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


@admin.register(LessonTemplate)
class LessonTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'module', 'order', 'is_active']
    list_filter = ['is_active', 'module__course', 'module']
    search_fields = ['name', 'description', 'module__name']
    ordering = ['module', 'order']

    fieldsets = (
        ('Informații Principale', {
            'fields': ('module', 'name', 'description', 'order')
        }),
        ('Conținut Lecție', {
            'fields': ('lesson_steps', 'lesson_plan_file'),
            'description': 'Pașii lecției și planul de lecție (PDF/document)'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )