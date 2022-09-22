from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
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

    def setUp(self):
        cache.clear()
        self.post = Post.objects.create(
            author=self.user,
            text="TestText-1234567890",
            group=self.group,
        )
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

        self.template_urls_all = {
            "": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.user}/": "posts/profile.html",
            f"/posts/{self.post.pk}/": "posts/post_detail.html",
        }
        self.template_urls_auth = {
            f"/posts/{self.post.pk}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }
        self.template_urls_redirect = {
            "/create/": "/auth/login/?next=/create/",
            f"/posts/{self.post.pk}/edit/": f"/posts/{self.post.pk}/",
        }

    def test_page_posts_auth(self):
        """Проверка авторизированного пользователя"""
        self.template_urls_auth.update(self.template_urls_all)
        for url, templ_url in self.template_urls_auth.items():
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, templ_url)

    def test_page_edit_not_author(self):
        """Проверка на перенаправление если пытается редактировать не автор"""
        not_author_user = User.objects.create(
            username="masha",
            email="masha@example.com",
            password="password",
        )
        auth_client_masha = Client()
        auth_client_masha.force_login(not_author_user)
        response_masha = auth_client_masha.get(
            f"/posts/{self.post.pk}/edit", follow=True
        )
        self.assertRedirects(
            response_masha,
            f"/posts/{self.post.pk}/",
            status_code=HTTPStatus.MOVED_PERMANENTLY,
        )

    def test_page_guest(self):
        """Проверка от лица неавторизированного пользователя"""
        for url, templ_url in self.template_urls_all.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, templ_url)

    def test_page_redirect(self):
        """
        Проверка редиректа при попытке редактирования или создания поста
        неавторизированным пользователем
        """
        for url, code in self.template_urls_redirect.items():
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, code)
