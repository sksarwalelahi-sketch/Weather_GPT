from unittest.mock import Mock

from fastapi.testclient import TestClient
from integration.member1_client import Member1APIError
from api.main import app
from api.routes import intelligence


client = TestClient(app)


class FakeResult:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self, mode="json"):
        return self.payload


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "weathergpt-intelligence"
    assert data["version"] == "1.0.0"


def test_current_intelligence_endpoint(monkeypatch):
    fake_service = Mock()

    fake_service.analyze_current.return_value = FakeResult(
        {
            "location_name": "Bhubaneswar",
            "generated_at": "2026-09-07T16:00:00",
            "risk_assessment": {
                "overall_level": "LOW",
                "overall_score": 20.0,
                "timestamp": "2026-09-07T16:00:00",
                "rainfall_risk": 0.0,
                "wind_risk": 0.0,
                "heat_risk": 20.0,
                "confidence": 1.0,
                "data_quality": "COMPLETE",
                },
            "hazards": [],
            "alerts": [],
            "advisories": [],
            "climate_analysis":[],
            "processing_version": "1.0.0",
        }
    )

    monkeypatch.setattr(intelligence, "service", fake_service)

    response = client.get(
        "/api/v1/intelligence/current",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "location_name": "Bhubaneswar",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["location_name"] == "Bhubaneswar"
    assert data["risk_assessment"]["overall_level"] == "LOW"
    assert data["processing_version"] == "1.0.0"

    fake_service.analyze_current.assert_called_once_with(
        latitude=20.281195,
        longitude=85.843376,
        location_name="Bhubaneswar",
    )


def test_forecast_intelligence_endpoint(monkeypatch):
    fake_service = Mock()

    fake_service.analyze_forecast.return_value = FakeResult(
        {
            "location_name": "Bhubaneswar",
            "generated_at": "2026-09-07T16:00:00",
            "forecast_start": "2026-09-07T00:00:00",
            "forecast_end": "2026-09-13T00:00:00",
            "forecast_points": [],
            "maximum_risk_level": "MODERATE",
            "maximum_risk_score": 34.0,
            "hazards": [],
            "summary": "Forecast analysis completed.",
            "confidence": 1.0,
            "source": "open-meteo",
            "data_points": 7,
        }
    )

    monkeypatch.setattr(intelligence, "service", fake_service)

    response = client.get(
        "/api/v1/intelligence/forecast",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "forecast_days": 7,
            "location_name": "Bhubaneswar",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["location_name"] == "Bhubaneswar"
    assert data["maximum_risk_level"] == "MODERATE"
    assert data["maximum_risk_score"] == 34.0
    assert data["data_points"] == 7

    fake_service.analyze_forecast.assert_called_once_with(
        latitude=20.281195,
        longitude=85.843376,
        forecast_days=7,
        location_name="Bhubaneswar",
    )


def test_current_endpoint_rejects_invalid_latitude():
    response = client.get(
        "/api/v1/intelligence/current",
        params={
            "latitude": 100,
            "longitude": 85.843376,
        },
    )

    assert response.status_code == 422


def test_current_endpoint_rejects_invalid_longitude():
    response = client.get(
        "/api/v1/intelligence/current",
        params={
            "latitude": 20.281195,
            "longitude": 200,
        },
    )

    assert response.status_code == 422


def test_forecast_endpoint_rejects_invalid_forecast_days():
    response = client.get(
        "/api/v1/intelligence/forecast",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "forecast_days": 17,
        },
    )

    assert response.status_code == 422


def test_forecast_endpoint_rejects_zero_forecast_days():
    response = client.get(
        "/api/v1/intelligence/forecast",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "forecast_days": 0,
        },
    )

    assert response.status_code == 422


def test_current_endpoint_returns_502_when_service_fails(monkeypatch):
    fake_service = Mock()

    fake_service.analyze_current.side_effect = Member1APIError(
        "Member 1 API unavailable"
    )

    monkeypatch.setattr(intelligence, "service", fake_service)

    response = client.get(
        "/api/v1/intelligence/current",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
        },
    )

    assert response.status_code == 502

    data = response.json()

    assert "Unable to analyze current weather" in data["detail"]


def test_forecast_endpoint_returns_502_when_service_fails(monkeypatch):
    fake_service = Mock()

    fake_service.analyze_forecast.side_effect = Member1APIError(
        "Member 1 API unavailable"
    )

    monkeypatch.setattr(intelligence, "service", fake_service)

    response = client.get(
        "/api/v1/intelligence/forecast",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "forecast_days": 7,
        },
    )

    assert response.status_code == 502

    data = response.json()

    assert "Unable to analyze forecast weather" in data["detail"]