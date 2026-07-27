from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Group, GroupStudent, Lesson, Attendance, Assignment, AssignmentSubmission, LessonNote, SimulatorAssignment, SimulatorTask, SimulatorTaskResult, SimulatorPracticeLog, LiveSession, LiveTask, LiveTaskResult, LiveParticipant
from accounts.models import User, StudentProfile, TeacherProfile
from courses.models import Module, LessonTemplate
from .forms import GroupForm, StudentForm, EditStudentForm, LessonForm, TeacherProfileForm


def teacher_required(view_func):
    """Decorator pentru a verifica dacă utilizatorul este profesor"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'teacher':
            messages.error(request, 'Acces restricționat doar pentru profesori.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def simulator_access(view_func):
    """
    Decorator pentru simulatoare: acces atât pentru profesori, cât și
    pentru elevi (antrenament liber acasă).
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role not in ('teacher', 'student'):
            messages.error(request, 'Acces restricționat.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def _simulator_context(request):
    """Context comun pentru paginile de simulatoare (profesor sau elev)."""
    is_student = request.user.role == 'student'
    return {
        'base_template': 'student_platform/base_student.html' if is_student else 'teacher_platform/base_teacher.html',
        'is_student_user': is_student,
        'active_menu': 'simulatoare',
    }


@login_required
@teacher_required
def dashboard(request):
    """
    Dashboard principal pentru profesor - overview cu statistici
    """
    teacher = request.user

    # Statistici generale
    total_groups = Group.objects.filter(teacher=teacher, is_active=True).count()
    total_students = GroupStudent.objects.filter(
        group__teacher=teacher,
        is_active=True
    ).distinct().count()

    # Lecții pentru săptămâna curentă
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    weekly_lessons = Lesson.objects.filter(
        group__teacher=teacher,
        date__range=[week_start, week_end]
    ).count()

    # Teme nenotate
    ungraded_assignments = AssignmentSubmission.objects.filter(
        assignment__group__teacher=teacher,
        is_graded=False
    ).count()

    # Lecțiile următoare (următoarele 5)
    upcoming_lessons = Lesson.objects.filter(
        group__teacher=teacher,
        date__gte=today,
        status='scheduled'
    ).select_related('group', 'lesson_template').order_by('date', 'start_time')[:5]

    # Grupele active
    active_groups = Group.objects.filter(
        teacher=teacher,
        is_active=True
    ).annotate(
        student_count=Count('students', filter=Q(students__is_active=True))
    ).select_related('course', 'module', 'location')[:6]

    # Teme cu deadline aproape (următoarele 7 zile)
    upcoming_deadline = today + timedelta(days=7)
    upcoming_assignments = Assignment.objects.filter(
        group__teacher=teacher,
        due_date__range=[today, upcoming_deadline]
    ).select_related('group').order_by('due_date')[:5]

    context = {
        'teacher': teacher,
        'total_groups': total_groups,
        'total_students': total_students,
        'weekly_lessons': weekly_lessons,
        'ungraded_assignments': ungraded_assignments,
        'upcoming_lessons': upcoming_lessons,
        'active_groups': active_groups,
        'upcoming_assignments': upcoming_assignments,
    }

    return render(request, 'teacher_platform/dashboard.html', context)


@login_required
@teacher_required
def groups_list(request):
    """
    Lista tuturor grupelor profesorului
    """
    teacher = request.user

    # Filtrare
    status_filter = request.GET.get('status', 'active')

    groups_query = Group.objects.filter(teacher=teacher)

    if status_filter == 'active':
        groups_query = groups_query.filter(is_active=True)
    elif status_filter == 'inactive':
        groups_query = groups_query.filter(is_active=False)

    groups = groups_query.annotate(
        student_count=Count('students', filter=Q(students__is_active=True))
    ).select_related('course', 'module', 'location').order_by('-created_at')

    context = {
        'groups': groups,
        'status_filter': status_filter,
    }

    return render(request, 'teacher_platform/groups_list.html', context)


@login_required
@teacher_required
def group_detail(request, group_id):
    """
    Detalii despre o grupă specifică
    """
    group = get_object_or_404(
        Group.objects.select_related('course', 'module', 'location', 'teacher'),
        id=group_id,
        teacher=request.user
    )

    # Studenții din grupă
    students = GroupStudent.objects.filter(
        group=group,
        is_active=True
    ).select_related('student', 'student__student_profile').order_by('student__first_name')

    # Lecțiile grupei (următoarele și trecute)
    upcoming_lessons = Lesson.objects.filter(
        group=group,
        date__gte=timezone.now().date()
    ).select_related('lesson_template').order_by('date', 'start_time')[:10]

    past_lessons = Lesson.objects.filter(
        group=group,
        date__lt=timezone.now().date()
    ).select_related('lesson_template').order_by('-date', '-start_time')[:10]

    # Temele grupei
    assignments = Assignment.objects.filter(
        group=group
    ).prefetch_related('submissions').order_by('-due_date')[:10]

    # Temele pe simulatoare (de grupă + personalizate)
    simulator_assignments = SimulatorAssignment.objects.filter(
        group=group
    ).select_related('student').prefetch_related('tasks').order_by('-start_date', '-created_at')[:20]

    # Progresul elevilor la temele pe simulatoare (zilnic: elev × sarcină × zi)
    from student_platform.views import assignment_day_states

    _results = SimulatorTaskResult.objects.filter(
        task__assignment__in=simulator_assignments
    )
    _totals = {}
    _by_day = {}
    for r in _results:
        key = (r.task_id, r.student_id)
        t = _totals.setdefault(key, {'ex': 0, 'ok': 0, 'bad': 0, 'sec': 0, 'days_done': 0})
        t['ex'] += r.completed_exercises
        t['ok'] += r.correct
        t['bad'] += r.incorrect
        t['sec'] += r.time_spent_seconds
        if r.completed:
            t['days_done'] += 1
        _by_day[(r.task_id, r.student_id, r.date)] = r

    _sim_short = {
        'anzan': 'Anzan', 'flashcards': 'Cartonașe',
        'flashcard-exercises': 'Exerciții', 'worksheet': 'Fișă',
    }
    _today = timezone.localdate()
    for sa in simulator_assignments:
        tasks = list(sa.tasks.all())
        for t in tasks:
            t.short_name = _sim_short.get(t.simulator, t.simulator)
        last_day = min(_today, sa.end_date)
        elapsed = max(0, (last_day - sa.start_date).days + 1) if sa.start_date <= _today else 0
        roster = [sa.student] if sa.student else [gs.student for gs in students]
        rows = []
        for st in roster:
            cells = []
            for t in tasks:
                totals = _totals.get((t.id, st.id))
                if totals is None:
                    cells.append({'status': 'none'})
                    continue
                answered = totals['ok'] + totals['bad']
                accuracy = round(totals['ok'] / answered * 100) if answered else 0
                cells.append({
                    'status': 'done' if (elapsed and totals['days_done'] >= elapsed) else 'working',
                    'days_done': totals['days_done'],
                    'days_elapsed': elapsed,
                    'exercises': totals['ex'],
                    'accuracy': accuracy,
                    'time_display': '%d:%02d' % divmod(totals['sec'], 60),
                })
            student_results = {
                (t.id, d): _by_day.get((t.id, st.id, d))
                for t in tasks
                for d in [sa.start_date + timedelta(days=k)
                          for k in range((sa.end_date - sa.start_date).days + 1)]
            }
            days = assignment_day_states(sa, tasks, student_results, _today)
            green_days = sum(1 for d in days if d['state'] == 'done')
            rows.append({
                'student': st,
                'cells': cells,
                'days': days,
                'green_days': green_days,
                'elapsed_days': elapsed,
                'all_done': elapsed > 0 and green_days >= elapsed,
            })
        sa.progress_rows = rows
        sa.students_done = sum(1 for row in rows if row['all_done'])
        sa.students_total = len(rows)

    # Șabloane de lecții disponibile din modulul grupei
    lesson_templates = []
    if group.module:
        lesson_templates = LessonTemplate.objects.filter(
            module=group.module,
            is_active=True
        ).order_by('order')

    # Sesiunea live activă (dacă există)
    live_session = LiveSession.objects.filter(group=group, ended_at__isnull=True).first()

    context = {
        'group': group,
        'students': students,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'assignments': assignments,
        'simulator_assignments': simulator_assignments,
        'lesson_templates': lesson_templates,
        'live_session': live_session,
    }

    return render(request, 'teacher_platform/group_detail.html', context)


@login_required
@teacher_required
def calendar_view(request):
    """
    Calendar cu toate lecțiile profesorului
    Suportă view_mode: 'list' (timeline) sau 'calendar' (grid)
    """
    teacher = request.user

    # Obține luna și anul din query params sau folosește luna curentă
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    view_mode = request.GET.get('view', 'list')  # 'list' sau 'calendar'

    # Prima și ultima zi a lunii
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)

    # Lecții pentru luna selectată
    lessons = Lesson.objects.filter(
        group__teacher=teacher,
        date__range=[first_day, last_day]
    ).select_related('group', 'group__module', 'lesson_template').order_by('date', 'start_time')

    # Grupuri pentru calendar view
    groups = Group.objects.filter(
        teacher=teacher,
        is_active=True
    ).select_related('course', 'module')

    # Calculează luna anterioară și următoare pentru navigare
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # Pentru calendar grid view, calculează săptămânile și zilele
    calendar_weeks = []
    if view_mode == 'calendar':
        import calendar as cal
        month_calendar = cal.monthcalendar(year, month)

        # Creează un dicționar cu lecțiile organizate pe zile
        lessons_by_date = {}
        for lesson in lessons:
            if lesson.date not in lessons_by_date:
                lessons_by_date[lesson.date] = []
            lessons_by_date[lesson.date].append(lesson)

        # Construiește săptămânile cu informații despre lecții
        for week in month_calendar:
            week_days = []
            for day in week:
                if day == 0:
                    week_days.append({'day': None, 'lessons': []})
                else:
                    date_obj = datetime(year, month, day).date()
                    week_days.append({
                        'day': day,
                        'date': date_obj,
                        'lessons': lessons_by_date.get(date_obj, []),
                        'is_today': date_obj == timezone.now().date()
                    })
            calendar_weeks.append(week_days)

    context = {
        'lessons': lessons,
        'groups': groups,
        'current_year': year,
        'current_month': month,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': timezone.now().date(),
        'view_mode': view_mode,
        'calendar_weeks': calendar_weeks,
    }

    return render(request, 'teacher_platform/calendar.html', context)


