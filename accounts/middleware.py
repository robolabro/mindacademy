from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    Utilizatorii cu `must_change_password` (ex. elevi cu parolă temporară
    setată de profesor) sunt redirecționați către pagina de schimbare a
    parolei până când și-o setează.
    """

    EXEMPT_PREFIXES = ('/static/', '/media/', '/admin/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and getattr(user, 'must_change_password', False):
            change_url = reverse('force_password_change')
            logout_url = reverse('logout')
            path = request.path
            if (path not in (change_url, logout_url)
                    and not path.startswith(self.EXEMPT_PREFIXES)):
                return redirect('force_password_change')
        return self.get_response(request)
