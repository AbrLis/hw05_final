from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    group, post, user = (None, None, None)
    TEXT_POST = "qwertyuiopasdfgh"
    LEN_POST_STR = 15

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username="auth", email="test@example.com", password="test"
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(author=cls.user, text=cls.TEXT_POST)

    def test_models_correct_object_name(self):
        """Проверяем, что у моделей корректно работает __str__."""
        name_post = str(self.post)
        name_group = str(self.group)
        self.assertEqual(
            name_post,
            self.TEXT_POST[: self.LEN_POST_STR],
            "Ошибка вывода str.post",
        )
        self.assertEqual(
            name_group,
            "Тестовая группа",
            "Ошибка вывода str.group",
        )

    def test_models_verbose_name(self):
        """Проверка verbose_name моделей"""
        fields_verbose_name = {
            "text": "Текст поста.",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
            "image": "Картинка",
        }
        for field, value in fields_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name,
                    value,
                )

    def test_models_help_text(self):
        """Проверка help_text моделей"""
        fields_help_text = {
            "text": "Введите не меньше 10 символов, а лучше хороший лонгрид.",
            "group": "Название группы.",
            "image": "Выберите картинку, если хотите.",
        }
        for field, value in fields_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text, value
                )
