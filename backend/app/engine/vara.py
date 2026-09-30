"""Vedic Vara: the weekday of birth and its ruling planet.

The Vedic civil day runs sunrise to sunrise, not midnight to midnight. The
authority is the Report of the Calendar Reform Committee (Government of
India, CSIR, 1955), which states that "the civil day (savana), according to
Hindu religious practices, should start from sunrise" and elsewhere defines
the savana day as running "between sunrise to sunrise".

So a birth at 02:00 on a Tuesday belongs to Monday's vara. This is the only
calculation in the engine where the time of birth changes the answer
outright.

True sunrise needs a birth location, which the brief never collects, so a
fixed 06:00 stands in. That assumption is the dominant source of error here:
a birth between true local sunrise and 06:00, or the reverse, lands on the
neighbouring vara. Documented rather than hidden.
"""

from datetime import date, time, timedelta
from typing import NamedTuple

# The stand-in for true local sunrise, in the absence of a birth location.
ASSUMED_SUNRISE = time(6, 0)

# Indexed by date.weekday(), where Monday is 0.
# The planetary lords are uncontested across sources; the ordering follows
# the hora sequence, in which the lord of the first hora after sunrise rules
# the whole day.
_VARAS = (
    ("Somavara", "Monday", "Moon"),
    ("Mangalavara", "Tuesday", "Mars"),
    ("Budhavara", "Wednesday", "Mercury"),
    ("Guruvara", "Thursday", "Jupiter"),
    ("Shukravara", "Friday", "Venus"),
    ("Shanivara", "Saturday", "Saturn"),
    ("Ravivara", "Sunday", "Sun"),
)


class Vara(NamedTuple):
    """A vara result, including whether the sunrise rule moved the day."""

    name: str
    weekday: str
    planet: str
    vedic_date: date
    shifted_by_sunrise: bool


def vara(birth_date: date, birth_time: time) -> Vara:
    """The vara for a birth date and time.

    A birth before the assumed sunrise belongs to the previous Vedic day.
    06:00 exactly is the start of the new vara, not the end of the old one.
    """
    shifted = birth_time < ASSUMED_SUNRISE
    vedic_date = birth_date - timedelta(days=1) if shifted else birth_date

    name, weekday, planet = _VARAS[vedic_date.weekday()]
    return Vara(
        name=name,
        weekday=weekday,
        planet=planet,
        vedic_date=vedic_date,
        shifted_by_sunrise=shifted,
    )
