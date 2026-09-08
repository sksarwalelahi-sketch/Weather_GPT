from unittest.mock import Mock
from integration.member1_client import Member1APIError
from fastapi.testclient import TestClient

from api.main import app
from api.routes import intelligence


client = TestClient(app)


class FakeResult:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self, mode="json"):
        return self.payload


def test_historical_intelligence_endpoint(monkeypatch):
    fake_service = Mock()

    fake_service.analyze_current_with_history.return_value = FakeResult(
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
            "climate_analysis": [
                {
                    "metric": "TEMPERATURE",
                    "period": "2026-08-18 to 2026-08-20",
                    "average_value": 31.5,
                    "baseline_value": 30.0,
                    "anomaly": 1.5,
                    "trend": "INCREASING",
                    "trend_percentage": 5.0,
                    "confidence": 1.0,
                    "location_name": "Bhubaneswar",
                    "data_points": 3,
                }
            ],
            "processing_version": "1.0.0",
        }
    )

    monkeypatch.setattr(intelligence, "service", fake_service)

    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": (
                '{"temperature":30,"rainfall":5,"wind_speed":15}'
            ),
            "location_name": "Bhubaneswar",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["location_name"] == "Bhubaneswar"
    assert len(data["climate_analysis"]) == 1
    assert data["climate_analysis"][0]["metric"] == "TEMPERATURE"

    fake_service.analyze_current_with_history.assert_called_once_with(
        latitude=20.281195,
        longitude=85.843376,
        start_date=__import__("datetime").date(2026, 8, 18),
        end_date=__import__("datetime").date(2026, 8, 20),
        baselines={
            "temperature": 30,
            "rainfall": 5,
            "wind_speed": 15,
        },
        location_name="Bhubaneswar",
    )


def test_historical_endpoint_rejects_invalid_date_order():
    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-20",
            "end_date": "2026-08-18",
            "baselines": '{"temperature":30}',
        },
    )

    assert response.status_code == 422
    assert "start_date must be before" in response.json()["detail"]


def test_historical_endpoint_rejects_invalid_baseline_json():
    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": "not-valid-json",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "baselines must be valid JSON"


def test_historical_endpoint_rejects_non_object_baselines():
    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": '["temperature", 30]',
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "baselines must be a JSON object"


def test_historical_endpoint_rejects_unsupported_metric():
    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": '{"humidity":80}',
        },
    )

    assert response.status_code == 422
    assert "Unsupported baseline metrics" in response.json()["detail"]


def test_historical_endpoint_rejects_non_numeric_baseline():
    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": '{"temperature":"hot"}',
        },
    )

    assert response.status_code == 422
    assert "Baseline 'temperature' must be numeric" in response.json()["detail"]


def test_historical_endpoint_rejects_empty_baselines():
    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": "{}",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "At least one climate baseline is required"
    )


def test_historical_endpoint_returns_502_when_service_fails(monkeypatch):
    fake_service = Mock()

    fake_service.analyze_current_with_history.side_effect = Member1APIError(
        "Member 1 historical API unavailable"
    )

    monkeypatch.setattr(intelligence, "service", fake_service)

    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": '{"temperature":30}',
        },
    )

    assert response.status_code == 502
    assert "Unable to analyze historical weather" in response.json()["detail"]



def test_historical_endpoint_returns_500_when_unexpected_error_occurs(
    monkeypatch,
):
    fake_service = Mock()

    fake_service.analyze_current_with_history.side_effect = RuntimeError(
        "Unexpected intelligence failure"
    )

    monkeypatch.setattr(intelligence, "service", fake_service)

    response = client.get(
        "/api/v1/intelligence/historical",
        params={
            "latitude": 20.281195,
            "longitude": 85.843376,
            "start_date": "2026-08-18",
            "end_date": "2026-08-20",
            "baselines": '{"temperature":30}',
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert "Internal intelligence error" in data["detail"]