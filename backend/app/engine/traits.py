"""Trait mapping: each method's result scored 0-10 on six dimensions.

The six dimensions are fixed by the brief, as is the 0-10 range. The scores
are ours to design, and the brief says so: "You design the mapping... There
is no single correct mapping. What matters is that your choices are reasoned,
consistent, and documented with your sources."

Every possible result needs six scores, which is 12 signs + 12 animals +
12 Life Path values + 9 name numbers + 7 varas = 52 results and 312 scores.
Rather than inventing 312 numbers, they are derived wherever the tradition
supplies a structure to derive them from:

- Sun signs are composed. Every sign is one element crossed with one
  modality, so twelve signs come out of seven rules on a neutral base of 5.
  Leo's Leadership is not a number anyone typed; it is 5 plus the Fire
  contribution plus the Fixed contribution.
- Vara scores come from the ruling planet's significations. Seven planets,
  which is already the minimum.
- Life Path and name numbers come from the published meanings of each
  number, which are themselves the rubric - there is nothing to compress.
- Chinese animals come from their traditional trait lists. These have no
  compositional structure to exploit, so twelve rows are unavoidable.

Where the composed result contradicts well-attested tradition, SIGN_OVERRIDES
records a deliberate exception with its reason. Those exceptions are the
honest part: an additive rubric is a crude model of a tradition that is not
additive, and pretending otherwise would be worse than saying so.

See docs/decisions.md for the fuller rationale.
"""

from typing import Dict, List, NamedTuple, Tuple

# Fixed by the brief, in the order it lists them.
TRAITS: Tuple[str, ...] = (
    "Leadership",
    "Creativity",
    "Emotional depth",
    "Communication",
    "Discipline",
    "Risk appetite",
)

MIN_SCORE = 0
MAX_SCORE = 10

# Every trait starts neutral and is moved by the contributions below.
NEUTRAL = 5


class Scored(NamedTuple):
    """Trait scores plus the reasoning that produced them."""

    scores: Dict[str, int]
    basis: str
    notes: List[str]


def _vector(
    leadership: int,
    creativity: int,
    emotional_depth: int,
    communication: int,
    discipline: int,
    risk_appetite: int,
) -> Dict[str, int]:
    """Build a trait dict positionally, in the brief's trait order."""
    return dict(
        zip(
            TRAITS,
            (
                leadership,
                creativity,
                emotional_depth,
                communication,
                discipline,
                risk_appetite,
            ),
        )
    )


def clamp(value: int) -> int:
    return max(MIN_SCORE, min(MAX_SCORE, value))


# --------------------------------------------------------------------------
# Western sun signs: composed from element and modality.
# --------------------------------------------------------------------------

SIGN_ELEMENTS: Dict[str, str] = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

SIGN_MODALITIES: Dict[str, str] = {
    "Aries": "Cardinal", "Cancer": "Cardinal",
    "Libra": "Cardinal", "Capricorn": "Cardinal",
    "Taurus": "Fixed", "Leo": "Fixed",
    "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Mutable", "Virgo": "Mutable",
    "Sagittarius": "Mutable", "Pisces": "Mutable",
}

# Element significations: Fire assertive and enthusiastic, Earth practical
# and grounded, Air intellectual and sociable, Water feeling and intuitive.
ELEMENT_CONTRIBUTIONS: Dict[str, Dict[str, int]] = {
    "Fire": _vector(3, 2, -1, 1, -1, 3),
    "Earth": _vector(1, -1, 0, -1, 4, -2),
    "Air": _vector(0, 2, -1, 4, -1, 1),
    "Water": _vector(-1, 2, 4, 0, 0, -2),
}

# Modality significations: Cardinal initiates, Fixed persists, Mutable adapts.
MODALITY_CONTRIBUTIONS: Dict[str, Dict[str, int]] = {
    "Cardinal": _vector(3, 1, 0, 1, 1, 2),
    "Fixed": _vector(1, -1, 1, -1, 3, -1),
    "Mutable": _vector(-1, 2, 0, 2, -2, 1),
}

