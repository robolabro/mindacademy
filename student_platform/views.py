import json
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST

from teacher_platform.models import (
    GroupStudent, Lesson, SimulatorAssignment, SimulatorTask,
    SimulatorTaskResult, SimulatorPracticeLog
)


def student_required(view_func):
    """Decorator pentru a verifica dacă utilizatorul este elev"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('student_platform:login')
        if request.user.role != 'student':
            messages.error(request, 'Acces restricționat doar pentru elevi.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


class StudentLoginView(LoginView):
    """Pagina de login dedicată elevilor (mindacademy.ro/student/login/)."""
    template_name = 'student_platform/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return '/dupa-login/'


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


def _day_progress(task, result):
    """Progresul unei zile la o sarcină, ca dict pentru template/JS."""
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


def assignment_day_states(assignment, tasks, results, today):
    """
    Starea fiecărei zile din perioada temei, pentru un elev:
    done (verde) / missed (roșu) / today (albastru) / upcoming (galben).
    `results` = dict {(task_id, date): SimulatorTaskResult}.
    """
    days = []
    day = assignment.start_date
    while day <= assignment.end_date:
        all_done = bool(tasks) and all(
            (r := results.get((t.id, day))) is not None and r.completed for t in tasks
        )
        if all_done:
            state = 'done'
        elif day < today:
            state = 'missed'
        elif day == today:
            state = 'today'
        else:
            state = 'upcoming'
        days.append({'date': day, 'state': state})
        day += timedelta(days=1)
    return days


@student_required
def my_assignments(request):
    """Pagina „Temele mele” — teme zilnice: progresul de AZI + calendarul zilelor."""
    student = request.user
    today = timezone.localdate()

    assignments = _assignments_for_student(student)

    results = {
        (r.task_id, r.date): r
        for r in SimulatorTaskResult.objects.filter(
            student=student, task__assignment__in=assignments
        )
    }

    active, upcoming, past = [], [], []
    for assignment in assignments:
        tasks = list(assignment.tasks.all())
        task_items = []
        done_today = 0
        for task in tasks:
            progress = _day_progress(task, results.get((task.id, today)))
            if progress['completed']:
                done_today += 1
            task_items.append({'task': task, 'progress': progress})

        days = assignment_day_states(assignment, tasks, results, today)

        entry = {
            'assignment': assignment,
            'tasks': task_items,
            'days': days,
            'done_count': done_today,
            'total_count': len(tasks),
            'all_done_today': len(tasks) > 0 and done_today == len(tasks),
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
        'active_menu': 'teme',
    }
    return render(request, 'student_platform/my_assignments.html', context)


@student_required
def schedule(request):
    """Orar: lecțiile viitoare + detalii despre grupă și nivelul elevului."""
    student = request.user
    today = timezone.localdate()

    memberships = GroupStudent.objects.filter(
        student=student, is_active=True
    ).select_related('group', 'group__course', 'group__teacher', 'group__location')
    group_ids = [m.group_id for m in memberships]

    upcoming_lessons = Lesson.objects.filter(
        group_id__in=group_ids, date__gte=today
    ).select_related('group', 'lesson_template').order_by('date', 'start_time')[:12]

    past_lessons = Lesson.objects.filter(
        group_id__in=group_ids, date__lt=today
    ).select_related('group', 'lesson_template').order_by('-date', '-start_time')[:6]

    profile = getattr(student, 'student_profile', None)

    context = {
        'memberships': memberships,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'soroban_level': profile.soroban_level if profile else None,
        'initial_tab': 'live' if request.GET.get('tab') == 'live' else 'calendar',
        'active_menu': 'grupa',
    }
    return render(request, 'student_platform/schedule.html', context)


@student_required
def simulators(request):
    """Simulatoare pentru antrenament liber (aceleași ca ale profesorului)."""
    context = {'active_menu': 'simulatoare'}
    return render(request, 'student_platform/simulators.html', context)


@student_required
def run_task(request, task_id):
    """
    Rulează o sarcină de simulator cu setările impuse de profesor.
    Elevul nu are acces la setări — primește doar exercițiile.
    Progresul se contorizează pe ZIUA curentă (temele sunt zilnice).
    """
    student = request.user
    task = _task_for_student_or_404(student, task_id)
    assignment = task.assignment

    today = timezone.localdate()
    if assignment.start_date > today:
        messages.info(request, 'Această temă nu a început încă.')
        return redirect('student_platform:my_assignments')

    result = SimulatorTaskResult.objects.filter(task=task, student=student, date=today).first()
    progress = _day_progress(task, result)

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
        'active_menu': 'teme',
    }
    return render(request, 'student_platform/task_runner.html', context)


def _log_scalar(value, cap):
    """
    Normalizează o valoare din istoricul de exerciții (venită de la elev)
    la un scalar mărginit: numerele rămân numere, orice altceva devine text
    scurtat; obiectele/listele sunt respinse. Previne umflarea JSONField.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if value is None:
        return None
    return str(value)[:cap]


