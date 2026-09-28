from unittest.mock import Mock

from integration.member1_client import Member1Client
from services.intelligence_service import IntelligenceService


def test_imd_source_uses_imd_endpoint_and_adapter():
    client = Mock(spec=Member1Client)
    client.get_current.return_value = {
        "latitude": 20.3,
        "longitude": 85.8,
        "timestamp": "2026-09-09T12:00:00+00:00",
        "temperature": 32,
        "relative_humidity": 70,
        "precipitation": 1,
        "source": "imd",
    }

    result = IntelligenceService(client=client).analyze_current(
        20.3,
        85.8,
        source="imd",
    )

    client.get_current.assert_called_once_with(
        latitude=20.3,
        longitude=85.8,
        source="imd",
    )
    assert result.risk_assessment is not None


def test_source_adapter_maps_gfs_payload():
    client = Mock(spec=Member1Client)
    client.get_current.return_value = {
        "source": "noaa-gfs",
        "data": {
            "latitude": 20.3,
            "longitude": 85.8,
            "valid_at": "2026-09-09T12:00:00+00:00",
            "temperature": 30,
        },
    }

    result = IntelligenceService(client=client).analyze_current(
        20.3,
        85.8,
        source="gfs",
    )

    assert result.risk_assessment is not None
