import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestFormPost(TestCase):
    user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="vasya")
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.group = Group.objects.create(
            title="Тестовая группа", slug="test-slug", description="Описание"
        )
        Post.objects.create(text="Пост существует...........", author=cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth = Client()
        self.auth.force_login(self.user)

    def test_send_valid_form_create(self):
        """Отправка валидной формы и проверка результата"""
        image = SimpleUploadedFile(
            name="test.gif",
            content=self.small_gif,
            content_type="image/gif",
        )
        post_count = Post.objects.count()
        form = {
            "text": "Пост создал Вася!",
            "group": self.group.id,
            "image": image,
        }
        response = self.auth.post(
            reverse("posts:post_create"), data=form, follow=True
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username}),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.fields_test_helper(form, "posts/test.gif")

    def test_send_valid_form_edit(self):
        """Проверка изменения поста"""
        image = SimpleUploadedFile(
            name="test2.gif",
            content=self.small_gif,
            content_type="image/gif",
        )
        form = {
            "text": "А вот и не Вася!",
            "group": self.group.id,
            "image": image,
        }
        response = self.auth.post(
            reverse("posts:post_edit", kwargs={"post_id": 1}),
            data=form,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": 1})
        )
        self.fields_test_helper(form, "posts/test2.gif")

    def fields_test_helper(self, form, image_field):
        """Проверка всех полей поста"""
        self.assertTrue(
            Post.objects.filter(
                text=form["text"],
                author=self.user,
                group=form["group"],
                image=image_field,
            ).exists()
        )

    def test_validate_post(self):
        """Проверка валидации создания поста"""
        form = {"text": "Пост"}
        response = self.auth.post(
            reverse("posts:post_create"), data=form, follow=True
        )
        form = response.context.get("form")
        self.assertEqual(form.errors["text"][0], "Не меньше 10 символов.")

    def _test_form_comment(self):
        """Проверка, что на странице присутствует форма комментария"""
        response = self.auth.get(
            reverse("posts:post_detail", kwargs={"post_id": 1})
        )
        self.assertTrue(response.context["form"].fields["text"])

    def test_send_valid_form_comment(self):
        """Отправка валидной формы комментария и проверка результата"""
        form = {"text": "Комментарий"}
        response = self.auth.post(
            reverse("posts:add_comment", kwargs={"post_id": 1}),
            data=form,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": 1})
        )
        self.assertTrue(
            Post.objects.filter(
                pk=1, comments__text=form["text"], comments__author=self.user
            ).exists()
        )
