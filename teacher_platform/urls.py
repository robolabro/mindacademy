from django.urls import path
from . import views

app_name = 'teacher_platform'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),

    # Grupe
    path('grupe/', views.groups_list, name='groups_list'),
    path('grupe/<int:group_id>/', views.group_detail, name='group_detail'),

    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),

    # Studenți
    path('studenti/', views.students_list, name='students_list'),
    path('studenti/<int:student_id>/', views.student_detail, name='student_detail'),

    # Lecții
    path('lectii/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),

    # Teme
    path('teme/', views.assignments_list, name='assignments_list'),
    path('teme/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
]
