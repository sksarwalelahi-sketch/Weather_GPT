from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.models.weather import (
    CurrentWeather,
    DailyForecast,
    OpenMeteoForecastResponse,
    OpenMeteoResponse,
)
from app.normalization.weather_normalizer import WeatherNormalizer
from app.models.weather import (
    DailyHistoricalWeather,
    OpenMeteoHistoricalResponse,
)


client = TestClient(app)


def sample_current_response():
    return OpenMeteoResponse(
        latitude=20.281195,
        longitude=85.843376,
        generationtime_ms=0.2,
        utc_offset_seconds=0,
        timezone="GMT",
        timezone_abbreviation="GMT",
        elevation=44.0,
        current_units={
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "apparent_temperature": "°C",
            "precipitation": "mm",
            "rain": "mm",
            "weather_code": "wmo code",
            "cloud_cover": "%",
            "surface_pressure": "hPa",
            "wind_speed_10m": "km/h",
            "wind_direction_10m": "°",
            "wind_gusts_10m": "km/h",
        },
        current=CurrentWeather(
            time=datetime(2026, 8, 28, 18, 45),
            temperature_2m=27.4,
            relative_humidity_2m=92.0,
            apparent_temperature=33.4,
            precipitation=0.0,
            rain=0.0,
            weather_code=3,
            cloud_cover=99.0,
            surface_pressure=997.3,
            wind_speed_10m=8.9,
            wind_direction_10m=251.0,
            wind_gusts_10m=16.6,
        ),
    )


def sample_forecast_response():
    return OpenMeteoForecastResponse(
        latitude=20.281195,
        longitude=85.843376,
        generationtime_ms=0.2,
        utc_offset_seconds=0,
        timezone="GMT",
        timezone_abbreviation="GMT",
        elevation=44.0,
        daily_units={
            "time": "iso8601",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
            "precipitation_sum": "mm",
            "rain_sum": "mm",
            "weather_code": "wmo code",
            "wind_speed_10m_max": "km/h",
        },
        daily=DailyForecast(
            time=[
                "2026-08-29",
                "2026-08-30",
                "2026-08-31",
            ],
            temperature_2m_max=[
                32.5,
                31.8,
                33.1,
            ],
            temperature_2m_min=[
                25.2,
                24.9,
                25.4,
            ],
            precipitation_sum=[
                2.5,
                5.2,
                0.0,
            ],
            rain_sum=[
                2.5,
                5.2,
                0.0,
            ],
            weather_code=[
                61,
                63,
                3,
            ],
            wind_speed_10m_max=[
                18.5,
                20.2,
                15.4,
            ],
        ),
    )


def sample_historical_response():
    return OpenMeteoHistoricalResponse(
        latitude=20.281195,
        longitude=85.843376,
        generationtime_ms=0.2,
        utc_offset_seconds=0,
        timezone="GMT",
        timezone_abbreviation="GMT",
        elevation=44.0,
        daily_units={
            "time": "iso8601",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
            "precipitation_sum": "mm",
            "rain_sum": "mm",
            "weather_code": "wmo code",
            "wind_speed_10m_max": "km/h",
        },
        daily=DailyHistoricalWeather(
            time=[
                "2026-08-25",
                "2026-08-26",
                "2026-08-27",
            ],
            temperature_2m_max=[
                31.2,
                30.8,
                32.1,
            ],
            temperature_2m_min=[
                25.1,
                24.8,
                25.4,
            ],
            precipitation_sum=[
                4.5,
                12.2,
                0.8,
            ],
            rain_sum=[
                4.5,
                12.2,
                0.8,
            ],
            weather_code=[
                61,
                63,
                3,
            ],
            wind_speed_10m_max=[
                17.2,
                21.5,
                15.8,
            ],
        ),
    )


def test_current_weather_endpoint(monkeypatch):
    async def fake_get_current_weather(
        self,
        latitude,
        longitude,
    ):
        return WeatherNormalizer.normalize(
            sample_current_response()
        )

    monkeypatch.setattr(
        "app.api.weather.WeatherService.get_current_weather",
        fake_get_current_weather,
    )

    response = client.get(
        "/weather/current",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "open-meteo"
    assert data["latitude"] == 20.281195
    assert data["longitude"] == 85.843376
    assert data["temperature"] == 27.4
    assert data["relative_humidity"] == 92.0
    assert data["wind_speed"] == 8.9
    assert data["wind_direction"] == 251.0


def test_current_weather_rejects_invalid_latitude():
    response = client.get(
        "/weather/current",
        params={
            "latitude": 100,
            "longitude": 85.8245,
        },
    )

    assert response.status_code == 422


def test_current_weather_rejects_invalid_longitude():
    response = client.get(
        "/weather/current",
        params={
            "latitude": 20.2961,
            "longitude": 200,
        },
    )

    assert response.status_code == 422


def test_forecast_endpoint(monkeypatch):
    async def fake_get_forecast(
        self,
        latitude,
        longitude,
        forecast_days,
    ):
        return WeatherNormalizer.normalize_forecast(
            sample_forecast_response()
        )

    monkeypatch.setattr(
        "app.api.weather.WeatherService.get_forecast",
        fake_get_forecast,
    )

    response = client.get(
        "/weather/forecast",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
            "forecast_days": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "open-meteo"
    assert len(data["forecast"]) == 3
    assert data["forecast"][0]["temperature_max"] == 32.5


def test_forecast_endpoint_rejects_invalid_days():
    response = client.get(
        "/weather/forecast",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
            "forecast_days": 17,
        },
    )

    assert response.status_code == 422


def test_historical_endpoint(monkeypatch):
    async def fake_get_historical(
        self,
        latitude,
        longitude,
        start_date,
        end_date,
    ):
        return WeatherNormalizer.normalize_historical(
            sample_historical_response()
        )

    monkeypatch.setattr(
        "app.api.weather.WeatherService.get_historical",
        fake_get_historical,
    )

    response = client.get(
        "/weather/historical",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
            "start_date": "2026-08-25",
            "end_date": "2026-08-27",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "open-meteo"
    assert data["start_date"] == "2026-08-25"
    assert data["end_date"] == "2026-08-27"
    assert len(data["historical"]) == 3
    assert data["historical"][0]["temperature_max"] == 31.2


def test_historical_endpoint_rejects_invalid_date_range():
    response = client.get(
        "/weather/historical",
        params={
            "latitude": 20.2961,
            "longitude": 85.8245,
            "start_date": "2026-08-27",
            "end_date": "2026-08-25",
        },
    )

    assert response.status_code == 400
    
def test_weather_models_endpoint():
    response = client.get(
        "/weather/models"
    )

    assert response.status_code == 200

    data = response.json()

    assert "models" in data
    assert len(data["models"]) == 3

    models = {
        model["id"]: model
        for model in data["models"]
    }

    assert "open-meteo" in models
    assert "noaa-gfs" in models
    assert "era5" in models

    assert models["open-meteo"]["status"] == "active"
    assert models["noaa-gfs"]["status"] == "active"
    assert models["era5"]["status"] == "active"