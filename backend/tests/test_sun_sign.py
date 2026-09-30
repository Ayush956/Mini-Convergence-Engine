"""Tests for the Western sun sign.

The reference longitudes are real JPL Horizons output, quantity 31
(ObsEcLon), target Sun (COMMAND=10), observer the geocentre (CENTER=500@399).
They were captured once by backend/scripts/check_against_horizons.py and
frozen here so the suite stays offline and deterministic.

Tolerance is 0.01 degrees, which is the accuracy Meeus states for this
method. Our worst observed disagreement across 1901-2099 was 0.0053 degrees,
so the tolerance is not being quietly widened to make the tests pass.
"""

from datetime import date, datetime, time, timedelta

import pytest

from app.engine.sun_sign import (
    ASSUMED_UTC_OFFSET_HOURS,
    SIGNS,
    apparent_solar_longitude,
    julian_day,
    sun_sign,
)

# Meeus's stated accuracy for the low-accuracy solar method.
TOLERANCE_DEGREES = 0.01

HORIZONS_REFERENCE = [
    (datetime(1995, 8, 15, 5, 0), 141.9185610),
    (datetime(2000, 1, 1, 12, 0), 280.3689092),
    (datetime(2026, 9, 30, 16, 0), 187.5112222),
    (datetime(1950, 1, 3, 18, 30), 282.8284343),
    (datetime(1901, 3, 1, 0, 0), 339.7335325),
    (datetime(2099, 11, 11, 11, 11), 229.3695884),
    # The 2024 cardinal points, where Horizons itself returns essentially
    # 0, 90, 180 and 270 - a useful independent check that quantity 31 is
    # the right quantity and these are the right moments.
    (datetime(2024, 3, 20, 3, 6), 359.9997093),
    (datetime(2024, 6, 20, 20, 51), 89.9999893),
    (datetime(2024, 9, 22, 12, 43), 179.9995392),
    (datetime(2024, 12, 21, 9, 20), 269.9995842),
]


def test_julian_day_epoch():
    """J2000.0 is 2000 Jan 1.5 TT, i.e. JD 2451545.0. Meeus chapter 7."""
    assert julian_day(datetime(2000, 1, 1, 12, 0)) == pytest.approx(2451545.0)


@pytest.mark.parametrize(
    "moment,expected",
    [
        # Meeus's own worked examples for the Julian Day conversion.
        (datetime(1957, 10, 4, 19, 26, 24), 2436116.31),
        (datetime(1987, 1, 27, 0, 0), 2446822.5),
        (datetime(1988, 6, 19, 12, 0), 2447332.0),
    ],
)
def test_julian_day_known_values(moment, expected):
    assert julian_day(moment) == pytest.approx(expected, abs=0.01)


def test_julian_day_handles_the_january_february_shift():
    """Meeus moves Jan and Feb into the previous year; an off-by-one here
    would shift every winter birth by a year."""
    assert julian_day(datetime(1988, 1, 27, 0, 0)) == pytest.approx(2447187.5)
    assert julian_day(datetime(1988, 2, 27, 0, 0)) == pytest.approx(2447218.5)
    assert julian_day(datetime(1988, 3, 27, 0, 0)) == pytest.approx(2447247.5)


@pytest.mark.parametrize("moment,reference", HORIZONS_REFERENCE)
def test_longitude_matches_jpl_horizons(moment, reference):
    ours = apparent_solar_longitude(moment)
    # Compare as an angle so a wrap at 360 does not read as a huge error.
    difference = abs((ours - reference + 180) % 360 - 180)
    assert difference < TOLERANCE_DEGREES, (
        "{}: ours {:.6f} vs Horizons {:.6f}, off by {:.6f} deg".format(
            moment, ours, reference, difference
        )
    )


def test_cardinal_points_are_where_the_seasons_say_they_are():
    """Equinoxes at 0 and 180, solstices at 90 and 270."""
    for moment, expected in (
        (datetime(2024, 3, 20, 3, 6), 0.0),
        (datetime(2024, 6, 20, 20, 51), 90.0),
        (datetime(2024, 9, 22, 12, 43), 180.0),
        (datetime(2024, 12, 21, 9, 20), 270.0),
    ):
        longitude = apparent_solar_longitude(moment)
        difference = abs((longitude - expected + 180) % 360 - 180)
        assert difference < 0.01, (moment, longitude)


def test_longitude_is_always_normalised():
    for year in (1901, 1950, 2000, 2026, 2100):
        for month in range(1, 13):
            longitude = apparent_solar_longitude(datetime(year, month, 15, 12))
            assert 0.0 <= longitude < 360.0


