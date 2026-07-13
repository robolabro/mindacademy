from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def post_login_redirect(request):
    """După login, fiecare rol ajunge pe platforma lui."""
    if request.user.role == 'student':
        return redirect('student_platform:my_assignments')
    if request.user.role == 'teacher':
        return redirect('teacher_platform:dashboard')
    return redirect('home')