@login_required
@teacher_required
def students_list(request):
    """
    Lista tuturor studenților profesorului
    """
    teacher = request.user

    # Filtrare după grupă
    group_filter = request.GET.get('group', '')

    # Obține elevii din grupe
    students_in_groups = GroupStudent.objects.filter(
        group__teacher=teacher,
        is_active=True
    ).select_related('student', 'student__student_profile', 'group')

    if group_filter:
        students_in_groups = students_in_groups.filter(group_id=group_filter)

    # Obține și elevii creați de profesor dar care nu sunt într-o grupă
    students_without_group = []
    if not group_filter:  # Doar când nu e filtru de grupă
        student_profiles = StudentProfile.objects.filter(
            teacher=teacher
        ).select_related('user')

        # Exclude elevii care sunt deja în grupe
        students_with_groups_ids = students_in_groups.values_list('student_id', flat=True)
        for profile in student_profiles:
            if profile.user.id not in students_with_groups_ids:
                # Creează un obiect pseudo-GroupStudent pentru consistență în template
                class StudentWithoutGroup:
                    def __init__(self, student):
                        self.student = student
                        self.group = None
                        self.lessons_attended = 0
                        self.lessons_missed = 0

                    def get_attendance_rate(self):
                        return 0

                students_without_group.append(StudentWithoutGroup(profile.user))

    students = list(students_in_groups.order_by('student__first_name', 'student__last_name'))
    students.extend(students_without_group)

    # Grupele pentru filtru
    groups = Group.objects.filter(
        teacher=teacher,
        is_active=True
    ).order_by('name')

    context = {
        'students': students,
        'groups': groups,
        'group_filter': group_filter,
    }

    return render(request, 'teacher_platform/students_list.html', context)


