import datetime
import pytz
from copy import copy
from django.test import TestCase
from requests.exceptions import HTTPError
from requests.models import Response
from rest_framework.test import APIClient
from unittest.mock import patch, Mock

from weather.clients import open_weather_cli
from weather.models import WeatherRequest
from weather.values import (
    created_weather_request_cities,
    open_weather_success_mock,
    open_weather_invalid_api_key_mock,
    open_weather_city_not_found_mock,
)

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


class OpenWeatherClientTest(TestCase):
    def setUp(self):
        self.success_mock = Mock(spec=Response)
        self.success_mock.json.return_value = copy(open_weather_success_mock)
        self.success_mock.status_code = 200

        self.invalid_api_key_mock = Mock(spec=Response)
        self.invalid_api_key_mock.raise_for_status.side_effect = HTTPError(
            open_weather_invalid_api_key_mock
        )

        self.city_not_found_mock = Mock(spec=Response)
        self.city_not_found_mock.raise_for_status.side_effect = HTTPError(
            open_weather_city_not_found_mock
        )

    @patch("weather.clients.requests.request")
    def test_request_success(self, client_mock):
        client_mock.return_value = self.success_mock

        response = open_weather_cli.get("city_id")
        self.assertEqual(response, open_weather_success_mock)

    @patch("weather.clients.requests.request")
    def test_invalid_api_key(self, client_mock):
        client_mock.return_value = self.invalid_api_key_mock

        with self.assertRaises(HTTPError) as e:
            open_weather_cli.get("city_id")

        self.assertEqual(str(e.exception), str(open_weather_invalid_api_key_mock))

    @patch("weather.clients.requests.request")
    def test_city_not_found(self, client_mock):
        client_mock.return_value = self.city_not_found_mock

        with self.assertRaises(HTTPError) as e:
            open_weather_cli.get("city_id")

        self.assertEqual(str(e.exception), str(open_weather_city_not_found_mock))