def test_longitude_advances_monotonically_over_a_year():
    """Roughly one degree a day, wrapping exactly once."""
    previous = apparent_solar_longitude(datetime(2024, 1, 1))
    wraps = 0
    for day in range(1, 366):
        moment = datetime(2024, 1, 1) + timedelta(days=day)
        current = apparent_solar_longitude(moment)
        if current < previous:
            wraps += 1
        else:
            assert 0.9 < current - previous < 1.1, moment
        previous = current
    assert wraps == 1


def test_there_are_twelve_signs_starting_at_aries():
    assert len(SIGNS) == 12
    assert SIGNS[0] == "Aries"
    assert SIGNS[6] == "Libra"
    assert SIGNS[-1] == "Pisces"


@pytest.mark.parametrize(
    "birth_date,birth_time,expected",
    [
        # 10:30 IST is 05:00 UTC, longitude 141.9, which is 4 signs and
        # 21.9 degrees, so Leo.
        (date(1995, 8, 15), time(10, 30), "Leo"),
        (date(2000, 6, 1), time(12, 0), "Gemini"),
        (date(2026, 9, 30), time(21, 30), "Libra"),
        (date(1950, 1, 4), time(0, 0), "Capricorn"),
    ],
)
def test_sun_sign_known_answers(birth_date, birth_time, expected):
    assert sun_sign(birth_date, birth_time).sign == expected


def test_sign_index_follows_longitude_exactly():
    """sign = floor(longitude / 30), with no fencepost error at a boundary."""
    for birth_date, birth_time in (
        (date(1995, 8, 15), time(10, 30)),
        (date(2024, 3, 20), time(8, 36)),
        (date(2024, 12, 21), time(14, 50)),
    ):
        result = sun_sign(birth_date, birth_time)
        assert SIGNS[int(result.longitude // 30)] == result.sign
        assert 0.0 <= result.degrees_into_sign < 30.0


def test_cusp_birth_is_flagged_and_placed_by_longitude():
    """The 2024 March equinox is 03:06 UTC, which is 08:36 IST.

    Just after it the Sun is barely into Aries; a few hours before, it is
    still at the very end of Pisces. A fixed table of sign date ranges
    cannot make this distinction, which is why longitude is computed.
    """
    just_after = sun_sign(date(2024, 3, 20), time(8, 40))
    just_before = sun_sign(date(2024, 3, 20), time(7, 30))

    assert just_after.sign == "Aries"
    assert just_after.degrees_into_sign < 0.1
    assert just_after.near_cusp is True

    assert just_before.sign == "Pisces"
    assert just_before.degrees_into_sign > 29.9
    assert just_before.near_cusp is True


def test_mid_sign_birth_is_not_flagged_as_a_cusp():
    result = sun_sign(date(1995, 8, 7), time(12, 0))
    assert result.sign == "Leo"
    assert result.near_cusp is False
    assert result.hours_to_cusp > 24.0


def test_hours_to_cusp_is_never_negative_or_absurd():
    """At most half a sign away, which is 15 degrees or about 15 days."""
    for month in range(1, 13):
        for day in (1, 11, 21):
            result = sun_sign(date(2024, month, day), time(12, 0))
            assert 0.0 <= result.hours_to_cusp <= 15.0 / 0.9856 * 24.0 + 1.0


def test_timezone_assumption_is_the_documented_ist():
    """A test rather than a comment, so changing it is deliberate."""
    assert ASSUMED_UTC_OFFSET_HOURS == 5.5


def test_timezone_assumption_actually_shifts_the_longitude():
    """Guards against the offset being silently ignored.

    The shift must equal 5.5 hours of real solar motion. Note that the mean
    rate of 0.9856 deg/day is not accurate enough to assert against directly:
    Earth's orbit is eccentric, so apparent solar motion runs from about
    0.953 deg/day near aphelion in early July to about 1.020 near perihelion
    in early January. This case is mid-August, close to aphelion, so the true
    shift is at the slow end of that band.
    """
    read_as_utc = apparent_solar_longitude(datetime(1995, 8, 15, 10, 30))
    read_as_ist = apparent_solar_longitude(datetime(1995, 8, 15, 5, 0))
    shift = read_as_utc - read_as_ist

    slowest = 5.5 / 24 * 0.953
    fastest = 5.5 / 24 * 1.020
    assert slowest <= shift <= fastest, shift

    # And confirm the eccentricity really is what makes the mean rate wrong
    # here, by checking January moves faster than August over the same span.
    january = apparent_solar_longitude(
        datetime(1995, 1, 15, 10, 30)
    ) - apparent_solar_longitude(datetime(1995, 1, 15, 5, 0))
    assert january > shift
