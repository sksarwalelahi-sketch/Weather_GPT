"""
WeatherGPT - Member 3
Risk Assessment Schemas

Defines standardized structures for representing individual
weather risks and overall risk assessments.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class RiskLevel(str, Enum):
    """
    Standard severity levels used throughout the
    WeatherGPT intelligence engine.
    """

    NORMAL = "NORMAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class RiskComponent(BaseModel):
    """
    Represents an individual weather-related risk component.

    Example:
        Rainfall → HIGH → score 85
        Wind     → MODERATE → score 60
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    risk_type: str = Field(
        ...,
        min_length=1,
        description="Type of weather risk, such as rainfall, wind, or heat."
    )

    level: RiskLevel = Field(
        ...,
        description="Severity level of this individual risk."
    )

    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Normalized risk score from 0 to 100."
    )

    reason: str = Field(
        ...,
        min_length=1,
        description="Explanation for why this risk level was assigned."
    )


class RiskAssessment(BaseModel):
    """
    Complete weather risk assessment produced by the
    Member 3 Risk Engine.
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    overall_level: RiskLevel = Field(
        ...,
        description="Overall weather risk severity."
    )

    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall normalized risk score from 0 to 100."
    )

    components: list[RiskComponent] = Field(
        default_factory=list,
        description="Individual weather risk components."
    )

    location_name: str | None = Field(
        default=None,
        description="Location associated with the risk assessment."
    )

    timestamp: datetime = Field(
        ...,
        description="Time at which the risk assessment was generated."
    )