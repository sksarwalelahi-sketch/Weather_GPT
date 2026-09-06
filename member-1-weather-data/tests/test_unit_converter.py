import pytest

from app.normalization.unit_converter import UnitConverter


def test_celsius_is_unchanged():
    assert UnitConverter.temperature_to_celsius(
        27.5,
        "°C",
    ) == pytest.approx(27.5)


def test_kelvin_to_celsius():
    assert UnitConverter.temperature_to_celsius(
        300.15,
        "K",
    ) == pytest.approx(27.0)


def test_fahrenheit_to_celsius():
    assert UnitConverter.temperature_to_celsius(
        32.0,
        "F",
    ) == pytest.approx(0.0)


def test_pascal_to_hpa():
    assert UnitConverter.pressure_to_hpa(
        100500.0,
        "Pa",
    ) == pytest.approx(1005.0)


def test_hpa_is_unchanged():
    assert UnitConverter.pressure_to_hpa(
        1005.0,
        "hPa",
    ) == pytest.approx(1005.0)


def test_ms_to_kmh():
    assert UnitConverter.wind_speed_to_kmh(
        5.0,
        "m/s",
    ) == pytest.approx(18.0)


def test_kmh_is_unchanged():
    assert UnitConverter.wind_speed_to_kmh(
        18.0,
        "km/h",
    ) == pytest.approx(18.0)


def test_mph_to_kmh():
    assert UnitConverter.wind_speed_to_kmh(
        10.0,
        "mph",
    ) == pytest.approx(16.09344)


def test_meters_to_mm():
    assert UnitConverter.precipitation_to_mm(
        0.0025,
        "m",
    ) == pytest.approx(2.5)


def test_mm_is_unchanged():
    assert UnitConverter.precipitation_to_mm(
        2.5,
        "mm",
    ) == pytest.approx(2.5)


def test_fraction_to_humidity_percent():
    assert UnitConverter.humidity_to_percent(
        0.75,
        "fraction",
    ) == pytest.approx(75.0)


def test_percent_is_unchanged():
    assert UnitConverter.humidity_to_percent(
        75.0,
        "%",
    ) == pytest.approx(75.0)


def test_wind_direction_is_normalized():
    assert UnitConverter.normalize_wind_direction(
        450.0,
    ) == pytest.approx(90.0)


def test_negative_wind_direction_is_normalized():
    assert UnitConverter.normalize_wind_direction(
        -90.0,
    ) == pytest.approx(270.0)


def test_unsupported_temperature_unit():
    with pytest.raises(ValueError):
        UnitConverter.temperature_to_celsius(
            20.0,
            "invalid",
        )


def test_unsupported_pressure_unit():
    with pytest.raises(ValueError):
        UnitConverter.pressure_to_hpa(
            1000.0,
            "invalid",
        )


def test_unsupported_wind_speed_unit():
    with pytest.raises(ValueError):
        UnitConverter.wind_speed_to_kmh(
            10.0,
            "invalid",
        )


def test_unsupported_precipitation_unit():
    with pytest.raises(ValueError):
        UnitConverter.precipitation_to_mm(
            10.0,
            "invalid",
        )


def test_unsupported_humidity_unit():
    with pytest.raises(ValueError):
        UnitConverter.humidity_to_percent(
            50.0,
            "invalid",
        )