# Deliberate exceptions where the composed score understates a sign's
# best-attested quality. Kept few and kept explained.
SIGN_OVERRIDES: Dict[Tuple[str, str], Tuple[int, str]] = {
    ("Leo", "Creativity"): (
        9,
        "Fire plus Fixed composes to 6, but Leo is specifically the sign of "
        "self-expression, performance and display, which every source treats "
        "as central rather than incidental. The rubric has no term for "
        "theatricality, so it undercounts it.",
    ),
    ("Virgo", "Discipline"): (
        9,
        "Earth supplies discipline and Mutable subtracts it, composing to 7. "
        "But Virgo's meticulousness is its defining trait, and here Mutable "
        "describes adaptability of method rather than laxity of standard, so "
        "the subtraction is the wrong reading.",
    ),
    ("Scorpio", "Risk appetite"): (
        7,
        "Water plus Fixed composes to 2, treating Scorpio as risk-averse. "
        "That conflates caution with control: the tradition is unanimous that "
        "Scorpio will go to extremes, which is high risk appetite exercised "
        "deliberately rather than impulsively.",
    ),
}


def score_sun_sign(sign: str) -> Scored:
    """Compose a sign's trait scores from its element and its modality."""
    if sign not in SIGN_ELEMENTS:
        raise ValueError("unknown sign: {}".format(sign))

    element = SIGN_ELEMENTS[sign]
    modality = SIGN_MODALITIES[sign]

    scores: Dict[str, int] = {}
    notes: List[str] = []

    for trait in TRAITS:
        composed = (
            NEUTRAL
            + ELEMENT_CONTRIBUTIONS[element][trait]
            + MODALITY_CONTRIBUTIONS[modality][trait]
        )
        override = SIGN_OVERRIDES.get((sign, trait))
        if override is not None:
            value, reason = override
            scores[trait] = clamp(value)
            notes.append(
                "{}: overridden from {} to {}. {}".format(
                    trait, clamp(composed), clamp(value), reason
                )
            )
        else:
            scores[trait] = clamp(composed)

    return Scored(
        scores=scores,
        basis="{} is {} and {}, so each trait is 5 plus the {} contribution "
        "plus the {} contribution".format(sign, element, modality, element, modality),
        notes=notes,
    )


# --------------------------------------------------------------------------
# Chinese zodiac animals: from traditional trait lists.
# --------------------------------------------------------------------------

ANIMAL_SCORES: Dict[str, Dict[str, int]] = {
    # clever, resourceful, quick-witted, adaptable
    "Rat": _vector(5, 8, 5, 8, 6, 6),
    # diligent, dependable, determined, stubborn
    "Ox": _vector(6, 3, 5, 3, 10, 2),
    # brave, confident, competitive, unpredictable
    "Tiger": _vector(9, 6, 5, 6, 4, 9),
    # gentle, quiet, elegant, alert
    "Rabbit": _vector(3, 7, 8, 6, 6, 2),
    # confident, charismatic, ambitious, a natural leader
    "Dragon": _vector(10, 8, 5, 8, 6, 8),
    # enigmatic, wise, private, watchful
    "Snake": _vector(6, 7, 8, 4, 8, 4),
    # energetic, independent, free-spirited, impatient
    "Horse": _vector(7, 7, 4, 8, 3, 9),
    # gentle, compassionate, artistic, shy
    "Goat": _vector(3, 9, 9, 5, 5, 2),
    # sharp, curious, inventive, mischievous
    "Monkey": _vector(6, 9, 4, 9, 4, 8),
    # observant, hardworking, courageous, outspoken
    "Rooster": _vector(7, 5, 4, 9, 8, 6),
    # loyal, honest, responsible, cautious
    "Dog": _vector(6, 4, 8, 6, 8, 3),
    # generous, easy-going, sincere, indulgent
    "Pig": _vector(4, 6, 7, 6, 5, 4),
}


def score_chinese_zodiac(animal: str) -> Scored:
    if animal not in ANIMAL_SCORES:
        raise ValueError("unknown animal: {}".format(animal))
    return Scored(
        scores=dict(ANIMAL_SCORES[animal]),
        basis="from the traditional trait list for the {}".format(animal),
        notes=[],
    )


# --------------------------------------------------------------------------
# Numerology: Life Path values and Chaldean name numbers.
# --------------------------------------------------------------------------

