from django.contrib import admin
from .models import Location, AgeGroup, Course, Testimonial, DemoLesson, ContactMessage


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