@login_required
@teacher_required
def student_detail(request, student_id):
    """
    Detalii despre un student specific
    """
    student = get_object_or_404(User, id=student_id, role='student')

    # Verifică dacă există student_profile
    if not hasattr(student, 'student_profile'):
        messages.error(request, 'Profilul de student nu a fost găsit.')
        return redirect('teacher_platform:students_list')

    # Verifică dacă profesorul are acces la acest student
    # (fie prin grupă, fie dacă l-a creat el direct)
    group_student = GroupStudent.objects.filter(
        student=student,
        group__teacher=request.user
    ).first()

    # Verifică și dacă profesorul a creat acest student
    is_creator = (student.student_profile.teacher == request.user)

    if not group_student and not is_creator:
        messages.error(request, 'Nu aveți acces la acest student.')
        return redirect('teacher_platform:students_list')

    # Grupele studentului
    student_groups = GroupStudent.objects.filter(
        student=student,
        is_active=True
    ).select_related('group', 'group__course', 'group__module')

    # Prezențe - queryset complet pentru statistici
    attendances_full = Attendance.objects.filter(
        student=student,
        lesson__group__teacher=request.user
    ).select_related('lesson', 'lesson__group')

    # Prezențe - limitate pentru afișare
    attendances = attendances_full.order_by('-lesson__date')[:20]

    # Teme predate
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__group__teacher=request.user
    ).select_related('assignment', 'assignment__group').order_by('-submitted_at')[:20]

    # Statistici - calculăm pe queryset-ul complet, nu cel sliced
    total_lessons = attendances_full.count()
    present_count = attendances_full.filter(is_present=True).count()
    attendance_rate = round((present_count / total_lessons * 100), 2) if total_lessons > 0 else 0

    avg_performance = attendances_full.filter(
        performance_rating__isnull=False
    ).aggregate(Avg('performance_rating'))['performance_rating__avg']

    # Statistici lunare pe simulatoare (teme vs antrenament liber)
    today = timezone.localdate()
    try:
        year, month = map(int, (request.GET.get('luna') or '').split('-'))
        stats_month = datetime(year, month, 1).date()
    except (ValueError, TypeError):
        stats_month = today.replace(day=1)
    prev_month = (stats_month - timedelta(days=1)).replace(day=1)
    next_month = (stats_month + timedelta(days=32)).replace(day=1)

    sim_names = dict(SimulatorTask.SIMULATOR_CHOICES)

    def _stat_rows(queryset, sim_field):
        rows = []
        for row in queryset:
            answered = (row['ok'] or 0) + (row['bad'] or 0)
            rows.append({
                'simulator': sim_names.get(row[sim_field], row[sim_field]),
                'exercises': row['ex'] or 0,
                'correct': row['ok'] or 0,
                'accuracy': round((row['ok'] or 0) / answered * 100) if answered else 0,
                'time_display': '%d:%02d' % divmod(row['sec'] or 0, 60),
            })
        return rows

    homework_stats = _stat_rows(
        SimulatorTaskResult.objects.filter(
            student=student, date__year=stats_month.year, date__month=stats_month.month
        ).values('task__simulator').annotate(
            ex=Sum('completed_exercises'), ok=Sum('correct'),
            bad=Sum('incorrect'), sec=Sum('time_spent_seconds')
        ).order_by('task__simulator'),
        'task__simulator'
    )
    practice_stats = _stat_rows(
        SimulatorPracticeLog.objects.filter(
            student=student, date__year=stats_month.year, date__month=stats_month.month
        ).values('simulator').annotate(
            ex=Sum('exercises'), ok=Sum('correct'),
            bad=Sum('incorrect'), sec=Sum('time_spent_seconds')
        ).order_by('simulator'),
        'simulator'
    )

    context = {
        'student': student,
        'group_student': group_student,
        'student_groups': student_groups,
        'attendances': attendances,
        'submissions': submissions,
        'attendance_rate': attendance_rate,
        'avg_performance': round(avg_performance, 2) if avg_performance else None,
        'stats_month': stats_month,
        'prev_month': prev_month.strftime('%Y-%m'),
        'next_month': next_month.strftime('%Y-%m'),
        'show_next_month': next_month <= today,
        'homework_stats': homework_stats,
        'practice_stats': practice_stats,
    }

    return render(request, 'teacher_platform/student_detail.html', context)


