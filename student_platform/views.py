import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST

from teacher_platform.models import (
    GroupStudent, SimulatorAssignment, SimulatorTask, SimulatorTaskResult
)


def student_required(view_func):
    """Decorator pentru a verifica dacă utilizatorul este elev"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'student':
            messages.error(request, 'Acces restricționat doar pentru elevi.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def _assignments_for_student(user):
    """
    Temele vizibile pentru un elev: temele personalizate pentru el
    + temele de grupă (fără elev setat) din grupele în care este activ.
    """
    group_ids = GroupStudent.objects.filter(
        student=user, is_active=True
    ).values_list('group_id', flat=True)

    return SimulatorAssignment.objects.filter(
        Q(student=user) | Q(student__isnull=True, group_id__in=group_ids)
    ).select_related('group').prefetch_related(
        Prefetch('tasks', queryset=SimulatorTask.objects.order_by('order'))
    ).distinct()


def _task_for_student_or_404(user, task_id):
    """Returnează sarcina doar dacă tema ei îi aparține elevului."""
    task = get_object_or_404(
        SimulatorTask.objects.select_related('assignment', 'assignment__group'),
        pk=task_id
    )
    assignment = task.assignment
    if assignment.student_id is not None:
        if assignment.student_id != user.id:
            raise Http404
    else:
        is_member = GroupStudent.objects.filter(
            student=user, group_id=assignment.group_id, is_active=True
        ).exists()
        if not is_member:
            raise Http404
    return task


def _task_progress_data(task, result):
    """Progresul unui elev la o sarcină, ca dict pentru template/JS."""
    if result is None:
        return {
            'exercises': 0, 'correct': 0, 'incorrect': 0,
            'time_seconds': 0, 'time_display': '0:00',
            'completed': False, 'percent': 0,
        }
    if task.target_type == 'minutes':
        percent = min(100, round(result.time_spent_seconds / (task.target_value * 60) * 100)) if task.target_value else 0
    else:
        percent = min(100, round(result.completed_exercises / task.target_value * 100)) if task.target_value else 0
    return {
        'exercises': result.completed_exercises,
        'correct': result.correct,
        'incorrect': result.incorrect,
        'time_seconds': result.time_spent_seconds,
        'time_display': '%d:%02d' % divmod(result.time_spent_seconds, 60),
        'completed': result.completed,
        'percent': 100 if result.completed else percent,
    }


@login_required
@student_required
def my_assignments(request):
    """Pagina „Temele mele” — temele active, viitoare și expirate ale elevului."""
    student = request.user
    today = timezone.now().date()

    assignments = _assignments_for_student(student)

    results = {
        r.task_id: r
        for r in SimulatorTaskResult.objects.filter(
            student=student, task__assignment__in=assignments
        )
    }

    active, upcoming, past = [], [], []
    for assignment in assignments:
        tasks = []
        done_count = 0
        for task in assignment.tasks.all():
            progress = _task_progress_data(task, results.get(task.id))
            if progress['completed']:
                done_count += 1
            tasks.append({'task': task, 'progress': progress})

        entry = {
            'assignment': assignment,
            'tasks': tasks,
            'done_count': done_count,
            'total_count': len(tasks),
            'all_done': len(tasks) > 0 and done_count == len(tasks),
        }
        if assignment.start_date > today:
            upcoming.append(entry)
        elif assignment.end_date < today:
            past.append(entry)
        else:
            active.append(entry)

    active.sort(key=lambda e: e['assignment'].end_date)
    upcoming.sort(key=lambda e: e['assignment'].start_date)
    past.sort(key=lambda e: e['assignment'].end_date, reverse=True)

    context = {
        'active_assignments': active,
        'upcoming_assignments': upcoming,
        'past_assignments': past[:10],
        'today': today,
    }
    return render(request, 'student_platform/my_assignments.html', context)


@login_required
@student_required
def run_task(request, task_id):
    """
    Rulează o sarcină de simulator cu setările impuse de profesor.
    Elevul nu are acces la setări — primește doar exercițiile.
    """
    student = request.user
    task = _task_for_student_or_404(student, task_id)
    assignment = task.assignment

    today = timezone.now().date()
    if assignment.start_date > today:
        messages.info(request, 'Această temă nu a început încă.')
        return redirect('student_platform:my_assignments')

    result = SimulatorTaskResult.objects.filter(task=task, student=student).first()
    progress = _task_progress_data(task, result)

    context = {
        'task': task,
        'assignment': assignment,
        'is_expired': assignment.end_date < today,
        'settings_json': json.dumps(task.settings),
        'progress_json': json.dumps(progress),
        'target_json': json.dumps({
            'type': task.target_type,
            'value': task.target_value,
        }),
    }
    return render(request, 'student_platform/task_runner.html', context)


@login_required
@student_required
@require_POST
def task_progress(request, task_id):
    """
    Endpoint POST: acumulează progresul elevului la o sarcină.
    Primește delte (exerciții/corecte/greșite/secunde) și le adaugă
    la SimulatorTaskResult; marchează sarcina finalizată la atingerea țintei.
    """
    student = request.user
    task = _task_for_student_or_404(student, task_id)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'JSON invalid'}, status=400)

    def _delta(key, cap=1000):
        try:
            value = int(data.get(key, 0))
        except (TypeError, ValueError):
            return 0
        return max(0, min(value, cap))

    result, _ = SimulatorTaskResult.objects.get_or_create(task=task, student=student)
    result.completed_exercises += _delta('exercises')
    result.correct += _delta('correct')
    result.incorrect += _delta('incorrect')
    result.time_spent_seconds += _delta('time_seconds', cap=3600)

    if not result.completed:
        if task.target_type == 'minutes':
            reached = result.time_spent_seconds >= task.target_value * 60
        else:
            reached = result.completed_exercises >= task.target_value
        if reached:
            result.completed = True
            result.completed_at = timezone.now()

    result.save()

    return JsonResponse({'ok': True, 'progress': _task_progress_data(task, result)})
