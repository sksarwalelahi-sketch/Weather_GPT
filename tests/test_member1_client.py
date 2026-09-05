"""
Tests for the Member 1 HTTP client.

These tests mock the HTTP layer so they do not require
the Member 1 FastAPI server to be running.
"""

import json
from datetime import date
from unittest.mock import patch

from integration.member1_client import (
    Member1APIError,
    Member1Client,
)


CURRENT_RESPONSE = {
    "latitude": 20.281195,
    "longitude": 85.843376,
    "observed_at": "2026-09-05T16:45:00",
    "temperature": 27.3,
    "apparent_temperature": 33.5,
    "relative_humidity": 93,
    "precipitation": 0,
    "rain": 0,
    "weather_code": 0,
    "cloud_cover": 14,
    "surface_pressure": 1004.6,
    "wind_speed": 8.3,
    "wind_direction": 210,
    "wind_gusts": 14.8,
    "source": "open-meteo",
}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_get_current():
    client = Member1Client()

    with patch(
        "integration.member1_client.urlopen",
        return_value=FakeResponse(CURRENT_RESPONSE),
    ) as mock_urlopen:

        result = client.get_current(
            latitude=20.281195,
            longitude=85.843376,
        )

    assert result == CURRENT_RESPONSE

    request = mock_urlopen.call_args.args[0]

    assert request.full_url.startswith(
        "http://127.0.0.1:8000/weather/current?"
    )

    assert "latitude=20.281195" in request.full_url
    assert "longitude=85.843376" in request.full_url


def test_get_forecast():
    client = Member1Client()

    payload = {
        "latitude": 20.281195,
        "longitude": 85.843376,
        "timezone": "GMT",
        "source": "open-meteo",
        "forecast": [],
    }

    with patch(
        "integration.member1_client.urlopen",
        return_value=FakeResponse(payload),
    ) as mock_urlopen:

        result = client.get_forecast(
            latitude=20.281195,
            longitude=85.843376,
            forecast_days=7,
        )

    assert result == payload

    request = mock_urlopen.call_args.args[0]

    assert "/weather/forecast?" in request.full_url
    assert "forecast_days=7" in request.full_url


def test_get_historical():
    client = Member1Client()

    payload = {
        "latitude": 20.281195,
        "longitude": 85.843376,
        "timezone": "GMT",
        "source": "open-meteo",
        "start_date": "2026-08-18",
        "end_date": "2026-08-20",
        "historical": [],
    }

    with patch(
        "integration.member1_client.urlopen",
        return_value=FakeResponse(payload),
    ) as mock_urlopen:

        result = client.get_historical(
            latitude=20.281195,
            longitude=85.843376,
            start_date=date(2026, 8, 18),
            end_date=date(2026, 8, 20),
        )

    assert result == payload

    request = mock_urlopen.call_args.args[0]

    assert "/weather/historical?" in request.full_url
    assert "start_date=2026-08-18" in request.full_url
    assert "end_date=2026-08-20" in request.full_url


def test_forecast_days_validation():
    client = Member1Client()

    try:
        client.get_forecast(
            latitude=20.281195,
            longitude=85.843376,
            forecast_days=17,
        )
    except ValueError as exc:
        assert "between 1 and 16" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for forecast_days=17"
        )


def test_api_invalid_json():
    class InvalidJSONResponse(FakeResponse):
        def read(self):
            return b"not-json"

    client = Member1Client()

    with patch(
        "integration.member1_client.urlopen",
        return_value=InvalidJSONResponse({}),
    ):
        try:
            client.get_current(
                latitude=20.281195,
                longitude=85.843376,
            )
        except Member1APIError as exc:
            assert "invalid JSON" in str(exc)
        else:
            raise AssertionError(
                "Expected Member1APIError"
            )