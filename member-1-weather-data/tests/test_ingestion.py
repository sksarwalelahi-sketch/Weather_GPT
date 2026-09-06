from datetime import datetime, timezone

import pytest

from app.ingestion.weather_ingestion import WeatherIngestion


class FakeClient:
    async def get_weather(
        self,
        latitude,
        longitude,
    ):
        return type(
            "Weather",
            (),
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": type(
                    "Current",
                    (),
                    {
                        "temperature": 27.0,
                        "relative_humidity": 80.0,
                        "apparent_temperature": 30.0,
                        "precipitation": 0.0,
                        "rain": 0.0,
                        "weather_code": 3,
                        "cloud_cover": 80.0,
                        "surface_pressure": 1000.0,
                        "wind_speed": 10.0,
                        "wind_direction": 180.0,
                        "wind_gusts": 15.0,
                        "time": datetime.now(timezone.utc),
                    },
                )(),
            },
        )()

    async def get_forecast(
        self,
        latitude,
        longitude,
        forecast_days,
    ):
        return None

    async def get_historical(
        self,
        latitude,
        longitude,
        start_date,
        end_date,
    ):
        return None

    async def close(self):
        pass


class FakeRepository:
    def __init__(self):
        self.current = []
        self.forecasts = []
        self.historical = []

    async def save_current(self, weather):
        self.current.append(weather)
        return "current-id"

    async def save_forecast(self, forecast):
        self.forecasts.append(forecast)
        return "forecast-id"

    async def save_historical(self, historical):
        self.historical.append(historical)
        return "historical-id"


def test_ingestion_initialization():
    client = FakeClient()
    repository = FakeRepository()

    ingestion = WeatherIngestion(
        client=client,
        repository=repository,
    )

    assert ingestion.client is client
    assert ingestion.repository is repository
    assert ingestion.SOURCE == "open-meteo"


@pytest.mark.asyncio
async def test_current_ingestion_validation():
    ingestion = WeatherIngestion(
        client=FakeClient(),
    )

    result = await ingestion.ingest_current(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result.latitude == 20.2961
    assert result.longitude == 85.8245
    assert result.temperature == 27.0
    assert result.apparent_temperature == 30.0
    assert result.relative_humidity == 80.0


@pytest.mark.asyncio
async def test_current_ingestion_saves_repository():
    repository = FakeRepository()

    ingestion = WeatherIngestion(
        client=FakeClient(),
        repository=repository,
    )

    result = await ingestion.ingest_current(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert result is not None
    assert len(repository.current) == 1
    assert repository.current[0] == result


@pytest.mark.asyncio
async def test_ingestion_close():
    client = FakeClient()

    ingestion = WeatherIngestion(
        client=client,
    )

    await ingestion.close()

    assert ingestion.client is client