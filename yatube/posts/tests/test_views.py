import shutil
from http import HTTPStatus

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import QuerySet
from django.db.models.fields.files import ImageFieldFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User
from .test_forms import TEMP_MEDIA_ROOT


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    COUNT_POST = 15
    COUNT_ON_PAGE = 10
    user, group = (None, None)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Bear-group",
            slug="bear",
            description="TestBear group",
        )
        cls.user = User.objects.create(
            username="vasya",
            email="guest@example.com",
            password="password",
        )
        cls.user2 = User.objects.create(
            username="petya",
            email="2@2.com",
            password="password",
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text=f"TestText-1234567890 {count} post",
                    group=cls.group,
                    image=SimpleUploadedFile(
                        name="small.gif",
                        content=small_gif,
                        content_type="image/gif",
                    ),
                )
                for count in range(cls.COUNT_POST)
            ]
        )
        cls.post = Post.objects.get(pk=cls.COUNT_POST)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client2 = Client()
        self.auth_client.force_login(self.user)
        self.auth_client2.force_login(self.user2)
        cache.clear()

    def test_following(self):
        """Проверка возможности подписки авторизированными пользователями"""
        self.auth_client.get(
            reverse("posts:profile_follow", kwargs={"username": self.user2})
        )
        self.assertTrue(self.user.follower.filter(user=self.user).exists())

    def test_unfollow(self):
        """Проверка возможности отписки от автора"""
        self.auth_client.get(
            reverse("posts:profile_follow", kwargs={"username": self.user2})
        )
        self.auth_client.get(
            reverse("posts:profile_unfollow", kwargs={"username": self.user2})
        )
        self.assertFalse(self.user.follower.filter(user=self.user).exists())

    def test_list_follow(self):
        """Проверка изменения количества записей листа подписок при
        добавлении нового поста"""
        self.auth_client.get(
            reverse("posts:profile_follow", kwargs={"username": self.user2})
        )
        # Проверка на то что лента подписок пуста
        response = self.auth_client.get(reverse("posts:follow_index"))
        self.assertEqual(response.context["paginator"].count, 0)
        self.auth_client2.post(
            reverse("posts:post_create"),
            data={
                "text": "Новый пост",
                "group": self.group.pk,
            },
            follow=True,
        )
        # Проверка на то что в ленте появился пост
        response = self.auth_client.get(reverse("posts:follow_index"))
        self.assertEqual(response.context["paginator"].count, 1)

    def test_pages_correct_template(self):
        """Проверка корректности темплейтов"""
        template = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": self.user.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post.pk}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": self.post.pk}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        for reverse_name, template in template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_helper(self, template, kwargs=None):
        """Повторяющийся код сведён в эту функцию"""
        kwargs = kwargs or {}
        response = self.auth_client.get(reverse(template, kwargs=kwargs))
        # ожидаемый тип данных
        self.assertEqual(type(response.context.get("posts")), QuerySet)
        # количество постов на странице
        self.assertEqual(
            response.context["object_list"].count(), self.COUNT_ON_PAGE
        )
        # проверка 2ой страницы на количество постов
        response = self.auth_client.get(
            reverse(template, kwargs=kwargs), {"page": 2}
        )
        self.assertEqual(
            response.context["object_list"].count(),
            self.COUNT_POST - self.COUNT_ON_PAGE,
        )
        for posts in response.context["object_list"]:
            group = posts.group
            # проверка, что все посты соответствуют группе
            with self.subTest(group_on_page=group):
                self.assertEqual(group, self.group)
            # проверка, что все посты соответствуют автору
            author_on_page = posts.author
            with self.subTest(author_on_page=author_on_page):
                self.assertEqual(author_on_page, self.user)
            # проверка поля image
            self.assertEqual(
                type(response.context["post"].image), ImageFieldFile
            )

    def test_index_correct_context(self):
        """Проверка контекста главной страницы"""
        self.check_helper("posts:index")

    def test_group_list_context(self):
        """Проверка контекста страницы списка групп"""
        self.check_helper("posts:group_list", {"slug": self.group.slug})

    def test_profile_context(self):
        """Проверка контекста страницы профиля автора"""
        self.check_helper("posts:profile", {"username": self.user.username})

    def test_post_detail(self):
        """Проверка вывода страницы одного поста"""
        posts = self.auth_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk})
        ).context.get("posts")
        # ожидаемый тип данных
        self.assertEqual(type(posts), Post)
        # id соответствует запрошеному
        self.assertEqual(posts.pk, self.post.pk)
        # присутствует картинка
        self.assertEqual(type(posts.image), ImageFieldFile)

    def check_form_helper(self, template, kwargs=None):
        """Общий код проверки форм"""
        count_fields = 3
        kwargs = kwargs or {}
        response = self.auth_client.get(reverse(template), kwarg=kwargs)
        form = response.context.get("form").fields
        # форма соответствует ожидаемой
        self.assertEqual(len(form), count_fields)

    def test_post_create(self):
        """Проверка создания поста"""
        self.check_form_helper("posts:post_create")

    def test_post_edit(self):
        """Проверка редактирования поста"""
        self.check_form_helper("posts:post_create", {"post_id": self.post.pk})

    def test_comment_add_no_author(self):
        """Проверка, что незалогиненный пользователь не может комментировать"""
        response = self.client.get(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            {"text": "test_comment"},
            follow=True,
        )
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next='
            f'{reverse("posts:add_comment", kwargs={"post_id": self.post.pk})}'
            f"?text=test_comment",
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
        )

    def test_comment_send(self):
        """После успешной отправки комментарий появляется на странице поста."""
        response = self.auth_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            {"text": "test_comment"},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
        )
        self.assertEqual(response.context["posts"].comments.count(), 1)
        self.assertEqual(
            response.context["posts"].comments.first().text, "test_comment"
        )

    def test_cache_index(self):
        """Проверка кэширования главной страницы"""
        response = self.auth_client.get(reverse("posts:index"))
        self.assertContains(response, self.post.text)
        self.post.text = "new text"
        self.post.save()
        response = self.auth_client.get(reverse("posts:index"))
        self.assertNotContains(response, self.post.text)
