import json
from copy import deepcopy
from django.shortcuts import render
from rest_framework import generics
from weather.models import WeatherRequest
from weather.serializers import WeatherRequestSerializer
from weather.values import open_weather_default_cities


class CreateWeatherRequest(generics.CreateAPIView):
    serializer_class = WeatherRequestSerializer

    def get_cities_json(self):
        cities = [{"city_id": city} for city in open_weather_default_cities]
        return json.dumps(cities)

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = deepcopy(kwargs["data"])
            data["cities"] = self.get_cities_json()
            kwargs["data"] = data

        return super().get_serializer(*args, **kwargs)
