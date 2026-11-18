"""
Login în producție: browserul e pe https://mindacademy.ro, iar Railway termină
HTTPS-ul în fața aplicației — cererea ajunge la Django pe http, cu antetul
X-Forwarded-Proto: https.

Regresie: login-ul pica cu „Verificarea CSRF nereușită" (403) când variabila
CSRF_TRUSTED_ORIGINS din Railway lipsea sau era greșită, pentru că Django nu
recunoștea proxy-ul și compara originea „https://…" cu „http://…".

Rulare:
    python manage.py test accounts
"""
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User


@override_settings(ALLOWED_HOSTS=['mindacademy.ro', 'www.mindacademy.ro'],
                   CSRF_COOKIE_SECURE=False)
class LoginInProductieTests(TestCase):

    def setUp(self):
        User.objects.create_user(username='prof', password='Test1234!', role='teacher')
        # Clientul verifică CSRF ca un browser real (implicit testele îl sar).
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST='mindacademy.ro')
        self.url = reverse('login')

    def _post_login(self, **headers):
        self.client.get(self.url, **headers)
        token = self.client.cookies['csrftoken'].value
        return self.client.post(
            self.url,
            {'username': 'prof', 'password': 'Test1234!', 'csrfmiddlewaretoken': token},
            **headers)

    def test_login_prin_proxy_https(self):
        """Exact cererea din producție: https la browser, http + antet la Django."""
        resp = self._post_login(HTTP_ORIGIN='https://mindacademy.ro',
                                HTTP_X_FORWARDED_PROTO='https')
        self.assertNotEqual(resp.status_code, 403)
        self.assertEqual(resp.status_code, 302)   # autentificat → redirect

    @override_settings(CSRF_TRUSTED_ORIGINS=[])
    def test_merge_si_fara_variabila_din_railway(self):
        """Dacă CSRF_TRUSTED_ORIGINS se pierde, proxy-ul recunoscut ajunge."""
        resp = self._post_login(HTTP_ORIGIN='https://mindacademy.ro',
                                HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(resp.status_code, 302)

    def test_domeniul_public_e_mereu_de_incredere(self):
        from django.conf import settings
        self.assertIn('https://mindacademy.ro', settings.CSRF_TRUSTED_ORIGINS)
        self.assertIn('https://www.mindacademy.ro', settings.CSRF_TRUSTED_ORIGINS)

    def test_alt_site_ramane_respins(self):
        """Protecția CSRF rămâne activă pentru originile străine."""
        resp = self._post_login(HTTP_ORIGIN='https://site-strain.example',
                                HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(resp.status_code, 403)
