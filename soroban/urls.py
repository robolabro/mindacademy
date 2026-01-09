from django.urls import path
from . import views

app_name = 'soroban'

urlpatterns = [
    # Simulator
    path('', views.soroban_simulator, name='simulator'),
    path('simulator/', views.soroban_simulator, name='simulator_alt'),

    # Sesiuni
    path('start-session/', views.start_session, name='start_session'),
    path('submit-answer/', views.submit_answer, name='submit_answer'),
    path('complete-session/<int:session_id>/', views.complete_session, name='complete_session'),

    # Statistici și clasament
    path('stats/', views.soroban_stats, name='stats'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),

    # Pentru profesori
    path('teacher/overview/', views.teacher_soroban_overview, name='teacher_overview'),
]