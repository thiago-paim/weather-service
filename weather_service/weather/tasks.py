from httpx import HTTPStatusError
from celery import shared_task
from django.db import transaction
from weather.clients import open_weather_cli
from weather.models import WeatherRequest


@shared_task(bind=True, rate_limit="60/m", retry_backoff=True)
def get_city_weather(self, city_id, weather_request_id):
    """Collects weather data for a city from Open Weather API and updates it in the corresponding WeatherRequest"""

    try:
        response = open_weather_cli.get(city_id)
    except HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise self.retry(exc=exc)
        raise

    data = {"city_id": city_id}
    data["temp"] = response.get("main").get("temp")
    data["humidity"] = response.get("main").get("humidity")

    with transaction.atomic():
        req = WeatherRequest.objects.select_for_update().get(id=weather_request_id)
        i = req.cities.index({"city_id": city_id})
        req.cities[i] = data
        req.save()
