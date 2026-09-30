"""Numerology Life Path number, Pythagorean system.

Reduction order is component-first: month, day and year are each reduced
separately before being summed. Master numbers 11, 22 and 33 are preserved
rather than reduced further.

This is a documented assumption, not a correctness claim. The authorities
split, and the two reduction orders disagree on 13.4% of birth dates. See
docs/decisions.md for the measurement and the reasoning.
"""

from datetime import date
from typing import List, NamedTuple

MASTER_NUMBERS = frozenset({11, 22, 33})


class LifePath(NamedTuple):
    """A Life Path result along with the working that produced it.

    The steps exist so the UI can show how the number was reached, which
    matters more here than usual: the value depends on a contested
    convention, so showing the derivation is part of being honest about it.
    """

    value: int
    month: int
    day: int
    year: int
    steps: List[str]


def reduce_number(value: int) -> int:
    """Sum digits repeatedly until a single digit or a master number.

    Stopping on 11, 22 and 33 at every level is what makes this
    component-first rather than a plain digit sum.
    """
    if value < 0:
        raise ValueError("cannot reduce a negative number")
    while value > 9 and value not in MASTER_NUMBERS:
        value = sum(int(digit) for digit in str(value))
    return value


def _describe(label: str, original: int, reduced: int) -> str:
    if original == reduced:
        return "{} {} is already reduced".format(label, original)
    return "{} {} reduces to {}".format(label, original, reduced)


def life_path(birth_date: date) -> LifePath:
    """Life Path number for a birth date."""
    month = reduce_number(birth_date.month)
    day = reduce_number(birth_date.day)
    year = reduce_number(birth_date.year)

    total = month + day + year
    value = reduce_number(total)

    steps = [
        _describe("month", birth_date.month, month),
        _describe("day", birth_date.day, day),
        _describe("year", birth_date.year, year),
        "{} + {} + {} = {}".format(month, day, year, total),
    ]
    if value != total:
        steps.append("{} reduces to {}".format(total, value))
    if value in MASTER_NUMBERS:
        steps.append("{} is a master number, so it is left unreduced".format(value))

    return LifePath(value=value, month=month, day=day, year=year, steps=steps)
