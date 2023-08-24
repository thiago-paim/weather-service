# weather-service

## Summary

This project setups a service API for collecting city weather data from [Open Weather API](https://openweathermap.org/current#cityid), and consist of several services running on Docker containers:

* Weather Service API

* PostgreSQL Database

* Celery Worker

* Celery Flower

* RabbitMQ


It implements two endpoints:

* `/weather/cities` 

    * Receives a POST request with an `user_id`, stores it in the DB, and then triggers async tasks for fetching city weather data from Open Weather
    * The collected data is stored in a `JSONField` in the DB.

* `/weather/progress`

    * Receives a GET request with an `user_id` url param and returns the progress cities weather data collection


## How to setup

* Create a local `.env` file by creating a copy of the sample file:

    ```bash
    cd weather_service
    cp .env.sample .env
    ```

* Update the `OPEN_WEATHER_API_KEY` with your Open Weather API key
    
    * Get one by [creating a free account on Open Weather](https://home.openweathermap.org/users/sign_up).


* Ensure you have [Docker](https://docs.docker.com/engine/) up and running, and then build the containers: 

    ```bash
    docker compose build
    ```


## How to run

* Start the containers, and the API will run on http://localhost:8000/

    ```bash
    docker compose up -d
    ```
    

* To start collecting weather data:

    ```bash
    curl -d "user_id=999" -X POST http://localhost:8000/weather/cities
    ```

* To check the collected data progress:

    ```bash
    curl -X GET http://localhost:8000/weather/progress?user_id=999
    ```

* To stop your app:

    ```bash
    docker compose down
    ```

### Monitoring

* In case you want a closer look on the database objects, you can use Django's builtin Admin app.

    * Create a super user:

        ```bash
        docker exec -it weather_service python3 manage.py createsuperuser
        ```
        
    * Then use it to login into the admin: http://localhost:8000/admin/


* To monitor running tasks check Celery Flower: http://localhost:8888/

* In case you want to stop all the tasks, you can purge the tasks queue:

    ```bash
    docker exec -it celery celery -A weather_service purge
    ```


## How to test

* After the app is running, you can test it with Coverage: 

    ```bash
    docker exec -it weather_service coverage run manage.py test
    ```

* To check the test coverage report: 

    ```bash
    docker exec -it weather_service coverage report
    ```


## Extra
### Open Weather rate limit

Open Weather free account has a 60 request/minute limit. This app relies on two strategies to avoid going over it:

* Using the `rate_limit` [Celery task param](https://docs.celeryq.dev/en/stable/userguide/tasks.html#Task.rate_limit) to ensure a worker won't execute it more than it should.

    * This param must be updated in the future if scaling workers becomes necessary

* Task retries with exponential backoff

    * When a request to Open Weather fails with a 429 HTTP error, it will be retried with increasing wait times to avoid storming their API with requests

### Django Admin

Django comes with a default Admin app that allows easy management of the models data. It is not necessary for this app to run and can be easily disabled in the future, but was kept for now as it helps visualizing the data during development.