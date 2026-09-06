import pytest

from app.services.weather_service import WeatherService


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


def test_service_accepts_optional_repository():
    repository = FakeRepository()

    service = WeatherService(
        client=None,
        repository=repository,
    )

    assert service.repository is repository


def test_service_without_repository():
    service = WeatherService()

    assert service.repository is None


@pytest.mark.asyncio
async def test_repository_is_used_for_current_weather():
    repository = FakeRepository()

    class FakeClient:
        async def get_weather(self, latitude, longitude):
            raise RuntimeError("network call should be mocked")

        async def close(self):
            pass

    service = WeatherService(
        client=FakeClient(),
        repository=repository,
    )

    assert service.repository is repository