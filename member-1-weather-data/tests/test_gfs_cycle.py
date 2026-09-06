from datetime import datetime, timezone

import pytest

from app.gfs.cycle import (
    GFSCycleResolver,
)


def test_cycle_at_00z():
    now = datetime(
        2026,
        8,
        30,
        1,
        0,
        tzinfo=timezone.utc,
    )

    cycle = GFSCycleResolver.resolve(now)

    assert cycle.date == "20260830"
    assert cycle.cycle == 0
    assert cycle.cycle_text == "00"


def test_cycle_at_06z():
    now = datetime(
        2026,
        8,
        30,
        8,
        0,
        tzinfo=timezone.utc,
    )

    cycle = GFSCycleResolver.resolve(now)

    assert cycle.date == "20260830"
    assert cycle.cycle == 6


def test_cycle_at_12z():
    now = datetime(
        2026,
        8,
        30,
        14,
        0,
        tzinfo=timezone.utc,
    )

    cycle = GFSCycleResolver.resolve(now)

    assert cycle.date == "20260830"
    assert cycle.cycle == 12


def test_cycle_at_18z():
    now = datetime(
        2026,
        8,
        30,
        20,
        0,
        tzinfo=timezone.utc,
    )

    cycle = GFSCycleResolver.resolve(now)

    assert cycle.date == "20260830"
    assert cycle.cycle == 18


def test_before_00z_uses_previous_day():
    now = datetime(
        2026,
        8,
        30,
        0,
        0,
        tzinfo=timezone.utc,
    )

    cycle = GFSCycleResolver.resolve(now)

    assert cycle.date == "20260830"
    assert cycle.cycle == 0


def test_url_uses_resolved_cycle():
    now = datetime(
        2026,
        8,
        30,
        14,
        0,
        tzinfo=timezone.utc,
    )

    url = GFSCycleResolver.build_url(
        now=now,
        forecast_hour=0,
    )

    assert "gfs.20260830" in url
    assert "12%2Fatmos" in url
    assert "gfs.t12z.pgrb2.0p25.f000" in url


def test_url_forecast_hour():
    now = datetime(
        2026,
        8,
        30,
        20,
        0,
        tzinfo=timezone.utc,
    )

    url = GFSCycleResolver.build_url(
        now=now,
        forecast_hour=12,
    )

    assert "gfs.t18z.pgrb2.0p25.f012" in url


def test_naive_datetime_is_treated_as_utc():
    now = datetime(
        2026,
        8,
        30,
        14,
        0,
    )

    cycle = GFSCycleResolver.resolve(now)

    assert cycle.date == "20260830"
    assert cycle.cycle == 12