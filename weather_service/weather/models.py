from django.db import models


class WeatherRequest(models.Model):
    user_id = models.CharField(max_length=8, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    cities = models.JSONField()
