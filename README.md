# weather-service

This project setups a service API for collecting city weather data from [Open Weather API](https://openweathermap.org/current#cityid). 

## How to setup

### Environment setup

This project uses `django_environ` to manage environment variables, so you must setup a local `.env` file. You should create a copy of the sample file:

```
cd weather_service
cp .env.sample .env
```

Then you must update the `OPEN_WEATHER_API_KEY` with your own Open Weather API key (you can get one by [creating a free account on Open Weather](https://home.openweathermap.org/users/sign_up)).


### Docker setup
Ensure you have [Docker](https://docs.docker.com/engine/) up and running.
If it's the first time you're running the project, you must build the containers: 

    docker compose build


## How to run

### Starting the app

After following the steps above, all you need to do is start the containers: 

    docker compose up -d

The app should be running on http://127.0.0.1:8000/

### Using the app

* Endpoints:

    * Get Cities: *POST* http://127.0.0.1:8000/weather/


* Admin: http://127.0.0.1:8000/admin/

* Celery Flower: http://127.0.0.1:8888/


### Stopping the app

For stopping your app, use the command:

    docker compose down


## How to test

After you have your application up and running, you can run the tests inside the container either with Django's management command: 

    docker exec -it weather_service python3 manage.py test

Or with Coverage: 

    docker exec -it weather_service coverage run manage.py test

For checking the test coverage report: 

    docker exec -it weather_service coverage report


## Troubleshooting

In case you need to stop all the tasks, you can purge Celery's tasks queue:

    docker exec -it celery celery -A weather_service purge