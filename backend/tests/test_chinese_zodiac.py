"""Tests for the Chinese Zodiac, focused on the New Year boundary.

The interesting failure mode here is not the animal lookup but the year
boundary, so most cases sit either side of Chinese New Year.
"""

from datetime import date, timedelta

import pytest

from app.data.cny_dates import FIRST_YEAR, LAST_YEAR, NEW_YEARS
from app.engine.chinese_zodiac import chinese_zodiac, new_year_date

ANIMAL_CYCLE = [
    "Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
    "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig",
]


def test_table_covers_two_centuries():
    assert FIRST_YEAR == 1901
    assert LAST_YEAR == 2100
    assert len(NEW_YEARS) == 200


def test_every_new_year_falls_in_the_documented_window():
    """HKO documents Chinese New Year as falling between 21 Jan and 20 Feb."""
    for year, (month, day, _, _) in NEW_YEARS.items():
        assert month in (1, 2), year
        if month == 1:
            assert day >= 21, year
        else:
            assert day <= 20, year


def test_animal_cycle_advances_by_one_each_year():
    """A break here would mean the generated table is corrupt."""
    years = sorted(NEW_YEARS)
    for previous, current in zip(years, years[1:]):
        previous_animal = NEW_YEARS[previous][3]
        current_animal = NEW_YEARS[current][3]
        expected = ANIMAL_CYCLE[(ANIMAL_CYCLE.index(previous_animal) + 1) % 12]
        assert current_animal == expected, current


@pytest.mark.parametrize(
    "year,expected",
    [
        (1995, date(1995, 1, 31)),
        (2000, date(2000, 2, 5)),
        (2011, date(2011, 2, 3)),
        (2026, date(2026, 2, 17)),
    ],
)
def test_known_new_year_dates(year, expected):
    assert new_year_date(year) == expected


@pytest.mark.parametrize(
    "birth_date,expected",
    [
        # Well-known years, sampled after the New Year boundary.
        (date(2000, 6, 1), "Dragon"),
        (date(2026, 6, 1), "Horse"),
        (date(1995, 8, 15), "Pig"),
    ],
)
def test_animal_for_mid_year_births(birth_date, expected):
    assert chinese_zodiac(birth_date).animal == expected


def test_january_birth_takes_the_previous_animal():
    """2000 was the Dragon, but 1 Jan 2000 is still in the Rabbit year.

    Chinese New Year 2000 was 5 February, so the whole of January belongs to
    the year that began in February 1999. This is the case a naive
    `year % 12` gets wrong.
    """
    result = chinese_zodiac(date(2000, 1, 1))

    assert result.animal == "Rabbit"
    assert result.zodiac_year == 1999
    assert result.born_before_new_year is True


def test_boundary_day_itself_belongs_to_the_new_year():
    """5 Feb 2000 is Chinese New Year, so it is already the Dragon."""
    day_before = chinese_zodiac(date(2000, 2, 4))
    boundary = chinese_zodiac(date(2000, 2, 5))

    assert day_before.animal == "Rabbit"
    assert day_before.born_before_new_year is True
    assert boundary.animal == "Dragon"
    assert boundary.born_before_new_year is False


def test_every_boundary_in_the_table_flips_exactly_one_animal():
    """Walk all 199 usable boundaries and check the transition each time."""
    for year in range(FIRST_YEAR + 1, LAST_YEAR + 1):
        boundary = new_year_date(year)

        before = chinese_zodiac(boundary - timedelta(days=1))
        on = chinese_zodiac(boundary)

        assert before.zodiac_year == year - 1, year
        assert on.zodiac_year == year, year

        expected = ANIMAL_CYCLE[(ANIMAL_CYCLE.index(before.animal) + 1) % 12]
        assert on.animal == expected, year


def test_late_february_is_always_the_current_year():
    """21 Feb is past the latest possible New Year, so never shifts back."""
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        result = chinese_zodiac(date(year, 2, 21))
        assert result.zodiac_year == year, year
        assert result.born_before_new_year is False, year


def test_date_outside_the_table_is_rejected_clearly():
    with pytest.raises(ValueError) as error:
        chinese_zodiac(date(1900, 6, 1))
    assert "1901" in str(error.value)


def test_first_table_year_before_its_new_year_is_rejected():
    """1901 is the first row, so January 1901 needs 1900 data we do not have.

    Better an explicit error than silently returning the wrong animal.
    """
    with pytest.raises(ValueError):
        chinese_zodiac(date(1901, 1, 1))
