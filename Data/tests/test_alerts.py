from datetime import UTC, datetime

import pytest

from app.api import alerts
from app.models.alert import AlertCreate


class FakeAlertRepository:
    def __init__(self):
        self.saved = None

    async def save(self, alert):
        self.saved = alert
        return {
            **alert.model_dump(),
            "alert_id": "alert-1",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

    async def list(self, **kwargs):
        return [], 0

    async def get(self, alert_id):
        return None


class FakeLiveUpdates:
    def __init__(self):
        self.published = []

    async def publish(self, channel, payload):
        self.published.append((channel, payload))


@pytest.mark.asyncio
async def test_create_alert_persists_and_publishes(monkeypatch):
    repository = FakeAlertRepository()
    updates = FakeLiveUpdates()
    monkeypatch.setattr(alerts, "alert_repository", repository)
    monkeypatch.setattr(alerts, "live_updates", updates)

    result = await alerts.create_alert(
        AlertCreate(
            title="Heavy rain",
            severity="warning",
            latitude=20.2961,
            longitude=85.8245,
        )
    )

    assert result.alert_id == "alert-1"
    assert repository.saved.title == "Heavy rain"
    assert updates.published[0][0] == "alerts"


def test_alert_requires_title():
    with pytest.raises(ValueError):
        AlertCreate(title="")


def test_official_alert_matches_nearby_coordinates():
    assert alerts._official_alert_matches_location(
        {"latitude": 20.35, "longitude": 85.82, "area": "Odisha"},
        20.30,
        85.80,
        "Bhubaneswar",
    )


def test_official_alert_does_not_match_without_location_evidence():
    assert not alerts._official_alert_matches_location(
        {"area": "Odisha"},
        20.30,
        85.80,
        "Bhubaneswar",
    )


def test_official_alert_matches_shared_administrative_component():
    assert alerts._official_alert_matches_location(
        {
            "area": "Khordha, Odisha",
            "metadata": {
                "district": "Khordha",
                "state": "Odisha",
            },
        },
        20.30,
        85.80,
        "Bhubaneswar, Khordha, Odisha",
    )


def test_official_alert_matches_structured_user_district():
    assert alerts._official_alert_matches_location(
        {
            "area": "Odisha",
            "metadata": {"district": "Khordha"},
        },
        20.30,
        85.80,
        "Bhubaneswar",
        district="Khordha",
    )


def test_official_alert_does_not_match_only_partial_component():
    assert not alerts._official_alert_matches_location(
        {
            "area": "New Delhi",
        },
        28.61,
        77.20,
        "Delhi NCR",
    )


def test_sachet_rss_is_parsed_as_national_official_alert():
    items = alerts._parse_sachet_rss(
        """<?xml version="1.0"?>
        <rss><channel><item>
          <title>Thunderstorm warning</title>
          <description>Take shelter indoors.</description>
          <category>Met</category>
          <link>https://sachet.ndma.gov.in/alert/123</link>
          <guid>123</guid>
          <author>NDMA Control Room</author>
          <pubDate>Thu, 17 Sep 2026 18:00:00 GMT</pubDate>
        </item></channel></rss>"""
    )

    alert = alerts._sachet_alert_record(
        items[0],
        latitude=20.2961,
        longitude=85.8245,
        area="Bhubaneswar",
    )

    assert alert.source == "NDMA-SACHET"
    assert alert.metadata["official_warning"] is True
    assert alert.metadata["scope"] == "national"
    assert alert.latitude is None
    assert alert.area == "India"
