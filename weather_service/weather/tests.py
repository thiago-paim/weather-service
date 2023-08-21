import datetime
import pytz
from copy import copy
from django.test import TestCase, override_settings
from requests.exceptions import RequestException
from requests.models import Response
from rest_framework.test import APIClient
from unittest.mock import patch, Mock

from weather.models import WeatherRequest
from weather.values import created_weather_request_cities

mocked_datetime = datetime.datetime(2023, 8, 20, 1, 20, 30, tzinfo=pytz.utc)


class CreateWeatherRequestViewTest(TestCase):
    def setUp(self):
        self.url = "/weather/"

    @patch("django.utils.timezone.now")
    def test_create_weather_request_success(self, datetime_mock):
        datetime_mock.return_value = mocked_datetime

        client = APIClient()
        response = client.post(
            self.url,
            {"user_id": "1"},
        )

        self.assertEqual(response.status_code, 201)

        req = WeatherRequest.objects.last()
        self.assertEqual(req.pk, 1)
        self.assertEqual(req.user_id, "1")
        self.assertEqual(req.date, mocked_datetime)
        self.assertEqual(
            req.cities,
            created_weather_request_cities,
        )

    def test_repeated_user_id(self):
        WeatherRequest.objects.create(
            user_id="1", cities=created_weather_request_cities
        )

        client = APIClient()
        response = client.post(
            self.url,
            {"user_id": "1"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"user_id": ["weather request with this user id already exists."]},
        )

    def test_invalid_user_id(self):
        client = APIClient()
        response = client.post(
            self.url,
            {"user_id": "super_long_user_id"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"user_id": ["Ensure this field has no more than 8 characters."]},
        )


class GetWeatherRequestViewTest(TestCase):
    def setUp(self):
        self.url = "/weather"

    def test_get_created_weather_request(self):
        ...

    def test_get_finished_weather_request(self):
        ...

    def test_empty_user_id(self):
        ...

    def test_invalid_user_id(self):
        ...
