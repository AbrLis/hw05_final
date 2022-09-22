from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class TestForm(TestCase):
    def test_signup_create_new_user(self):
        """Проверка создания нового пользователя"""
        template = "users:signup"
        form = {
            "first_name": "user",
            "last_name": "user",
            "username": "user",
            "email": "user@example.com",
            "password1": "password8888",
            "password2": "password8888",
        }
        response = self.client.post(reverse(template), data=form, follow=True)
        self.assertRedirects(response, "/")
        user = User.objects.filter(username="user", email="user@example.com")
        self.assertEqual(user.count(), 1)
