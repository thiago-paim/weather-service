import datetime
import pytz
from copy import copy
from django.test import TestCase
from requests.exceptions import HTTPError
from requests.models import Response
from rest_framework.test import APIClient
from unittest.mock import patch, Mock, call

from weather.clients import open_weather_cli
from weather.models import WeatherRequest
from weather.tasks import get_city_weather
from weather import mocks

mocked_datetime = datetime.datetime(2023, 8, 20, 1, 20, 30, tzinfo=pytz.utc)


class WeatherRequestTest(TestCase):
    @patch("weather.tasks.get_city_weather.delay")
    def test_create_open_weather_tasks(self, task_mock):
        req = WeatherRequest.objects.create(
            user_id="1",
            cities=[
                {"city_id": "3439525"},
                {"city_id": "3439781"},
            ],
        )

        req.create_open_weather_tasks()
        calls = [
            call("3439525", req.id),
            call("3439781", req.id),
        ]
        task_mock.assert_has_calls(calls)

    @patch("weather.tasks.get_city_weather.delay")
    def test_empty_cities_create_open_weather_tasks(self, task_mock):
        req = WeatherRequest.objects.create(
            user_id="0",
            cities=[],
        )

        req.create_open_weather_tasks()
        task_mock.assert_not_called()

    def test_new_req_progress(self):
        req = WeatherRequest.objects.create(
            user_id="1",
            cities=[
                {"city_id": "3439525"},
                {"city_id": "3439781"},
            ],
        )
        self.assertEqual(req.progress(), "0%")

    def test_incomplete_req_progress(self):
        req = WeatherRequest.objects.create(
            user_id="2",
            cities=[
                {"city_id": "3439525"},
                {"temp": 285.89, "city_id": "3439781", "humidity": 94},
                {"temp": 288.28, "city_id": "3440645", "humidity": 95},
            ],
        )
        self.assertEqual(req.progress(), "67%")

    def test_complete_req_progress(self):
        req = WeatherRequest.objects.create(
            user_id="3",
            cities=[
                {"city_id": "3439525", "temp": 289.99, "humidity": 88},
                {"city_id": "3439781", "temp": 285.89, "humidity": 94},
                {"city_id": "3440645", "temp": 288.28, "humidity": 95},
            ],
        )

        self.assertEqual(req.progress(), "100%")

    def test_empty_cities_req_progress(self):
        req = WeatherRequest.objects.create(
            user_id="0",
            cities=[],
        )

        self.assertEqual(req.progress(), "0%")


class CreateWeatherRequestViewTest(TestCase):
    def setUp(self):
        self.url = "/weather/cities"
        self.client = APIClient()

    @patch("django.utils.timezone.now")
    @patch("weather.models.WeatherRequest.create_open_weather_tasks")
    def test_create_weather_request_success(self, create_tasks_mock, datetime_mock):
        datetime_mock.return_value = mocked_datetime

        response = self.client.post(
            self.url,
            {"user_id": "1"},
        )
        self.assertEqual(response.status_code, 201)

        req = WeatherRequest.objects.last()
        self.assertEqual(req.user_id, "1")
        self.assertEqual(req.date, mocked_datetime)
        self.assertEqual(
            req.cities,
            mocks.default_weather_request_cities_json,
        )

        create_tasks_mock.assert_called_once()

    @patch("weather.models.WeatherRequest.create_open_weather_tasks")
    def test_repeated_user_id(self, create_tasks_mock):
        WeatherRequest.objects.create(
            user_id="1", cities=mocks.default_weather_request_cities_json
        )

        response = self.client.post(
            self.url,
            {"user_id": "1"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"user_id": ["weather request with this user id already exists."]},
        )

        create_tasks_mock.assert_not_called()

    @patch("weather.models.WeatherRequest.create_open_weather_tasks")
    def test_invalid_user_id(self, create_tasks_mock):
        response = self.client.post(
            self.url,
            {"user_id": "super_long_user_id"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"user_id": ["Ensure this field has no more than 8 characters."]},
        )

        create_tasks_mock.assert_not_called()


