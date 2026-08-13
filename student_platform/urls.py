from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'student_platform'

urlpatterns = [
    path('', views.my_assignments, name='my_assignments'),
    path('login/', views.StudentLoginView.as_view(), name='login'),
    path('grupa/', views.schedule, name='schedule'),
    path('orar/', RedirectView.as_view(pattern_name='student_platform:schedule'), name='schedule_old'),
    path('live/state/', views.live_state_student, name='live_state'),
    path('live/sarcina/<int:task_id>/', views.live_run_task, name='live_run_task'),
    path('live/sarcina/<int:task_id>/progres/', views.live_task_progress, name='live_task_progress'),
    path('simulatoare/', views.simulators, name='simulators'),
    path('sarcina/<int:task_id>/', views.run_task, name='run_task'),
    path('sarcina/<int:task_id>/progres/', views.task_progress, name='task_progress'),
    path('practica/log/', views.practice_log, name='practice_log'),
]
