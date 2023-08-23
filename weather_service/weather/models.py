from django.db import models


class WeatherRequest(models.Model):
    user_id = models.CharField(max_length=8, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    cities = models.JSONField()

    def create_open_weather_tasks(self):
        """Creates Celery tasks for collecting weather data for each city"""
        from weather.tasks import get_city_weather

        for city in self.cities:
            get_city_weather.delay(city["city_id"], self.id)

    def progress(self):
        total = len(self.cities)
        finished = 0
        for city in self.cities:
            if "temp" in city and "humidity" in city:
                finished += 1
        percent = 100 * finished / total
        return f"{percent:.0f}%"
