from app.normalization.satellite_normalizer import (
    SatelliteWeatherNormalizer,
)


def test_satellite_normalization():
    payload = {
        "lat": 20.2961,
        "lon": 85.8245,
        "time": "2026-09-04T10:00:00Z",
        "cloud": 68.5,
        "brightness_temp": 245.7,
        "rainfall": 1.2,
        "solar": 540.0,
        "product": "INSAT-test",
    }

    weather = SatelliteWeatherNormalizer.normalize(
        payload
    )

    assert weather.latitude == 20.2961
    assert weather.longitude == 85.8245
    assert weather.cloud_cover == 68.5
    assert weather.brightness_temperature == 245.7
    assert weather.rainfall_estimate == 1.2
    assert weather.solar_radiation == 540.0
    assert weather.source == "mosdac"
    assert weather.product == "INSAT-test"