def _read_deltas(request):
    """Citește delte numerice pozitive din corpul JSON al cererii."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    def delta(key, cap=1000):
        try:
            value = int(data.get(key, 0))
        except (TypeError, ValueError):
            return 0
        return max(0, min(value, cap))

    return data, delta


@student_required
@require_POST
def task_progress(request, task_id):
    """
    Endpoint POST: acumulează progresul elevului la o sarcină pe ziua curentă.
    Marchează ziua finalizată la atingerea țintei (exerciții sau minute).
    """
    student = request.user
    task = _task_for_student_or_404(student, task_id)

    parsed = _read_deltas(request)
    if parsed is None:
        return JsonResponse({'ok': False, 'error': 'JSON invalid'}, status=400)
    _, delta = parsed

    today = timezone.localdate()
    result, _created = SimulatorTaskResult.objects.get_or_create(
        task=task, student=student, date=today
    )
    result.completed_exercises += delta('exercises')
    result.correct += delta('correct')
    result.incorrect += delta('incorrect')
    result.time_spent_seconds += delta('time_seconds', cap=3600)

    if not result.completed:
        if task.target_type == 'minutes':
            reached = result.time_spent_seconds >= task.target_value * 60
        else:
            reached = result.completed_exercises >= task.target_value
        if reached:
            result.completed = True
            result.completed_at = timezone.now()

    result.save()

    return JsonResponse({'ok': True, 'progress': _day_progress(task, result)})


@student_required
@require_POST
def practice_log(request):
    """
    Endpoint POST: jurnalizează antrenamentul liber pe simulatoare
    (în afara temelor) — un rând per elev × simulator × zi.
    """
    student = request.user
    parsed = _read_deltas(request)
    if parsed is None:
        return JsonResponse({'ok': False, 'error': 'JSON invalid'}, status=400)
    data, delta = parsed

    simulator = data.get('simulator')
    valid = {key for key, _ in SimulatorTask.SIMULATOR_CHOICES}
    if simulator not in valid:
        return JsonResponse({'ok': False, 'error': 'Simulator necunoscut'}, status=400)

    log, _created = SimulatorPracticeLog.objects.get_or_create(
        student=student, simulator=simulator, date=timezone.localdate()
    )
    log.exercises += delta('exercises')
    log.correct += delta('correct')
    log.incorrect += delta('incorrect')
    log.time_spent_seconds += delta('time_seconds', cap=3600)
    log.save()

    return JsonResponse({'ok': True})


# ==================== LECȚII LIVE (elev) ====================

from teacher_platform.models import LiveSession, LiveTask, LiveTaskResult, LiveParticipant


def _active_live_session_for(student):
    """Sesiunea live activă din grupele elevului (prima găsită)."""
    group_ids = GroupStudent.objects.filter(
        student=student, is_active=True
    ).values_list('group_id', flat=True)
    return LiveSession.objects.filter(
        group_id__in=group_ids, ended_at__isnull=True
    ).select_related('group').first()


def _live_task_for_student_or_404(user, task_id):
    """Sarcina live doar dacă aparține unei sesiuni din grupele elevului."""
    task = get_object_or_404(
        LiveTask.objects.select_related('session', 'session__group'),
        pk=task_id
    )
    if task.student_id is not None and task.student_id != user.id:
        raise Http404
    is_member = GroupStudent.objects.filter(
        student=user, group_id=task.session.group_id, is_active=True
    ).exists()
    if not is_member:
        raise Http404
    return task


def _live_progress(task, result):
    """Progresul la o sarcină live (fără dimensiune zilnică)."""
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


@student_required
def live_state_student(request):
    """
    Polling elev: sesiunea live activă + sarcinile lui. Fiecare apel
    contează ca heartbeat de prezență (elevul apare „conectat" la profesor).
    """
    student = request.user
    session = _active_live_session_for(student)
    if session is None:
        return JsonResponse({'ok': True, 'active': False})

    # heartbeat prezență (auto_now actualizează last_seen la fiecare save)
    participant, created = LiveParticipant.objects.get_or_create(session=session, student=student)
    if not created:
        participant.save(update_fields=['last_seen'])

    tasks = session.tasks.filter(
        Q(student__isnull=True) | Q(student=student)
    ).order_by('order')
    results = {
        r.task_id: r for r in LiveTaskResult.objects.filter(task__session=session, student=student)
    }
    sim_names = dict(SimulatorTask.SIMULATOR_CHOICES)

    tasks_json = []
    for t in tasks:
        s = t.settings or {}
        chips = [v for v in (s.get('complexity_label'), s.get('digits_label'),
                             s.get('difficulty_label')) if v]
        if s.get('terms'):
            chips.append(f"{s['terms']} termeni")
        tasks_json.append({
            'id': t.id,
            'order': t.order,
            'simulator_name': sim_names.get(t.simulator, t.simulator),
            'personal': t.student_id is not None,
            'chips': chips,
            'target': t.get_target_display(),
            'progress': _live_progress(t, results.get(t.id)),
        })

    return JsonResponse({
        'ok': True,
        'active': True,
        'session_id': session.id,
        'group_name': session.group.name,
        'started_at': timezone.localtime(session.started_at).strftime('%H:%M'),
        'meeting_link': session.group.meeting_link if session.group.lesson_type == 'online' else '',
        'tasks': tasks_json,
    })


@student_required
def live_run_task(request, task_id):
    """Rulează o sarcină live cu setările impuse — reutilizează runner-ul de teme."""
    student = request.user
    task = _live_task_for_student_or_404(student, task_id)

    if task.session.ended_at is not None:
        messages.info(request, 'Lecția live s-a încheiat.')
        return redirect('student_platform:schedule')

    result = LiveTaskResult.objects.filter(task=task, student=student).first()
    progress = _live_progress(task, result)

    context = {
        'task': task,
        'runner_title': f'Lecție live · {task.session.group.name}',
        'is_live': True,
        'is_expired': False,
        'settings_json': json.dumps(task.settings),
        'progress_json': json.dumps(progress),
        'target_json': json.dumps({'type': task.target_type, 'value': task.target_value}),
        'progress_url': f'/student/live/sarcina/{task.id}/progres/',
        'back_url': '/student/grupa/?tab=live',
        'back_label': '← Înapoi la lecția live',
        'active_menu': 'grupa',
    }
    return render(request, 'student_platform/task_runner.html', context)


@student_required
@require_POST
def live_task_progress(request, task_id):
    """POST: acumulează progresul la o sarcină live + heartbeat prezență."""
    student = request.user
    task = _live_task_for_student_or_404(student, task_id)

    # După ce profesorul a închis lecția, rezultatele devin imutabile.
    if task.session.ended_at is not None:
        return JsonResponse({'ok': False, 'error': 'Lecția s-a încheiat'}, status=409)

    parsed = _read_deltas(request)
    if parsed is None:
        return JsonResponse({'ok': False, 'error': 'JSON invalid'}, status=400)
    data, delta = parsed

    result, _created = LiveTaskResult.objects.get_or_create(task=task, student=student)
    result.completed_exercises += delta('exercises')
    result.correct += delta('correct')
    result.incorrect += delta('incorrect')
    result.time_spent_seconds += delta('time_seconds', cap=3600)

    # istoric detaliat al exercițiilor (pentru raportul profesorului).
    # Conținutul vine de la elev — coercem la scalari mărginiți (anti-DoS
    # + defense-in-depth alături de escaping-ul la randare).
    entries = data.get('entries')
    if isinstance(entries, list) and entries:
        log = list(result.exercise_log or [])
        for e in entries[:50]:
            if not isinstance(e, dict):
                continue
            log.append({
                'ex': _log_scalar(e.get('ex'), 120),
                'ca': _log_scalar(e.get('ca'), 40),
                'ua': _log_scalar(e.get('ua'), 40),
                'ok': bool(e.get('ok')),
                't': round(float(e.get('t', 0)), 1) if isinstance(e.get('t'), (int, float)) else 0,
            })
        result.exercise_log = log[-200:]

    if not result.completed:
        if task.target_type == 'minutes':
            reached = result.time_spent_seconds >= task.target_value * 60
        else:
            reached = result.completed_exercises >= task.target_value
        if reached:
            result.completed = True
            result.completed_at = timezone.now()

    result.save()

    # heartbeat prezență
    participant, created = LiveParticipant.objects.get_or_create(session=task.session, student=student)
    if not created:
        participant.save(update_fields=['last_seen'])

    return JsonResponse({'ok': True, 'progress': _live_progress(task, result)})