@login_required
@teacher_required
def lesson_detail(request, lesson_id):
    """
    Detalii despre o lecție și tracking prezență
    """
    lesson = get_object_or_404(
        Lesson.objects.select_related('group', 'lesson_template'),
        id=lesson_id,
        group__teacher=request.user
    )

    # Studenții din grupă și prezența lor
    students_data = []
    group_students = GroupStudent.objects.filter(
        group=lesson.group,
        is_active=True
    ).select_related('student')

    for gs in group_students:
        attendance = Attendance.objects.filter(
            lesson=lesson,
            student=gs.student
        ).first()

        students_data.append({
            'group_student': gs,
            'student': gs.student,
            'attendance': attendance,
        })

    context = {
        'lesson': lesson,
        'students_data': students_data,
    }

    return render(request, 'teacher_platform/lesson_detail.html', context)


@login_required
@teacher_required
def assignments_list(request):
    """
    Integrator: toate temele pe simulatoare din toate grupele profesorului,
    cu progresul elevilor, grupate pe active / viitoare / încheiate.
    """
    teacher = request.user
    today = timezone.localdate()
    group_filter = request.GET.get('group', '')

    assignments_query = SimulatorAssignment.objects.filter(
        group__teacher=teacher
    ).select_related('group', 'student').prefetch_related('tasks')

    if group_filter:
        assignments_query = assignments_query.filter(group_id=group_filter)

    assignments = list(assignments_query.order_by('-start_date', '-created_at'))

    # Progres: elevi care au terminat toate zilele scurse din temă
    results = SimulatorTaskResult.objects.filter(
        task__assignment__in=assignments
    ).values('task__assignment_id', 'student_id', 'date').annotate(
        tasks_done=Count('id', filter=Q(completed=True))
    )
    done_map = {}
    for row in results:
        done_map.setdefault((row['task__assignment_id'], row['student_id']), {})[row['date']] = row['tasks_done']

    memberships = GroupStudent.objects.filter(
        group__teacher=teacher, is_active=True
    ).values_list('group_id', 'student_id')
    roster = {}
    for gid, sid in memberships:
        roster.setdefault(gid, []).append(sid)

    active, upcoming, past = [], [], []
    for sa in assignments:
        task_count = len(sa.tasks.all())
        student_ids = [sa.student_id] if sa.student_id else roster.get(sa.group_id, [])
        last_day = min(today, sa.end_date)
        elapsed = max(0, (last_day - sa.start_date).days + 1) if sa.start_date <= today else 0
        students_ok = 0
        for sid in student_ids:
            days = done_map.get((sa.id, sid), {})
            ok_days = sum(
                1 for d, n in days.items()
                if sa.start_date <= d <= last_day and n >= task_count
            )
            if elapsed > 0 and ok_days >= elapsed:
                students_ok += 1
        entry = {
            'assignment': sa,
            'task_count': task_count,
            'students_total': len(student_ids),
            'students_ok': students_ok,
            'elapsed_days': elapsed,
            'total_days': (sa.end_date - sa.start_date).days + 1,
        }
        if sa.start_date > today:
            upcoming.append(entry)
        elif sa.end_date < today:
            past.append(entry)
        else:
            active.append(entry)

    groups = Group.objects.filter(teacher=teacher, is_active=True).order_by('name')

    context = {
        'active_entries': active,
        'upcoming_entries': upcoming,
        'past_entries': past[:20],
        'groups': groups,
        'group_filter': group_filter,
        'today': today,
    }

    return render(request, 'teacher_platform/assignments_list.html', context)


@login_required
@teacher_required
def assignment_detail(request, assignment_id):
    """
    Detalii despre o temă și submissions-urile studentilor
    """
    assignment = get_object_or_404(
        Assignment.objects.select_related('group'),
        id=assignment_id,
        group__teacher=request.user
    )

    # Submissions
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).select_related('student').order_by('-submitted_at')

    # Studenții care nu au predat
    students_submitted = submissions.values_list('student_id', flat=True)
    students_not_submitted = GroupStudent.objects.filter(
        group=assignment.group,
        is_active=True
    ).exclude(student_id__in=students_submitted).select_related('student')

    context = {
        'assignment': assignment,
        'submissions': submissions,
        'students_not_submitted': students_not_submitted,
        'today': timezone.now().date(),
    }

    return render(request, 'teacher_platform/assignment_detail.html', context)


@login_required
@teacher_required
def group_add(request):
    """
    Adaugă o grupă nouă
    """
    teacher = request.user

    if request.method == 'POST':
        form = GroupForm(request.POST, teacher=teacher)
        if form.is_valid():
            group = form.save(commit=False)
            group.teacher = teacher
            group.save()
            group.generate_code()
            group.save()
            messages.success(request, f'Grupa "{group.name}" a fost creată cu succes! Cod: {group.code}')
            return redirect('teacher_platform:group_detail', group_id=group.id)
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        form = GroupForm(teacher=teacher)

    context = {
        'form': form,
        'title': 'Adaugă Grupă Nouă'
    }
    return render(request, 'teacher_platform/group_form.html', context)


