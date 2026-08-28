"""
WeatherGPT - Member 3
Risk Assessment Schemas

Defines structured data contracts for weather risk analysis.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """
    Categorical weather risk level.
    """

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class DataQuality(str, Enum):
    """
    Describes the availability of the weather measurements
    used by the risk engine.

    COMPLETE:
        All core weather measurements required by the current
        baseline risk engine are available.

    PARTIAL:
        At least one core measurement is available, but one or
        more measurements are missing.

    INSUFFICIENT:
        No core weather measurements are available.
    """

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


class RiskComponent(BaseModel):
    """
    Individual weather-risk component.
    """

    risk_type: str = Field(
        min_length=1,
        description="Type of weather risk being evaluated.",
    )

    level: RiskLevel

    score: float = Field(
        ge=0,
        le=100,
        description="Normalized risk score from 0 to 100.",
    )

    reason: str = Field(
        min_length=1,
        description="Human-readable explanation of the risk.",
    )


class RiskAssessment(BaseModel):
    """
    Complete weather risk assessment.

    The assessment contains:
    - Overall weather risk
    - Individual risk components
    - Data-quality information
    - Assessment timestamp
    """

    overall_level: RiskLevel

    overall_score: float = Field(
        ge=0,
        le=100,
        description="Overall normalized risk score from 0 to 100.",
    )

    components: list[RiskComponent] = Field(
        default_factory=list,
    )

    data_quality: DataQuality = Field(
        default=DataQuality.INSUFFICIENT,
        description="Quality/coverage of the weather data used.",
    )

    confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description=(
            "Input-data coverage confidence from 0 to 1. "
            "This is not the probability of a weather event."
        ),
    )

    location_name: str | None = None

    timestamp: datetime