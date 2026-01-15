from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Group, GroupStudent, Lesson, Attendance, Assignment, AssignmentSubmission, LessonNote
from accounts.models import User, StudentProfile
from courses.models import Module, LessonTemplate
from .forms import GroupForm, StudentForm, EditStudentForm


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

    # Șabloane de lecții disponibile din modulul grupei
    lesson_templates = []
    if group.module:
        lesson_templates = LessonTemplate.objects.filter(
            module=group.module,
            is_active=True
        ).order_by('order')

    context = {
        'group': group,
        'students': students,
        'upcoming_lessons': upcoming_lessons,
        'past_lessons': past_lessons,
        'assignments': assignments,
        'lesson_templates': lesson_templates,
    }

    return render(request, 'teacher_platform/group_detail.html', context)


@login_required
@teacher_required
def calendar_view(request):
    """
    Calendar cu toate lecțiile profesorului
    """
    teacher = request.user

    # Obține luna și anul din query params sau folosește luna curentă
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))

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

    students_query = GroupStudent.objects.filter(
        group__teacher=teacher,
        is_active=True
    ).select_related('student', 'student__student_profile', 'group')

    if group_filter:
        students_query = students_query.filter(group_id=group_filter)

    students = students_query.order_by('student__first_name', 'student__last_name')

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

    # Verifică dacă profesorul are acces la acest student
    group_student = GroupStudent.objects.filter(
        student=student,
        group__teacher=request.user
    ).first()

    if not group_student:
        messages.error(request, 'Nu aveți acces la acest student.')
        return redirect('teacher_platform:students_list')

    # Grupele studentului
    student_groups = GroupStudent.objects.filter(
        student=student,
        is_active=True
    ).select_related('group', 'group__course', 'group__module')

    # Prezențe
    attendances = Attendance.objects.filter(
        student=student,
        lesson__group__teacher=request.user
    ).select_related('lesson', 'lesson__group').order_by('-lesson__date')[:20]

    # Teme predate
    submissions = AssignmentSubmission.objects.filter(
        student=student,
        assignment__group__teacher=request.user
    ).select_related('assignment', 'assignment__group').order_by('-submitted_at')[:20]

    # Statistici
    total_lessons = attendances.count()
    present_count = attendances.filter(is_present=True).count()
    attendance_rate = round((present_count / total_lessons * 100), 2) if total_lessons > 0 else 0

    avg_performance = attendances.filter(
        performance_rating__isnull=False
    ).aggregate(Avg('performance_rating'))['performance_rating__avg']

    context = {
        'student': student,
        'group_student': group_student,
        'student_groups': student_groups,
        'attendances': attendances,
        'submissions': submissions,
        'attendance_rate': attendance_rate,
        'avg_performance': round(avg_performance, 2) if avg_performance else None,
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
    Lista tuturor temelor create de profesor
    """
    teacher = request.user

    # Filtrare
    status_filter = request.GET.get('status', 'all')
    group_filter = request.GET.get('group', '')

    assignments_query = Assignment.objects.filter(
        group__teacher=teacher
    ).select_related('group').prefetch_related('submissions')

    if group_filter:
        assignments_query = assignments_query.filter(group_id=group_filter)

    today = timezone.now().date()

    if status_filter == 'upcoming':
        assignments_query = assignments_query.filter(due_date__gte=today)
    elif status_filter == 'past':
        assignments_query = assignments_query.filter(due_date__lt=today)

    assignments = assignments_query.order_by('-due_date')

    # Grupele pentru filtru
    groups = Group.objects.filter(
        teacher=teacher,
        is_active=True
    ).order_by('name')

    context = {
        'assignments': assignments,
        'groups': groups,
        'status_filter': status_filter,
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

            # Redirect către detalii doar dacă studentul e în grupă, altfel către lista de studenți
            if group_student:
                return redirect('teacher_platform:student_detail', student_id=student.id)
            else:
                return redirect('teacher_platform:students_list')
        else:
            messages.error(request, 'Te rog corectează erorile din formular.')
    else:
        form = StudentForm(teacher=teacher)

    context = {
        'form': form,
        'title': 'Adaugă Elev Nou'
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
def get_modules_for_course(request):
    """
    API endpoint pentru a obține modulele unui curs (pentru AJAX)
    """
    course_id = request.GET.get('course_id')
    if course_id:
        modules = Module.objects.filter(course_id=course_id, is_active=True).values('id', 'title')
        return JsonResponse(list(modules), safe=False)
    return JsonResponse([], safe=False)