@login_required
@teacher_required
def group_edit(request, group_id):
    """
    Editează o grupă existentă
    """
    group = get_object_or_404(Group, id=group_id, teacher=request.user)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group, teacher=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupa "{group.name}" a fost actualizată cu succes!')
            return redirect('teacher_platform:group_detail', group_id=group.id)
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        form = GroupForm(instance=group, teacher=request.user)

    context = {
        'form': form,
        'group': group,
        'title': f'Editează Grupa {group.name}'
    }
    return render(request, 'teacher_platform/group_form.html', context)


@login_required
@teacher_required
def student_add(request):
    """
    Adaugă un elev nou
    """
    teacher = request.user
    group_id = request.GET.get('group')
    selected_group = None

    # Verifică dacă există un parametru de grup și dacă profesorul are acces la acel grup
    if group_id:
        try:
            selected_group = Group.objects.get(id=group_id, teacher=teacher, is_active=True)
        except Group.DoesNotExist:
            messages.error(request, 'Grupa selectată nu a fost găsită.')
            return redirect('teacher_platform:groups_list')

    if request.method == 'POST':
        form = StudentForm(request.POST, teacher=teacher)
        if form.is_valid():
            student = form.save()

            # Verifică dacă studentul a fost adăugat într-o grupă
            group_student = GroupStudent.objects.filter(
                student=student,
                group__teacher=teacher
            ).first()

            messages.success(
                request,
                f'Elevul {student.get_full_name()} a fost creat cu succes! '
                f'Username: {student.username}, Parolă: {student.username} (trebuie schimbată la prima autentificare)'
            )

            # Redirect către detalii student după creare
            return redirect('teacher_platform:student_detail', student_id=student.id)
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        # Pre-selectează grupa în formular dacă este furnizată
        initial_data = {}
        if selected_group:
            initial_data['group'] = selected_group
        form = StudentForm(teacher=teacher, initial=initial_data)

    context = {
        'form': form,
        'title': 'Adaugă Elev Nou',
        'selected_group': selected_group
    }
    return render(request, 'teacher_platform/student_form.html', context)


@login_required
@teacher_required
def student_edit(request, student_id):
    """
    Editează informațiile unui elev
    """
    student = get_object_or_404(User, id=student_id, role='student')

    # Verifică dacă profesorul are acces la acest student
    group_student = GroupStudent.objects.filter(
        student=student,
        group__teacher=request.user
    ).first()

    if not group_student:
        messages.error(request, 'Nu aveți acces la acest student.')
        return redirect('teacher_platform:students_list')

    if request.method == 'POST':
        form = EditStudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f'Datele elevului {student.get_full_name()} au fost actualizate cu succes!')
            return redirect('teacher_platform:student_detail', student_id=student.id)
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        form = EditStudentForm(instance=student)

    context = {
        'form': form,
        'student': student,
        'title': f'Editează Elev: {student.get_full_name()}'
    }
    return render(request, 'teacher_platform/student_form.html', context)


@login_required
@teacher_required
def student_reset_password(request, student_id):
    """
    Resetează parola unui elev la valoarea temporară (username-ul lui).
    Elevul va fi obligat să-și aleagă o parolă nouă la următoarea logare.
    """
    if request.method != 'POST':
        return redirect('teacher_platform:student_detail', student_id=student_id)

    student = get_object_or_404(User, id=student_id, role='student')

    has_access = GroupStudent.objects.filter(
        student=student, group__teacher=request.user
    ).exists() or (
        hasattr(student, 'student_profile') and student.student_profile.teacher == request.user
    )
    if not has_access:
        messages.error(request, 'Nu aveți acces la acest student.')
        return redirect('teacher_platform:students_list')

    student.set_password(student.username)
    student.must_change_password = True
    student.save(update_fields=['password', 'must_change_password'])

    messages.success(
        request,
        f'Parola elevului {student.get_full_name()} a fost resetată. '
        f'Username: {student.username}, Parolă temporară: {student.username} '
        f'(va trebui schimbată la prima autentificare).'
    )
    return redirect('teacher_platform:student_detail', student_id=student.id)


@login_required
@teacher_required
def get_modules_for_course(request):
    """
    API endpoint pentru a obține modulele unui curs (pentru AJAX)
    """
    course_id = request.GET.get('course_id')
    if course_id:
        modules = Module.objects.filter(course_id=course_id, is_active=True).values('id', 'title')
        return JsonResponse(list(modules), safe=False)
    return JsonResponse([], safe=False)


