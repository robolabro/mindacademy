from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import redirect, render


def _role_home(user):
    """Pagina de start potrivită rolului utilizatorului."""
    if user.role == 'student':
        return 'student_platform:my_assignments'
    if user.role == 'teacher':
        return 'teacher_platform:dashboard'
    return 'home'


@login_required
def post_login_redirect(request):
    """După login, fiecare rol ajunge pe platforma lui."""
    return redirect(_role_home(request.user))


@login_required
def force_password_change(request):
    """
    Schimbarea obligatorie a parolei temporare (prima autentificare).
    Middleware-ul ForcePasswordChange trimite aici utilizatorii cu
    `must_change_password` până își setează o parolă proprie.
    """
    user = request.user
    if not user.must_change_password:
        return redirect(_role_home(user))

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])
            update_session_auth_hash(request, user)
            messages.success(request, 'Parola a fost schimbată. Bine ai venit!')
            return redirect(_role_home(user))
    else:
        form = SetPasswordForm(user)

    return render(request, 'registration/force_password_change.html', {'form': form})