LIFE_PATH_SCORES: Dict[int, Dict[str, int]] = {
    1: _vector(10, 6, 3, 6, 7, 8),    # the leader, independent, pioneering
    2: _vector(3, 5, 9, 8, 6, 2),     # the diplomat, cooperative, sensitive
    3: _vector(5, 10, 6, 10, 3, 6),   # the communicator, expressive, social
    4: _vector(6, 3, 4, 4, 10, 2),    # the builder, methodical, practical
    5: _vector(6, 8, 4, 8, 2, 10),    # the free spirit, change, adventure
    6: _vector(6, 6, 9, 7, 7, 3),     # the nurturer, responsible, harmonising
    7: _vector(4, 7, 8, 4, 8, 4),     # the seeker, analytical, introspective
    8: _vector(10, 5, 4, 7, 8, 8),    # the executive, authority, ambition
    9: _vector(6, 8, 10, 7, 5, 5),    # the humanitarian, compassionate
    # Master numbers are read as intensified forms of 2, 4 and 6, so they
    # inherit that shape with the intensity raised rather than being scored
    # from scratch.
    11: _vector(7, 9, 10, 8, 5, 5),   # intuitive visionary, master of 2
    22: _vector(9, 7, 6, 6, 10, 5),   # master builder, master of 4
    33: _vector(8, 8, 10, 10, 7, 4),  # master teacher, master of 6
}

# Cheiro attaches a planet to each single number, and the planet's
# significations are what these scores follow.
NAME_NUMBER_PLANETS: Dict[int, str] = {
    1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Uranus", 5: "Mercury",
    6: "Venus", 7: "Neptune", 8: "Saturn", 9: "Mars",
}

NAME_NUMBER_SCORES: Dict[int, Dict[str, int]] = {
    1: _vector(9, 6, 4, 6, 7, 7),    # Sun: authority, vitality
    2: _vector(4, 6, 9, 7, 5, 3),    # Moon: feeling, receptivity
    3: _vector(8, 8, 5, 8, 7, 6),    # Jupiter: expansion, standing
    4: _vector(5, 8, 5, 6, 4, 8),    # Uranus: unconventional, abrupt
    5: _vector(6, 8, 4, 10, 4, 8),   # Mercury: speech, quickness
    6: _vector(5, 9, 8, 7, 6, 3),    # Venus: harmony, art
    7: _vector(4, 8, 9, 5, 5, 6),    # Neptune: intuition, restlessness
    8: _vector(8, 4, 6, 4, 10, 4),   # Saturn: discipline, endurance
    9: _vector(9, 6, 5, 6, 6, 10),   # Mars: courage, force
}


def score_life_path(value: int) -> Scored:
    if value not in LIFE_PATH_SCORES:
        raise ValueError("unknown life path value: {}".format(value))
    return Scored(
        scores=dict(LIFE_PATH_SCORES[value]),
        basis="from the published meaning of Life Path {}".format(value),
        notes=[],
    )


def score_name_number(value: int) -> Scored:
    if value not in NAME_NUMBER_SCORES:
        raise ValueError("unknown name number: {}".format(value))
    planet = NAME_NUMBER_PLANETS[value]
    return Scored(
        scores=dict(NAME_NUMBER_SCORES[value]),
        basis="Cheiro attaches {} to the number {}, and these follow its "
        "significations".format(planet, value),
        notes=[],
    )


# --------------------------------------------------------------------------
# Vedic vara: from the ruling planet.
# --------------------------------------------------------------------------

PLANET_SCORES: Dict[str, Dict[str, int]] = {
    "Sun": _vector(10, 6, 4, 6, 7, 6),      # authority, vitality
    "Moon": _vector(3, 7, 10, 6, 4, 2),     # feeling, nurture, intuition
    "Mars": _vector(8, 4, 3, 5, 6, 10),     # courage, force, appetite for risk
    "Mercury": _vector(5, 8, 4, 10, 6, 6),  # speech, intellect, dexterity
    "Jupiter": _vector(8, 7, 7, 8, 7, 5),   # wisdom, teaching, expansion
    "Venus": _vector(4, 10, 8, 7, 5, 4),    # art, harmony, pleasure
    "Saturn": _vector(6, 3, 6, 3, 10, 2),   # discipline, endurance, restraint
}


def score_vara(planet: str) -> Scored:
    if planet not in PLANET_SCORES:
        raise ValueError("unknown planet: {}".format(planet))
    return Scored(
        scores=dict(PLANET_SCORES[planet]),
        basis="from the traditional significations of {}, lord of the "
        "vara".format(planet),
        notes=[],
    )