@login_required
@teacher_required
def lesson_create(request, group_id=None):
    """
    Creează lecții noi (ad-hoc sau recurente)
    """
    teacher = request.user

    # Dacă e specificat group_id, precompletează grupul
    initial_data = {}
    if group_id:
        group = get_object_or_404(Group, id=group_id, teacher=teacher)
        initial_data['group'] = group
        initial_data['start_time'] = group.start_time
        # Calculează end_time bazat pe durată
        if group.duration_minutes:
            start_datetime = datetime.combine(datetime.today(), group.start_time)
            end_datetime = start_datetime + timedelta(minutes=group.duration_minutes)
            initial_data['end_time'] = end_datetime.time()

    if request.method == 'POST':
        form = LessonForm(request.POST, teacher=teacher)
        if form.is_valid():
            lesson_type = form.cleaned_data['lesson_type']

            if lesson_type == 'single':
                # Creează o singură lecție
                lesson = form.save(commit=False)
                lesson.status = 'scheduled'
                lesson.save()

                messages.success(request, f'Lecția a fost creată cu succes pentru {lesson.date.strftime("%d %B %Y")}!')
                return redirect('teacher_platform:lesson_detail', lesson_id=lesson.id)

            else:  # recurring
                # Creează lecții recurente
                group = form.cleaned_data['group']
                recurrence_count = form.cleaned_data['recurrence_count']
                recurrence_weekday = int(form.cleaned_data['recurrence_weekday'])
                start_date = form.cleaned_data['date']

                # Găsește prima dată care corespunde zilei săptămânii
                days_ahead = recurrence_weekday - start_date.weekday()
                if days_ahead < 0:
                    days_ahead += 7
                first_lesson_date = start_date + timedelta(days=days_ahead)

                # Creează lecțiile
                created_lessons = []
                for i in range(recurrence_count):
                    lesson_date = first_lesson_date + timedelta(weeks=i)

                    # Verifică dacă nu există deja lecție în această dată
                    existing = Lesson.objects.filter(
                        group=group,
                        date=lesson_date,
                        start_time=form.cleaned_data['start_time']
                    ).exists()

                    if not existing:
                        lesson = Lesson.objects.create(
                            group=group,
                            lesson_template=form.cleaned_data.get('lesson_template'),
                            date=lesson_date,
                            start_time=form.cleaned_data['start_time'],
                            end_time=form.cleaned_data.get('end_time'),
                            topic=form.cleaned_data.get('topic', ''),
                            description=form.cleaned_data.get('description', ''),
                            homework=form.cleaned_data.get('homework', ''),
                            teacher_notes=form.cleaned_data.get('teacher_notes', ''),
                            status='scheduled'
                        )
                        created_lessons.append(lesson)

                messages.success(
                    request,
                    f'{len(created_lessons)} lecții au fost create cu succes! '
                    f'Prima lecție: {first_lesson_date.strftime("%d %B %Y")}'
                )
                return redirect('teacher_platform:group_detail', group_id=group.id)
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        form = LessonForm(teacher=teacher, initial=initial_data)

    context = {
        'form': form,
        'title': 'Adaugă Lecție Nouă',
        'group_id': group_id,
    }
    return render(request, 'teacher_platform/lesson_form.html', context)


