from django.urls import path
from . import views

app_name = 'student_platform'

urlpatterns = [
    path('', views.my_assignments, name='my_assignments'),
    path('sarcina/<int:task_id>/', views.run_task, name='run_task'),
    path('sarcina/<int:task_id>/progres/', views.task_progress, name='task_progress'),
]
