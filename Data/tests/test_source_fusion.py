from datetime import UTC, datetime, timedelta

from app.services.source_fusion import score_sources


def test_single_live_source_has_moderate_confidence():
    result = score_sources(["open-meteo"])

    assert result.score == 0.65
    assert result.label == "moderate"
    assert result.method == "single-source"


def test_corroborated_sources_raise_confidence():
    result = score_sources(
        ["open-meteo", "noaa-gfs"],
        corroborating_sources=1,
    )

    assert result.score == 0.8
    assert result.label == "moderate"
    assert result.method == "multi-source-corroboration"


def test_official_source_has_high_confidence():
    result = score_sources(["IMD-official-feed"], official=True)

    assert result.score == 0.95
    assert result.label == "high"
    assert result.method == "official-source"


def test_stale_source_is_penalized():
    result = score_sources(
        ["noaa-gfs"],
        retrieved_at=datetime.now(UTC) - timedelta(hours=60),
    )

    assert result.score == 0.4
    assert result.label == "low"