class GetWeatherRequestViewTest(TestCase):
    def setUp(self):
        self.url = "/weather/progress"
        self.client = APIClient()

    def test_new_weather_request(self):
        req = WeatherRequest.objects.create(
            user_id="1",
            cities=[
                {"city_id": "3439525"},
                {"city_id": "3439781"},
            ],
        )

        response = self.client.get(
            self.url,
            {"user_id": req.user_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"progress": "0%"})

    def test_incomplete_weather_request(self):
        req = WeatherRequest.objects.create(
            user_id="2",
            cities=[
                {"city_id": "3439525"},
                {"temp": 285.89, "city_id": "3439781", "humidity": 94},
                {"temp": 288.28, "city_id": "3440645", "humidity": 95},
            ],
        )

        response = self.client.get(
            self.url,
            {"user_id": req.user_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"progress": "67%"})

    def test_complete_weather_request(self):
        req = WeatherRequest.objects.create(
            user_id="3",
            cities=[
                {"city_id": "3439525", "temp": 289.99, "humidity": 88},
                {"city_id": "3439781", "temp": 285.89, "humidity": 94},
                {"city_id": "3440645", "temp": 288.28, "humidity": 95},
            ],
        )

        response = self.client.get(
            self.url,
            {"user_id": req.user_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"progress": "100%"})

    def test_empty_user_id(self):
        response = self.client.get(
            self.url,
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not found."})

    def test_user_id_not_found(self):
        response = self.client.get(
            self.url,
            {"user_id": "NON_EXISTING_USER_ID"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Not found."})


class OpenWeatherClientTest(TestCase):
    @patch("weather.clients.requests.request")
    def test_request_success(self, client_mock):
        client_mock.return_value = mocks.open_weather_success_mock

        response = open_weather_cli.get("city_id")
        self.assertEqual(response, mocks.open_weather_success_response)

    @patch("weather.clients.requests.request")
    def test_invalid_api_key(self, client_mock):
        client_mock.return_value = mocks.open_weather_invalid_api_key_mock

        with self.assertRaises(HTTPError) as e:
            open_weather_cli.get("city_id")

        self.assertEqual(
            str(e.exception), str(mocks.open_weather_invalid_api_key_response)
        )

    @patch("weather.clients.requests.request")
    def test_city_not_found(self, client_mock):
        client_mock.return_value = mocks.open_weather_city_not_found_mock

        with self.assertRaises(HTTPError) as e:
            open_weather_cli.get("city_id")

        self.assertEqual(
            str(e.exception), str(mocks.open_weather_city_not_found_response)
        )

    @patch("weather.clients.requests.request")
    def test_rate_limit(self, client_mock):
        client_mock.return_value = mocks.open_weather_rate_limit_mock

        with self.assertRaises(HTTPError) as e:
            open_weather_cli.get("city_id")

        self.assertEqual(str(e.exception), str(mocks.open_weather_rate_limit_response))


class CityWeatherTaskTest(TestCase):
    def setUp(self):
        self.req = WeatherRequest.objects.create(
            user_id="1",
            cities=[
                {"city_id": "3439525"},
                {"city_id": "3439781"},
            ],
        )

    @patch("weather.clients.OpenWeatherClient.get")
    def test_city_weather_success(self, client_mock):
        client_mock.return_value = copy(mocks.open_weather_success_response)

        get_city_weather("3439525", self.req.id)
        self.req.refresh_from_db()

        client_mock.assert_called_once_with("3439525")
        self.assertEqual(
            self.req.cities,
            [
                {"city_id": "3439525", "temp": 289.99, "humidity": 88},
                {"city_id": "3439781"},
            ],
        )

    @patch("weather.clients.OpenWeatherClient.get")
    def test_sequential_city_weather_success(self, client_mock):
        client_mock.side_effect = [
            copy(mocks.open_weather_success_response),
            copy(mocks.open_weather_success_2_response),
        ]

        get_city_weather("3439525", self.req.id)
        self.req.refresh_from_db()
        self.assertEqual(
            self.req.cities,
            [
                {"city_id": "3439525", "temp": 289.99, "humidity": 88},
                {"city_id": "3439781"},
            ],
        )

        get_city_weather("3439781", self.req.id)
        self.req.refresh_from_db()
        self.assertEqual(
            self.req.cities,
            [
                {"city_id": "3439525", "temp": 289.99, "humidity": 88},
                {"city_id": "3439781", "temp": 285.05, "humidity": 64},
            ],
        )

        calls = [
            call("3439525"),
            call("3439781"),
        ]
        client_mock.assert_has_calls(calls)

    def test_open_weather_error(self):
        ...
