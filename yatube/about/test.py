from django.test import TestCase


class TestStaticUrl(TestCase):
    urls = {
        "/about/author/": "about/author.html",
        "/about/tech/": "about/tech.html",
    }

    def test_static_page(self):
        """Проверка корректного открытия страницы"""
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_template_page(self):
        """Проверка соответствия темплейтов"""
        for template, urls in self.urls.items():
            with self.subTest(template=template):
                response = self.client.get(template)
                self.assertTemplateUsed(response, urls)
