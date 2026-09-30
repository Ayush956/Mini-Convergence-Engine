"""Tests for the Vedic Vara, focused on the sunrise day boundary.

The boundary is the whole point of this calculation, so most of these cases
sit either side of 06:00 rather than testing the weekday lookup, which is
just datetime.
"""

from datetime import date, time

import pytest

from app.engine.vara import ASSUMED_SUNRISE, _VARAS, vara


def test_every_weekday_has_exactly_one_lord():
    assert len(_VARAS) == 7
    assert len({planet for _, _, planet in _VARAS}) == 7
    assert len({weekday for _, weekday, _ in _VARAS}) == 7


def test_traditional_lord_assignments():
    """Sunday is the Sun's, Monday the Moon's, Saturday Saturn's."""
    lords = {weekday: planet for _, weekday, planet in _VARAS}
    assert lords["Sunday"] == "Sun"
    assert lords["Monday"] == "Moon"
    assert lords["Tuesday"] == "Mars"
    assert lords["Wednesday"] == "Mercury"
    assert lords["Thursday"] == "Jupiter"
    assert lords["Friday"] == "Venus"
    assert lords["Saturday"] == "Saturn"


def test_daytime_birth_keeps_its_calendar_weekday():
    """15 Aug 1995 was a Tuesday, so a morning birth is Mangalavara."""
    result = vara(date(1995, 8, 15), time(10, 30))

    assert result.weekday == "Tuesday"
    assert result.name == "Mangalavara"
    assert result.planet == "Mars"
    assert result.shifted_by_sunrise is False
    assert result.vedic_date == date(1995, 8, 15)


def test_birth_before_sunrise_belongs_to_the_previous_vara():
    """02:00 Tuesday is still Monday in the Vedic reckoning."""
    result = vara(date(1995, 8, 15), time(2, 0))

    assert result.weekday == "Monday"
    assert result.name == "Somavara"
    assert result.planet == "Moon"
    assert result.shifted_by_sunrise is True
    assert result.vedic_date == date(1995, 8, 14)


@pytest.mark.parametrize(
    "birth_time,expected_weekday,shifted",
    [
        (time(0, 0), "Monday", True),
        (time(5, 59), "Monday", True),
        # 06:00 exactly starts the new vara rather than ending the old one.
        (time(6, 0), "Tuesday", False),
        (time(6, 1), "Tuesday", False),
        (time(23, 59), "Tuesday", False),
    ],
)
def test_sunrise_boundary_is_inclusive_of_six(birth_time, expected_weekday, shifted):
    result = vara(date(1995, 8, 15), birth_time)
    assert result.weekday == expected_weekday
    assert result.shifted_by_sunrise is shifted


def test_midnight_is_the_previous_day():
    """A birth at exactly 00:00 is the clearest case of the rule biting."""
    result = vara(date(1995, 8, 15), time(0, 0))
    assert result.vedic_date == date(1995, 8, 14)
    assert result.shifted_by_sunrise is True


def test_shift_crosses_a_month_boundary():
    result = vara(date(1995, 9, 1), time(3, 0))
    assert result.vedic_date == date(1995, 8, 31)


def test_shift_crosses_a_year_boundary():
    result = vara(date(1996, 1, 1), time(3, 0))
    assert result.vedic_date == date(1995, 12, 31)


def test_shift_lands_on_a_leap_day():
    """1 March 2000 before sunrise must fall back onto 29 February."""
    result = vara(date(2000, 3, 1), time(4, 30))
    assert result.vedic_date == date(2000, 2, 29)
    assert result.weekday == "Tuesday"


def test_assumed_sunrise_is_the_documented_six_am():
    """Guards the assumption itself, so changing it is a deliberate act."""
    assert ASSUMED_SUNRISE == time(6, 0)
