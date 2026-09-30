"""Chinese Zodiac animal for a birth date.

The Chinese year begins at Chinese New Year, which falls between 21 January
and 20 February, not on 1 January. So `year % 12` is wrong for anyone born in
January or early February - they belong to the previous animal year. That is
not a rare edge case: it is roughly one birthday in nine.

The New Year date is astronomically defined and cannot be derived by simple
arithmetic, so it comes from a table generated from the Hong Kong Observatory
conversion tables. See app/data/cny_dates.py for provenance.
"""

from datetime import date
from typing import NamedTuple

from app.data.cny_dates import FIRST_YEAR, LAST_YEAR, NEW_YEARS


class ChineseZodiac(NamedTuple):
    """A zodiac result, with the year boundary that decided it."""

    animal: str
    ganzhi: str
    zodiac_year: int
    new_year_date: date
    born_before_new_year: bool


def new_year_date(year: int) -> date:
    """The Gregorian date on which the given Chinese year begins."""
    if year not in NEW_YEARS:
        raise ValueError(
            "no Chinese New Year data for {}; the table covers {}-{}".format(
                year, FIRST_YEAR, LAST_YEAR
            )
        )
    month, day, _, _ = NEW_YEARS[year]
    return date(year, month, day)


def chinese_zodiac(birth_date: date) -> ChineseZodiac:
    """Zodiac animal for a birth date, respecting the Chinese year boundary.

    A birth on or after Chinese New Year takes that year's animal. A birth
    before it takes the previous year's, which is why the previous year must
    also be in the table - hence the effective range starts at 1902.
    """
    boundary = new_year_date(birth_date.year)
    before = birth_date < boundary

    zodiac_year = birth_date.year - 1 if before else birth_date.year
    if zodiac_year not in NEW_YEARS:
        raise ValueError(
            "birth on {} falls in Chinese year {}, which is outside the "
            "table range {}-{}".format(birth_date, zodiac_year, FIRST_YEAR, LAST_YEAR)
        )

    _, _, ganzhi, animal = NEW_YEARS[zodiac_year]
    return ChineseZodiac(
        animal=animal,
        ganzhi=ganzhi,
        zodiac_year=zodiac_year,
        new_year_date=boundary,
        born_before_new_year=before,
    )
