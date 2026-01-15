from django.urls import path
from . import views

app_name = 'teacher_platform'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),

    # Grupe
    path('grupe/', views.groups_list, name='groups_list'),
    path('grupe/adauga/', views.group_add, name='group_add'),
    path('grupe/<int:group_id>/', views.group_detail, name='group_detail'),
    path('grupe/<int:group_id>/editeaza/', views.group_edit, name='group_edit'),

    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),

    # Studenți
    path('studenti/', views.students_list, name='students_list'),
    path('studenti/adauga/', views.student_add, name='student_add'),
    path('studenti/<int:student_id>/', views.student_detail, name='student_detail'),
    path('studenti/<int:student_id>/editeaza/', views.student_edit, name='student_edit'),

    # Lecții
    path('lectii/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),

    # Teme
    path('teme/', views.assignments_list, name='assignments_list'),
    path('teme/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),

    # API
    path('api/get-modules/', views.get_modules_for_course, name='get_modules_for_course'),
]
