from django.contrib import admin
from weather.models import WeatherRequest


@admin.register(WeatherRequest)
class WeatherRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "date", "progress")
