"""Orchestrates the five methods into one reading.

This module does no domain arithmetic of its own. It runs each calculator,
asks the trait rubric to score each result, runs the convergence arithmetic,
and assembles the response. Keeping it thin means the interesting logic stays
in the modules that are individually tested.
"""

from datetime import date, time
from typing import Dict, List, Tuple

from app.engine import traits as trait_rubric
from app.engine.chinese_zodiac import chinese_zodiac
from app.engine.convergence import converge
from app.engine.life_path import life_path
from app.engine.name_number import name_number
from app.engine.sun_sign import ASSUMED_UTC_OFFSET_HOURS, sun_sign
from app.engine.vara import ASSUMED_SUNRISE, vara

METHOD_LABELS = {
    "sun_sign": "Western Sun Sign",
    "chinese_zodiac": "Chinese Zodiac",
    "life_path": "Numerology Life Path",
    "name_number": "Name Number (Chaldean)",
    "vara": "Vedic Vara",
}

# Order the five appear in the brief, which is the order the UI shows them.
METHOD_ORDER = ("sun_sign", "chinese_zodiac", "life_path", "name_number", "vara")


class ReadingError(ValueError):
    """A calculation could not be completed for the given input."""


def build_reading(
    full_name: str, birth_date: date, birth_time: time
) -> Tuple[List[dict], List[dict], List[str]]:
    """Run all five methods and converge them.

    Returns the per-method results, the per-trait convergence rows, and the
    list of assumptions that applied to this particular reading.
    """
    try:
        sun = sun_sign(birth_date, birth_time)
        animal = chinese_zodiac(birth_date)
        path = life_path(birth_date)
        name = name_number(full_name)
        day = vara(birth_date, birth_time)
    except ValueError as error:
        raise ReadingError(str(error))

    scored = {
        "sun_sign": trait_rubric.score_sun_sign(sun.sign),
        "chinese_zodiac": trait_rubric.score_chinese_zodiac(animal.animal),
        "life_path": trait_rubric.score_life_path(path.value),
        "name_number": trait_rubric.score_name_number(name.value),
        "vara": trait_rubric.score_vara(day.planet),
    }

    results = {
        "sun_sign": (
            sun.sign,
            "The Sun was at {:.2f} degrees of ecliptic longitude, which is "
            "{:.1f} degrees into {}.".format(
                sun.longitude, sun.degrees_into_sign, sun.sign
            ),
        ),
        "chinese_zodiac": (
            animal.animal,
            "The Chinese year {} ({}) began on {}, so this birth falls in the "
            "year of the {}.".format(
                animal.zodiac_year,
                animal.ganzhi,
                animal.new_year_date.isoformat(),
                animal.animal,
            ),
        ),
        "life_path": (
            str(path.value),
            "; ".join(path.steps) + ".",
        ),
        "name_number": (
            str(name.value),
            "Letters total {}, and the name parts reduce to a compound of {}, "
            "giving {}.".format(name.letter_total, name.compound, name.value),
        ),
        "vara": (
            "{} ({})".format(day.name, day.planet),
            "The Vedic day runs sunrise to sunrise, so this birth belongs to "
            "{}, ruled by {}.".format(day.weekday, day.planet),
        ),
    }

    methods = []
    for method_id in METHOD_ORDER:
        value, detail = results[method_id]
        rubric = scored[method_id]
        methods.append(
            {
                "id": method_id,
                "label": METHOD_LABELS[method_id],
                "result": value,
                "detail": detail,
                "basis": rubric.basis,
                "notes": rubric.notes,
                "scores": rubric.scores,
            }
        )

    rows = converge(
        trait_rubric.TRAITS,
        {method_id: scored[method_id].scores for method_id in METHOD_ORDER},
    )

    traits = [
        {
            "trait": row.trait,
            "scores": row.scores,
            "agreeing": row.agreeing,
            "n": row.n,
            "confidence": row.confidence,
        }
        for row in rows
    ]

    return methods, traits, _assumptions(birth_date, sun, animal, name, day)


def _assumptions(birth_date: date, sun, animal, name, day) -> List[str]:
    """Assumptions that actually applied to this reading.

    Only the ones that bit are listed, so the user sees what affected their
    result rather than a generic disclaimer they will skip.
    """
    notes = [
        "The brief collects a time of birth but no place, so the time is "
        "assumed to be IST (UTC+{:g}).".format(ASSUMED_UTC_OFFSET_HOURS),
    ]

    if sun.near_cusp:
        notes.append(
            "This birth is about {:.0f} hours from a sign cusp. Because the "
            "timezone above is an assumption, the neighbouring sign is "
            "genuinely possible.".format(sun.hours_to_cusp)
        )

    if day.shifted_by_sunrise:
        notes.append(
            "The Vedic day begins at sunrise, so this birth before {} belongs "
            "to the previous day: the vara is taken from {}, not {}. True "
            "sunrise needs a birthplace, so {} stands in for it.".format(
                ASSUMED_SUNRISE.strftime("%H:%M"),
                day.vedic_date.isoformat(),
                birth_date.isoformat(),
                ASSUMED_SUNRISE.strftime("%H:%M"),
            )
        )

    if animal.born_before_new_year:
        notes.append(
            "This birth is before Chinese New Year ({}), so the animal is the "
            "previous year's. A plain year-modulo-12 calculation would get "
            "this wrong.".format(animal.new_year_date.isoformat())
        )

    if name.ignored_characters:
        notes.append(
            "The Chaldean table has no value for {}, so those characters were "
            "ignored in the name number.".format(
                ", ".join(repr(c) for c in name.ignored_characters)
            )
        )

    return notes