@login_required
@teacher_required
def mark_attendance(request, lesson_id):
    """
    AJAX endpoint pentru marcarea/actualizarea prezenței
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    lesson = get_object_or_404(
        Lesson.objects.select_related('group'),
        id=lesson_id,
        group__teacher=request.user
    )

    student_id = request.POST.get('student_id')
    is_present = request.POST.get('is_present') == 'true'
    performance_rating = request.POST.get('performance_rating')
    notes = request.POST.get('notes', '')

    if not student_id:
        return JsonResponse({'error': 'Student ID is required'}, status=400)

    student = get_object_or_404(User, id=student_id, role='student')

    # Verifică că studentul e în grupă
    if not GroupStudent.objects.filter(group=lesson.group, student=student, is_active=True).exists():
        return JsonResponse({'error': 'Student not in this group'}, status=400)

    # Creează sau actualizează attendance
    attendance, created = Attendance.objects.update_or_create(
        lesson=lesson,
        student=student,
        defaults={
            'is_present': is_present,
            'notes': notes,
            'performance_rating': int(performance_rating) if performance_rating and performance_rating != '' else None
        }
    )

    # Actualizează contoarele în GroupStudent
    group_student = GroupStudent.objects.get(group=lesson.group, student=student)
    total_lessons = Attendance.objects.filter(
        lesson__group=lesson.group,
        student=student
    ).count()

    attended_lessons = Attendance.objects.filter(
        lesson__group=lesson.group,
        student=student,
        is_present=True
    ).count()

    group_student.lessons_attended = attended_lessons
    group_student.lessons_missed = total_lessons - attended_lessons
    group_student.save()

    return JsonResponse({
        'success': True,
        'created': created,
        'attendance': {
            'is_present': attendance.is_present,
            'performance_rating': attendance.performance_rating,
            'notes': attendance.notes,
        }
    })


@login_required
@teacher_required
def lesson_edit(request, lesson_id):
    """
    Editează o lecție existentă
    """
    lesson = get_object_or_404(
        Lesson.objects.select_related('group'),
        id=lesson_id,
        group__teacher=request.user
    )

    if request.method == 'POST':
        # Pentru editare, folosim doar câmpurile relevante (nu lesson_type)
        form = LessonForm(request.POST, instance=lesson, teacher=request.user)
        # Ignorăm câmpurile de recurență pentru editare
        if form.is_valid():
            form.save()
            messages.success(request, 'Lecția a fost actualizată cu succes!')
            return redirect('teacher_platform:lesson_detail', lesson_id=lesson.id)
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        form = LessonForm(instance=lesson, teacher=request.user)
        # Setează lesson_type la single pentru editare
        form.initial['lesson_type'] = 'single'

    context = {
        'form': form,
        'lesson': lesson,
        'title': f'Editează Lecție: {lesson.date.strftime("%d %B %Y")}',
        'is_edit': True,
    }
    return render(request, 'teacher_platform/lesson_form.html', context)


@login_required
@teacher_required
def teacher_profile(request):
    """
    Vizualizare și editare profil profesor
    """
    teacher = request.user

    # Creează profil dacă nu există
    teacher_profile, created = TeacherProfile.objects.get_or_create(user=teacher)

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, instance=teacher_profile, user=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profilul tău a fost actualizat cu succes!')
            return redirect('teacher_platform:teacher_profile')
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        form = TeacherProfileForm(instance=teacher_profile, user=teacher)

    context = {
        'form': form,
        'teacher': teacher,
        'teacher_profile': teacher_profile,
    }
    return render(request, 'teacher_platform/teacher_profile.html', context)


@login_required
@simulator_access
def simulators_list(request):
    """
    Lista tuturor simulatoarelor disponibile
    """
    simulators = [
        {
            'name': 'Abac Online',
            'description': 'Simulator interactiv de abac pentru învățarea matematicii',
            'icon': '🧮',
            'url': 'teacher_platform:abacus_simulator',
            'color': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        },
        {
            'name': 'Cartonașe Flash',
            'description': 'Învață să recunoști numerele pe soroban prin exerciții interactive',
            'icon': '🎴',
            'url': 'teacher_platform:flashcard_simulator',
            'color': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
        },
        {
            'name': 'Anzan (Calcul Mental)',
            'description': 'Calcul mental rapid cu soroban imaginar',
            'icon': '🧠',
            'url': 'teacher_platform:anzan_simulator',
            'color': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
        },
        {
            'name': 'Exerciții Abac',
            'description': 'Exerciții pe ecran cu răspuns direct în platformă și verificare imediată',
            'icon': '✏️',
            'url': 'teacher_platform:abacus_exercises',
            'color': 'linear-gradient(135deg, #10b981 0%, #34d399 100%)'
        },
        # Aici se vor adăuga alte simulatoare în viitor
    ]

    context = {
        'simulators': simulators,
        **_simulator_context(request),
    }
    return render(request, 'teacher_platform/simulators_list.html', context)


@login_required
@simulator_access
def abacus_simulator(request):
    """
    Simulator interactiv de abac
    """
    return render(request, 'teacher_platform/abacus_simulator.html', _simulator_context(request))


@login_required
@simulator_access
def abacus_exercises(request):
    """
    Exerciții Abac - exerciții tip fișă de lucru rezolvate pe ecran,
    cu răspuns tastat direct și verificare imediată sau la final de set
    """
    return render(request, 'teacher_platform/abacus_exercises.html', _simulator_context(request))


@login_required
@simulator_access
def flashcard_simulator(request):
    """
    Simulator de cartonașe flash pentru recunoașterea numerelor pe soroban
    """
    return render(request, 'teacher_platform/flashcard_simulator.html', _simulator_context(request))


@login_required
@simulator_access
def anzan_simulator(request):
    """
    Simulator Anzan pentru calcul mental rapid cu soroban imaginar
    """
    return render(request, 'teacher_platform/anzan_simulator.html', _simulator_context(request))


# ==================== TEME SIMULATOARE ====================

@login_required
@teacher_required
def simulator_assignment_create(request, group_id):
    """
    Creează o temă pe simulatoare pentru o grupă (sau personalizată
    pentru un elev). Primește JSON:
    { title, start_date, end_date, student_id (opțional),
      tasks: [ { simulator, settings: {...}, target_type, target_value } ] }
    """
    import json

    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST necesar'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'JSON invalid'}, status=400)

    tasks = data.get('tasks') or []
    if not tasks:
        return JsonResponse({'error': 'Tema trebuie să conțină cel puțin o sarcină'}, status=400)
    if not data.get('start_date') or not data.get('end_date'):
        return JsonResponse({'error': 'Perioada temei este obligatorie'}, status=400)

    student = None
    if data.get('student_id'):
        membership = GroupStudent.objects.filter(
            group=group, student_id=data['student_id'], is_active=True
        ).select_related('student').first()
        if not membership:
            return JsonResponse({'error': 'Elevul nu face parte din această grupă'}, status=400)
        student = membership.student

    assignment = SimulatorAssignment.objects.create(
        group=group,
        student=student,
        title=(data.get('title') or 'Temă de casă')[:200],
        start_date=data['start_date'],
        end_date=data['end_date'],
    )

    valid_simulators = dict(SimulatorTask.SIMULATOR_CHOICES)
    for i, t in enumerate(tasks):
        if t.get('simulator') not in valid_simulators:
            continue
        SimulatorTask.objects.create(
            assignment=assignment,
            order=i + 1,
            simulator=t['simulator'],
            settings=t.get('settings') or {},
            target_type=t.get('target_type') if t.get('target_type') in ('count', 'minutes') else 'count',
            target_value=max(1, min(999, int(t.get('target_value') or 5))),
        )

    return JsonResponse({'ok': True, 'assignment_id': assignment.id})


@login_required
@teacher_required
def simulator_assignment_delete(request, assignment_id):
    """Șterge o temă pe simulatoare (doar ale profesorului curent)"""
    assignment = get_object_or_404(
        SimulatorAssignment, id=assignment_id, group__teacher=request.user
    )
    if request.method != 'POST':
        return JsonResponse({'error': 'POST necesar'}, status=405)
    assignment.delete()
    return JsonResponse({'ok': True})


# ==================== LECȚII LIVE ====================

def _live_session_or_404(request, session_id):
    return get_object_or_404(
        LiveSession.objects.select_related('group'),
        id=session_id, group__teacher=request.user
    )


@login_required
@teacher_required
def live_session_start(request, group_id):
    """Pornește (sau returnează) sesiunea live activă a grupei."""
    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST necesar'}, status=405)

    session = LiveSession.objects.filter(group=group, ended_at__isnull=True).first()
    if session is None:
        session = LiveSession.objects.create(group=group, teacher=request.user)
    return JsonResponse({'ok': True, 'session_id': session.id})


@login_required
@teacher_required
def live_session_end(request, session_id):
    """Închide sesiunea live."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST necesar'}, status=405)
    session = _live_session_or_404(request, session_id)
    if session.ended_at is None:
        session.ended_at = timezone.now()
        session.save(update_fields=['ended_at'])
    return JsonResponse({'ok': True})


