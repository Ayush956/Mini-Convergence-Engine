"""Known-answer tests for the Life Path calculation.

Expected values come from worked examples published by numerology
authorities, plus hand-computed cases for the boundaries. Sources are
recorded in docs/decisions.md.
"""

from datetime import date

import pytest

from app.engine.life_path import MASTER_NUMBERS, life_path, reduce_number


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, 1),
        (9, 9),
        (10, 1),
        (12, 3),
        (19, 1),
        (21, 3),
        # Master numbers stop the reduction where a naive loop would not.
        (11, 11),
        (22, 22),
        (33, 33),
        # 38 -> 11, which is a master number, so it stops there rather than
        # continuing to 2.
        (38, 11),
    ],
)
def test_reduce_number(value, expected):
    assert reduce_number(value) == expected


def test_reduce_number_rejects_negative():
    with pytest.raises(ValueError):
        reduce_number(-1)


@pytest.mark.parametrize(
    "birth_date,expected",
    [
        # Published worked example: March 15 1992 -> month 3, day 6, year 3.
        (date(1992, 3, 15), 3),
        # Published worked example: March 12 1940 -> 3 + 3 + 5 = 11, a master
        # number that must survive.
        (date(1940, 3, 12), 11),
        # Hand-computed. Also one of the dates where the flat-sum method
        # disagrees, which the test below pins down explicitly.
        (date(1950, 1, 4), 11),
        # Leap day: day 29 reduces to 11, so 2 + 11 + 2 = 15 -> 6.
        (date(2000, 2, 29), 6),
    ],
)
def test_life_path_known_answers(birth_date, expected):
    assert life_path(birth_date).value == expected


def test_life_path_preserves_master_number_from_components():
    """4 Jan 1950 is where our convention visibly differs from the alternative.

    Component-first: month 1, day 4, year 1950 -> 15 -> 6, so 1 + 4 + 6 = 11.
    Summing every digit instead gives 1+9+5+0+0+1+0+4 = 20 -> 2.

    We return 11. This test exists to make that a deliberate, locked-in
    choice rather than an accident, so a future change of reduction order
    fails loudly here.
    """
    result = life_path(date(1950, 1, 4))

    assert result.value == 11
    assert result.value in MASTER_NUMBERS

    flat_sum = sum(int(digit) for digit in "19500104")
    assert flat_sum == 20
    assert reduce_number(flat_sum) == 2
    assert result.value != reduce_number(flat_sum)


def test_life_path_exposes_its_working():
    result = life_path(date(1992, 3, 15))

    assert result.month == 3
    assert result.day == 6
    assert result.year == 3
    assert "3 + 6 + 3 = 12" in result.steps


def test_life_path_is_stable_across_the_whole_supported_range():
    """Every date must produce a valid Life Path, never an unreduced total."""
    valid = set(range(1, 10)) | MASTER_NUMBERS

    for year in (1901, 1950, 2000, 2026, 2100):
        for month in range(1, 13):
            result = life_path(date(year, month, 28))
            assert result.value in valid
