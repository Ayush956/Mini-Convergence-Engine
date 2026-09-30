"""Request and response models for the API.

Python 3.9 compatible throughout: Optional[X] and List[X], never X | None,
because PEP 604 unions fail wherever Pydantic evaluates the annotation.
"""

from datetime import date, time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# The HKO-derived Chinese New Year table bounds what we can answer for.
# 1902 rather than 1901 because a January 1901 birth would need 1900 data.
EARLIEST_YEAR = 1902
LATEST_YEAR = 2100

MAX_NAME_LENGTH = 120


class ReadingRequest(BaseModel):
    """The three inputs the brief specifies."""

    full_name: str = Field(..., description="Full name, used for the Chaldean name number")
    date_of_birth: date = Field(..., description="Calendar date of birth")
    time_of_birth: time = Field(..., description="Local time of birth, assumed IST")

    @field_validator("full_name")
    @classmethod
    def name_must_contain_a_letter(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Please enter a name.")
        if len(trimmed) > MAX_NAME_LENGTH:
            raise ValueError(
                "That name is longer than {} characters.".format(MAX_NAME_LENGTH)
            )
        if not any(character.isalpha() for character in trimmed):
            raise ValueError(
                "A name needs at least one letter, so we can score it."
            )
        return trimmed

    @field_validator("date_of_birth")
    @classmethod
    def date_must_be_in_supported_range(cls, value: date) -> date:
        if value.year < EARLIEST_YEAR or value.year > LATEST_YEAR:
            raise ValueError(
                "We can only calculate for births between {} and {}, because "
                "that is the range of the Chinese calendar data we "
                "verified.".format(EARLIEST_YEAR, LATEST_YEAR)
            )
        return value


class MethodResult(BaseModel):
    """One divination system's result and its trait scores."""

    id: str
    label: str
    result: str
    detail: str
    basis: str
    notes: List[str] = []
    scores: Dict[str, int]


class TraitRow(BaseModel):
    """One trait dimension across all five methods."""

    trait: str
    scores: Dict[str, int]
    agreeing: List[str]
    n: int
    confidence: float


class ReadingResponse(BaseModel):
    """Everything the output screen needs, in one response."""

    full_name: str
    date_of_birth: date
    time_of_birth: time
    methods: List[MethodResult]
    traits: List[TraitRow]
    summary: str
    summary_source: str = Field(
        ...,
        description="Either 'model' or 'template', so the UI can be honest "
        "about whether the LLM call succeeded.",
    )
    assumptions: List[str]


class ErrorResponse(BaseModel):
    """A validation or calculation failure, phrased for a human."""

    message: str
    field: Optional[str] = None
