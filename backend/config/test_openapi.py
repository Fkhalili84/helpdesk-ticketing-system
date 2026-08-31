from django.test import TestCase
from django.urls import reverse

from rest_framework import status


class OpenAPITests(TestCase):

    def test_openapi_schema_is_available(self):
        response = self.client.get(
            reverse("schema")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_swagger_ui_is_available(self):
        response = self.client.get(
            reverse("swagger-ui")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_redoc_is_available(self):
        response = self.client.get(
            reverse("redoc")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )