from http import HTTPStatus

from django.test import TestCase


class Test404(TestCase):
    def test_404(self):
        response = self.client.get("/404/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "core/404.html")
