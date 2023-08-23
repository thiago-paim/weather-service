from rest_framework import serializers
from weather.models import WeatherRequest


class WeatherRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherRequest
        fields = ["user_id", "date", "cities"]


class WeatherRequestProgressSerializer(serializers.ModelSerializer):
    progress = serializers.ReadOnlyField()

    class Meta:
        model = WeatherRequest
        fields = ["progress"]
