from http import HTTPStatus

from django.test import TestCase
from rest_framework.test import APIClient


class RecipesAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_exists(self):
        """Проверка доступности рецептов."""
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
