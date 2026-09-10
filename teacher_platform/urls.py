from django.urls import path
from . import views

app_name = 'teacher_platform'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),

    # Profil profesor
    path('profil/', views.teacher_profile, name='teacher_profile'),

    # Grupe
    path('grupe/', views.groups_list, name='groups_list'),
    path('grupe/adauga/', views.group_add, name='group_add'),
    path('grupe/<int:group_id>/', views.group_detail, name='group_detail'),
    path('grupe/<int:group_id>/editeaza/', views.group_edit, name='group_edit'),
    path('grupe/<int:group_id>/teme/', views.group_homework, name='group_homework'),
    path('grupe/<int:group_id>/live/', views.group_live, name='group_live'),
    path('grupe/<int:group_id>/curriculum/', views.group_curriculum, name='group_curriculum'),
    path('grupe/<int:group_id>/milestone/', views.milestone_toggle, name='milestone_toggle'),
    path('grupe/<int:group_id>/performanta/', views.group_performance, name='group_performance'),

    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),

    # Studenți
    path('studenti/', views.students_list, name='students_list'),
    path('studenti/adauga/', views.student_add, name='student_add'),
    path('studenti/<int:student_id>/', views.student_detail, name='student_detail'),
    path('studenti/<int:student_id>/editeaza/', views.student_edit, name='student_edit'),
    path('studenti/<int:student_id>/reseteaza-parola/', views.student_reset_password, name='student_reset_password'),

    # Lecții
    path('lectii/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lectii/<int:lesson_id>/gestioneaza/', views.lesson_manage, name='lesson_manage'),
    path('lectii/adauga/', views.lesson_create, name='lesson_create'),
    path('lectii/adauga/<int:group_id>/', views.lesson_create, name='lesson_create_for_group'),
    path('lectii/<int:lesson_id>/editeaza/', views.lesson_edit, name='lesson_edit'),

    # Teme
    path('teme/', views.assignments_list, name='assignments_list'),
    path('grupe/<int:group_id>/teme-simulatoare/adauga/', views.simulator_assignment_create, name='simulator_assignment_create'),
    path('teme-simulatoare/<int:assignment_id>/sterge/', views.simulator_assignment_delete, name='simulator_assignment_delete'),
    path('teme/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),

    # Simulatoare
    path('simulatoare/', views.simulators_list, name='simulators_list'),
    path('simulatoare/abac/', views.abacus_simulator, name='abacus_simulator'),
    path('simulatoare/cartonase-flash/', views.flashcard_simulator, name='flashcard_simulator'),
    path('simulatoare/anzan/', views.anzan_simulator, name='anzan_simulator'),
    path('simulatoare/exercitii-abac/', views.abacus_exercises, name='abacus_exercises'),

    # Lecții live
    path('grupe/<int:group_id>/live/porneste/', views.live_session_start, name='live_session_start'),
    path('grupe/<int:group_id>/live/state/', views.live_state, name='live_state'),
    path('live/<int:session_id>/inchide/', views.live_session_end, name='live_session_end'),
    path('live/<int:session_id>/sarcina/adauga/', views.live_task_create, name='live_task_create'),
    path('live/sarcina/<int:task_id>/sterge/', views.live_task_delete, name='live_task_delete'),

    # API
    path('api/get-modules/', views.get_modules_for_course, name='get_modules_for_course'),
]
