from django.test import TestCase, Client
from django.urls import reverse

from posts.models import User


class TestUrl(TestCase):
    urls = {
        "/auth/reset/done/": "users/password_reset_complete.html",
        "/auth/password_reset/done/": "users/password_reset_done.html",
        "/auth/password_reset/": "users/password_reset_form.html",
        "/auth/password_change/done/": "users/password_change_done.html",
        "/auth/password_change/": "users/password_change_form.html",
        "/auth/login/": "users/login.html",
        "/auth/signup/": "users/signup.html",
        "/auth/logout/": "users/logged_out.html",
    }
    namespace = {
        "users:password_reset_complete": "users/password_reset_complete.html",
        "users:password_reset_done": "users/password_reset_done.html",
        "users:password_reset_form": "users/password_reset_form.html",
        "users:password_change_done": "users/password_change_done.html",
        "users:password_change": "users/password_change_form.html",
        "users:login": "users/login.html",
        "users:signup": "users/signup.html",
        "users:logout": "users/logged_out.html",
    }

    def setUp(self):
        self.client_login = Client()
        user = User.objects.create(username="user", password="password")
        self.client_login.force_login(user)

    def test_page_open(self):
        """Проверка корректного открытия страницы"""
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client_login.get(url)
                self.assertEqual(response.status_code, 200)

    def test_namespaces_open(self):
        """Проверка работы namespace"""
        for name, url in self.namespace.items():
            with self.subTest(name=name):
                response = self.client_login.get(reverse(name))
                self.assertTemplateUsed(response, url)

    def test_form_signup(self):
        """Проверка формы signup"""
        template = "users:signup"
        response = self.client_login.get(reverse(template))
        form = response.context.get("form").fields
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertTrue(form.get(field))
