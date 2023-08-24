"""
URL configuration for weather_service project.
"""
from django.contrib import admin
from django.urls import path
from weather import views


urlpatterns = [
    path("weather/cities", views.CreateWeatherRequestView.as_view()),
    path("weather/progress", views.GetWeatherRequestProgress.as_view()),
    path("admin/", admin.site.urls),
]
