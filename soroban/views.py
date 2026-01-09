from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg, Count
from .models import SorobanExercise, SorobanSession, SorobanProgress
from accounts.models import User
import json


@login_required
def soroban_simulator(request):
    """
    Pagina principală a simulatorului soroban
    """
    # Asigură-te că utilizatorul este elev
    if request.user.role != 'student':
        messages.error(request, 'Doar elevii pot accesa simulatorul soroban.')
        return redirect('home')

    # Obține sau creează progresul elevului
    progress, created = SorobanProgress.objects.get_or_create(student=request.user)

    # Exerciții disponibile pentru nivelul curent
    available_exercises = SorobanExercise.objects.filter(
        is_active=True
    ).order_by('difficulty', 'title')

    # Ultimele 5 sesiuni
    recent_sessions = SorobanSession.objects.filter(
        student=request.user
    ).order_by('-started_at')[:5]

    context = {
        'progress': progress,
        'available_exercises': available_exercises,
        'recent_sessions': recent_sessions,
    }

    return render(request, 'soroban/simulator.html', context)


@login_required
def start_session(request):
    """
    Start a new soroban practice session
    """
    if request.method == 'POST':
        exercise_id = request.POST.get('exercise_id')

        # Creează sesiune nouă
        if exercise_id:
            exercise = get_object_or_404(SorobanExercise, id=exercise_id, is_active=True)
            session = SorobanSession.objects.create(
                student=request.user,
                exercise=exercise
            )
        else:
            # Practică liberă (fără exercițiu specific)
            session = SorobanSession.objects.create(
                student=request.user
            )

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'exercise': {
                'title': exercise.title if exercise_id else 'Practică Liberă',
                'number_count': exercise.number_count if exercise_id else 10,
                'time_limit': exercise.time_limit_seconds if exercise_id else None,
            } if exercise_id else {}
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def submit_answer(request):
    """
    Salvează răspunsul elevului pentru o problemă
    API endpoint pentru JavaScript
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        session_id = data.get('session_id')
        problem = data.get('problem')
        answer = data.get('answer')
        correct = data.get('correct')
        time_taken = data.get('time')

        session = get_object_or_404(SorobanSession, id=session_id, student=request.user)

        # Adaugă răspunsul în detalii
        answer_detail = {
            'problem': problem,
            'answer': answer,
            'correct': correct,
            'time': time_taken
        }

        if not session.answers_detail:
            session.answers_detail = []

        session.answers_detail.append(answer_detail)
        session.problems_attempted += 1

        if correct:
            session.problems_correct += 1
            # Calculează puncte
            points = session.exercise.points_per_correct if session.exercise else 10
            session.points_earned += points

        session.save()

        return JsonResponse({
            'success': True,
            'total_points': session.points_earned,
            'accuracy': session.calculate_accuracy()
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def complete_session(request, session_id):
    """
    Finalizează o sesiune de practică
    """
    session = get_object_or_404(SorobanSession, id=session_id, student=request.user)

    if request.method == 'POST':
        session.mark_completed()

        # Actualizează progresul general al elevului
        progress, created = SorobanProgress.objects.get_or_create(student=request.user)
        progress.update_stats_from_session(session)

        # Actualizează și profilul studentului
        if hasattr(request.user, 'student_profile'):
            request.user.student_profile.total_points += session.points_earned
            request.user.student_profile.soroban_level = progress.current_level
            request.user.student_profile.save()

        messages.success(request, f'Sesiune finalizată! Ai câștigat {session.points_earned} puncte!')

        return redirect('soroban_stats')

    return redirect('soroban_simulator')


@login_required
def soroban_stats(request):
    """
    Pagina cu statistici detaliate pentru elev
    """
    if request.user.role != 'student':
        messages.error(request, 'Doar elevii pot vedea statisticile.')
        return redirect('home')

    progress, created = SorobanProgress.objects.get_or_create(student=request.user)

    # Statistici pe ultimele 30 de zile
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)

    recent_sessions = SorobanSession.objects.filter(
        student=request.user,
        started_at__gte=thirty_days_ago
    ).order_by('-started_at')

    # Agregări
    stats = SorobanSession.objects.filter(
        student=request.user,
        completed_at__isnull=False
    ).aggregate(
        total_sessions=Count('id'),
        total_problems=Sum('problems_attempted'),
        total_correct=Sum('problems_correct'),
        total_points=Sum('points_earned'),
        avg_accuracy=Avg('problems_correct') * 100 / Avg('problems_attempted') if Count('id') > 0 else 0
    )

    # Grafic progres pe zile (ultimele 7 zile)
    from datetime import datetime
    week_data = []
    for i in range(7):
        day = timezone.now() - timedelta(days=i)
        day_sessions = SorobanSession.objects.filter(
            student=request.user,
            started_at__date=day.date()
        )

        week_data.append({
            'date': day.strftime('%d/%m'),
            'sessions': day_sessions.count(),
            'points': day_sessions.aggregate(Sum('points_earned'))['points_earned__sum'] or 0,
            'accuracy': (day_sessions.aggregate(
                Avg('problems_correct')
            )['problems_correct__avg'] or 0) * 100 if day_sessions.count() > 0 else 0
        })

    week_data.reverse()

    context = {
        'progress': progress,
        'recent_sessions': recent_sessions[:10],
        'stats': stats,
        'week_data': week_data,
    }

    return render(request, 'soroban/stats.html', context)


@login_required
def leaderboard(request):
    """
    Clasament global Soroban
    """
    # Top 20 elevi după puncte totale
    top_students = SorobanProgress.objects.select_related('student').order_by(
        '-total_points'
    )[:20]

    # Poziția utilizatorului curent
    if request.user.role == 'student':
        user_progress, created = SorobanProgress.objects.get_or_create(student=request.user)
        user_rank = SorobanProgress.objects.filter(
            total_points__gt=user_progress.total_points
        ).count() + 1
    else:
        user_progress = None
        user_rank = None

    context = {
        'top_students': top_students,
        'user_progress': user_progress,
        'user_rank': user_rank,
    }

    return render(request, 'soroban/leaderboard.html', context)


# ==================== ADMIN/TEACHER VIEWS ====================

@login_required
def teacher_soroban_overview(request):
    """
    Vedere pentru profesori - progresul elevilor lor la soroban
    """
    if request.user.role != 'teacher':
        messages.error(request, 'Acces interzis.')
        return redirect('home')

    # Obține toți elevii profesorului (din grupe)
    from teacher_platform.models import GroupStudent

    students_in_groups = GroupStudent.objects.filter(
        group__teacher=request.user,
        is_active=True
    ).values_list('student_id', flat=True)

    # Progresul acestor elevi la soroban
    students_progress = SorobanProgress.objects.filter(
        student_id__in=students_in_groups
    ).select_related('student').order_by('-total_points')

    # Statistici generale
    total_sessions = SorobanSession.objects.filter(
        student_id__in=students_in_groups
    ).count()

    avg_level = SorobanProgress.objects.filter(
        student_id__in=students_in_groups
    ).aggregate(Avg('current_level'))['current_level__avg'] or 0

    context = {
        'students_progress': students_progress,
        'total_sessions': total_sessions,
        'avg_level': round(avg_level, 1),
    }

    return render(request, 'teacher_platform/soroban_overview.html', context)