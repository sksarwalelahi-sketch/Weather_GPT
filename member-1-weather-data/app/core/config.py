import os

from dotenv import load_dotenv


# Load variables from the project's .env file.
load_dotenv()


class Settings:
    APP_NAME = os.getenv(
        "APP_NAME",
        "WeatherGPT Weather Data Platform",
    )

    APP_VERSION = os.getenv(
        "APP_VERSION",
        "0.1.0",
    )

    API_PREFIX = os.getenv(
        "API_PREFIX",
        "/api",
    )

    MONGODB_URI = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017",
    )

    MONGODB_DATABASE = os.getenv(
        "MONGODB_DATABASE",
        "weathergpt",
    )

    REDIS_HOST = os.getenv(
        "REDIS_HOST",
        "127.0.0.1",
    )

    REDIS_PORT = int(
        os.getenv(
            "REDIS_PORT",
            "6379",
        )
    )

    REDIS_DB = int(
        os.getenv(
            "REDIS_DB",
            "0",
        )
    )


settings = Settings()