import httpx
from django.conf import settings


OPEN_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class OpenWeatherClient:
    """Helper class for sending requests to Open Weather API"""

    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key

    def get(self, city_id):
        params = {"id": city_id, "appid": self.api_key}
        with httpx.Client() as client:
            response = client.get(self.url, params=params)
        response.raise_for_status()
        return response.json()


open_weather_cli = OpenWeatherClient(OPEN_WEATHER_URL, settings.OPEN_WEATHER_API_KEY)