@login_required
@teacher_required
def live_task_create(request, session_id):
    """
    Adaugă o sarcină în lecția live. JSON:
    { simulator, settings: {...}, target_type, target_value, student_id (opțional) }
    """
    import json
    if request.method != 'POST':
        return JsonResponse({'error': 'POST necesar'}, status=405)
    session = _live_session_or_404(request, session_id)
    if session.ended_at is not None:
        return JsonResponse({'error': 'Sesiunea este închisă'}, status=400)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'JSON invalid'}, status=400)

    if data.get('simulator') not in dict(SimulatorTask.SIMULATOR_CHOICES):
        return JsonResponse({'error': 'Simulator necunoscut'}, status=400)

    student = None
    if data.get('student_id'):
        membership = GroupStudent.objects.filter(
            group=session.group, student_id=data['student_id'], is_active=True
        ).select_related('student').first()
        if not membership:
            return JsonResponse({'error': 'Elevul nu face parte din această grupă'}, status=400)
        student = membership.student

    task = LiveTask.objects.create(
        session=session,
        order=session.tasks.count() + 1,
        student=student,
        simulator=data['simulator'],
        settings=data.get('settings') or {},
        target_type=data.get('target_type') if data.get('target_type') in ('count', 'minutes') else 'count',
        target_value=max(1, min(999, int(data.get('target_value') or 5))),
    )
    return JsonResponse({'ok': True, 'task_id': task.id})


@login_required
@teacher_required
def live_task_delete(request, task_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST necesar'}, status=405)
    task = get_object_or_404(
        LiveTask.objects.select_related('session', 'session__group'),
        id=task_id, session__group__teacher=request.user
    )
    task.delete()
    return JsonResponse({'ok': True})


def _live_state_payload(session):
    """Starea completă a sesiunii live: sarcini, elevi, rezultate, prezență."""
    now = timezone.now()
    tasks = list(session.tasks.select_related('student').order_by('order'))
    results = {
        (r.task_id, r.student_id): r
        for r in LiveTaskResult.objects.filter(task__session=session)
    }
    participants = {
        p.student_id: p for p in session.participants.all()
    }
    roster = [
        gs.student for gs in GroupStudent.objects.filter(
            group=session.group, is_active=True
        ).select_related('student').order_by('student__first_name')
    ]

    sim_names = dict(SimulatorTask.SIMULATOR_CHOICES)
    tasks_json = [{
        'id': t.id,
        'order': t.order,
        'simulator': t.simulator,
        'simulator_name': sim_names.get(t.simulator, t.simulator),
        'target': t.get_target_display(),
        'student_id': t.student_id,
        'student_name': t.student.get_full_name() if t.student else None,
        'settings': t.settings,
    } for t in tasks]

    students_json = []
    for st in roster:
        p = participants.get(st.id)
        connected = bool(p and (now - p.last_seen).total_seconds() < 30)
        cells = []
        for t in tasks:
            if t.student_id and t.student_id != st.id:
                cells.append(None)  # sarcină individuală a altui elev
                continue
            r = results.get((t.id, st.id))
            if r is None:
                cells.append({'status': 'none'})
            else:
                if t.target_type == 'minutes':
                    percent = min(100, round(r.time_spent_seconds / (t.target_value * 60) * 100)) if t.target_value else 0
                else:
                    percent = min(100, round(r.completed_exercises / t.target_value * 100)) if t.target_value else 0
                cells.append({
                    'status': 'done' if r.completed else 'working',
                    'exercises': r.completed_exercises,
                    'correct': r.correct,
                    'incorrect': r.incorrect,
                    'time_display': '%d:%02d' % divmod(r.time_spent_seconds, 60),
                    'percent': 100 if r.completed else percent,
                })
        students_json.append({
            'id': st.id,
            'name': st.get_full_name() or st.username,
            'connected': connected,
            'cells': cells,
        })

    return {
        'session_id': session.id,
        'active': session.is_active,
        'started_at': session.started_at.strftime('%H:%M'),
        'tasks': tasks_json,
        'students': students_json,
    }


@login_required
@teacher_required
def live_state(request, group_id):
    """Polling profesor: starea sesiunii live active a grupei."""
    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    session = LiveSession.objects.filter(group=group, ended_at__isnull=True).first()
    if session is None:
        return JsonResponse({'ok': True, 'active': False})
    return JsonResponse({'ok': True, **_live_state_payload(session)})
