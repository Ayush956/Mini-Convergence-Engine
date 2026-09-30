"""Western (tropical) Sun sign from the Sun's apparent ecliptic longitude.

Algorithm: Meeus, "Astronomical Algorithms", chapter 25, the low-accuracy
solar method, with the Julian Day conversion from chapter 7. Meeus states the
accuracy of this method as about 0.01 degrees of longitude. At the Sun's mean
motion of roughly 0.9856 degrees per day that is about 15 minutes of clock
time at a sign cusp.

That is not the dominant error. The brief collects a time of birth with no
location, so the civil time has to be assumed to be IST, and an unknown
birthplace can put the true local time out by hours. The formula is far more
accurate than the timezone assumption it is fed.

Signs are the tropical twelve, each exactly 30 degrees measured from the
vernal equinox, so the sign is floor(longitude / 30).
"""

import math
from datetime import date, datetime, time
from typing import NamedTuple

# The brief collects no birth location, so civil time is assumed to be IST.
# Kept explicit rather than buried, because it is the largest single source
# of error in this calculation.
ASSUMED_UTC_OFFSET_HOURS = 5.5

SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Degrees of solar longitude per day, used only to estimate how far a birth
# sits from its nearest cusp.
_MEAN_DAILY_MOTION = 0.9856


class SunSign(NamedTuple):
    """A sun sign with the longitude that produced it and cusp proximity."""

    sign: str
    longitude: float
    degrees_into_sign: float
    hours_to_cusp: float
    near_cusp: bool


def julian_day(moment: datetime) -> float:
    """Julian Day for a UTC datetime. Meeus chapter 7, Gregorian calendar."""
    year = moment.year
    month = moment.month
    day = (
        moment.day
        + moment.hour / 24.0
        + moment.minute / 1440.0
        + moment.second / 86400.0
    )

    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year / 100.0)
    b = 2 - a + math.floor(a / 4.0)

    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )


def apparent_solar_longitude(moment: datetime) -> float:
    """The Sun's apparent geocentric ecliptic longitude, in degrees.

    `moment` must be UTC. The returned value is referred to the ecliptic and
    mean equinox of date, corrected for nutation and aberration, which is the
    same quantity JPL Horizons reports as ObsEcLon for target Sun seen from
    the geocentre.
    """
    t = (julian_day(moment) - 2451545.0) / 36525.0

    # Geometric mean longitude of the Sun.
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t

    # Mean anomaly of the Sun.
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    m_rad = math.radians(m)

    # Equation of the centre.
    c = (
        (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
        + 0.000289 * math.sin(3 * m_rad)
    )

    true_longitude = l0 + c

    # Correction to apparent longitude: constant aberration plus the
    # longitude term of nutation, via the Moon's ascending node.
    omega = math.radians(125.04 - 1934.136 * t)
    apparent = true_longitude - 0.00569 - 0.00478 * math.sin(omega)

    return apparent % 360.0


def sun_sign(birth_date: date, birth_time: time) -> SunSign:
    """Tropical sun sign for a birth date and local (assumed IST) time."""
    local = datetime.combine(birth_date, birth_time)
    utc = local - _offset()

    longitude = apparent_solar_longitude(utc)
    index = int(longitude // 30)
    degrees_into_sign = longitude - index * 30

    # Distance to whichever cusp is nearer, expressed in hours.
    degrees_to_next = 30.0 - degrees_into_sign
    degrees_to_cusp = min(degrees_into_sign, degrees_to_next)
    hours_to_cusp = degrees_to_cusp / _MEAN_DAILY_MOTION * 24.0

    return SunSign(
        sign=SIGNS[index],
        longitude=longitude,
        degrees_into_sign=degrees_into_sign,
        hours_to_cusp=hours_to_cusp,
        # Within a day of a cusp, the timezone assumption could plausibly
        # have put the birth in the neighbouring sign.
        near_cusp=hours_to_cusp < 24.0,
    )


def _offset():
    from datetime import timedelta

    return timedelta(hours=ASSUMED_UTC_OFFSET_HOURS)
