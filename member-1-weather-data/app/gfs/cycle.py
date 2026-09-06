from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass(frozen=True)
class GFSCycle:
    date: str
    cycle: int

    @property
    def cycle_text(self) -> str:
        return f"{self.cycle:02d}"


class GFSCycleResolver:
    """
    Resolves the latest GFS forecast cycle that should be
    available for ingestion.

    GFS runs are produced at:
        00Z
        06Z
        12Z
        18Z
    """

    CYCLES = (0, 6, 12, 18)

    @classmethod
    def resolve(
        cls,
        now: datetime | None = None,
    ) -> GFSCycle:
        if now is None:
            now = datetime.now(timezone.utc)

        if now.tzinfo is None:
            now = now.replace(
                tzinfo=timezone.utc
            )

        now = now.astimezone(timezone.utc)

        available_hours = [
            cycle
            for cycle in cls.CYCLES
            if cycle <= now.hour
        ]

        if available_hours:
            cycle = max(available_hours)

            return GFSCycle(
                date=now.strftime("%Y%m%d"),
                cycle=cycle,
            )

        # Before the 00Z cycle of the current day,
        # use the previous day's 18Z cycle.
        previous_day = now.date()

        previous_day = previous_day.fromordinal(
            previous_day.toordinal() - 1
        )

        return GFSCycle(
            date=previous_day.strftime("%Y%m%d"),
            cycle=18,
        )

    @classmethod
    def build_url(
        cls,
        now: datetime | None = None,
        forecast_hour: int = 0,
    ) -> str:
        cycle = cls.resolve(now)

        return (
            "https://nomads.ncep.noaa.gov/cgi-bin/"
            "filter_gfs_0p25.pl"
            f"?dir=%2Fgfs.{cycle.date}%2F"
            f"{cycle.cycle_text}%2Fatmos"
            "&file="
            f"gfs.t{cycle.cycle_text}z."
            "pgrb2.0p25."
            f"f{forecast_hour:03d}"
        )