from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.validation.weather_validator import (
    HumidityData,
    LocationData,
    PrecipitationData,
    PressureData,
    TemperatureData,
    TimestampData,
    WindData,
)


# -------------------------
# Location
# -------------------------

def test_valid_location():
    location = LocationData(
        latitude=20.2961,
        longitude=85.8245,
    )

    assert location.latitude == 20.2961
    assert location.longitude == 85.8245


def test_invalid_latitude():
    with pytest.raises(ValidationError):
        LocationData(
            latitude=95,
            longitude=85.8245,
        )


def test_invalid_longitude():
    with pytest.raises(ValidationError):
        LocationData(
            latitude=20.2961,
            longitude=185,
        )


# -------------------------
# Temperature
# -------------------------

def test_valid_temperature():
    temperature = TemperatureData(temperature=27.4)

    assert temperature.temperature == 27.4


def test_temperature_too_low():
    with pytest.raises(ValidationError):
        TemperatureData(temperature=-101)


def test_temperature_too_high():
    with pytest.raises(ValidationError):
        TemperatureData(temperature=71)


# -------------------------
# Humidity
# -------------------------

def test_valid_humidity():
    humidity = HumidityData(relative_humidity=92)

    assert humidity.relative_humidity == 92


def test_humidity_below_zero():
    with pytest.raises(ValidationError):
        HumidityData(relative_humidity=-1)


def test_humidity_above_100():
    with pytest.raises(ValidationError):
        HumidityData(relative_humidity=101)


# -------------------------
# Precipitation
# -------------------------

def test_valid_precipitation():
    precipitation = PrecipitationData(precipitation=12.5)

    assert precipitation.precipitation == 12.5


def test_precipitation_cannot_be_negative():
    with pytest.raises(ValidationError):
        PrecipitationData(precipitation=-0.1)


# -------------------------
# Wind
# -------------------------

def test_valid_wind():
    wind = WindData(
        wind_speed=8.9,
        wind_direction=251,
    )

    assert wind.wind_speed == 8.9
    assert wind.wind_direction == 251


def test_wind_speed_cannot_be_negative():
    with pytest.raises(ValidationError):
        WindData(
            wind_speed=-1,
            wind_direction=251,
        )


def test_wind_direction_cannot_be_invalid():
    with pytest.raises(ValidationError):
        WindData(
            wind_speed=8.9,
            wind_direction=361,
        )


# -------------------------
# Pressure
# -------------------------

def test_valid_pressure():
    pressure = PressureData(surface_pressure=997.3)

    assert pressure.surface_pressure == 997.3


def test_pressure_cannot_be_zero():
    with pytest.raises(ValidationError):
        PressureData(surface_pressure=0)


def test_pressure_cannot_be_negative():
    with pytest.raises(ValidationError):
        PressureData(surface_pressure=-10)


# -------------------------
# Timestamp
# -------------------------

def test_valid_timestamp():
    timestamp = TimestampData(
        timestamp=datetime.now(timezone.utc)
    )

    assert timestamp.validate_timestamp() is not None


def test_future_timestamp_is_rejected():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=10)

    timestamp = TimestampData(timestamp=future_time)

    with pytest.raises(ValueError):
        timestamp.validate_timestamp()


def test_timestamp_within_five_minutes_is_allowed():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=2)

    timestamp = TimestampData(timestamp=future_time)

    assert timestamp.validate_timestamp() == future_time