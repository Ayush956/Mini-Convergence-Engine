"""Name Number, Chaldean system.

Letter values are taken from Cheiro (Count Louis Hamon), "Cheiro's Book of
Numbers" (1926), read from the primary text rather than a secondary chart.
Cheiro sets them out inline and explains the absent 9: no single letter is
ever given the value 9, which he describes as reserved.

Cheiro reduces each name in a full name to a single digit and adds those
digits to form the compound number, rather than summing every letter at
once. We follow him, and expose the compound alongside the single digit.
Both routes land on the same final digit, because repeated digit summing is
arithmetic modulo 9, but the compound numbers differ and Cheiro reads the
compound as meaningful in its own right.

See docs/decisions.md for the two places we knowingly depart from Cheiro.
"""

import unicodedata
from typing import Dict, List, NamedTuple

# Cheiro, Book of Numbers (1926). Verified letter for letter against the
# primary text. No letter maps to 9.
CHALDEAN_VALUES: Dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3,
    "H": 5, "I": 1, "J": 1, "K": 2, "L": 3, "M": 4, "N": 5,
    "O": 7, "P": 8, "Q": 1, "R": 2, "S": 3, "T": 4, "U": 6,
    "V": 6, "W": 6, "X": 5, "Y": 1, "Z": 7,
}


class NamePart(NamedTuple):
    """One word of the name, with its letter total and reduced digit."""

    text: str
    total: int
    reduced: int


class NameNumber(NamedTuple):
    """A name number result with the working that produced it."""

    value: int
    compound: int
    letter_total: int
    parts: List[NamePart]
    ignored_characters: List[str]


def reduce_to_digit(value: int) -> int:
    """Sum digits repeatedly until a single digit.

    Chaldean practice has no master-number concept, so unlike the Life Path
    reduction this never stops early. 9 is a legitimate result even though no
    letter carries the value 9; Cheiro says as much explicitly.
    """
    if value < 0:
        raise ValueError("cannot reduce a negative number")
    while value > 9:
        value = sum(int(digit) for digit in str(value))
    return value


def normalise(text: str) -> str:
    """Fold a name down to the A-Z letters the Chaldean table can score.

    Accents are stripped rather than rejected, so "José" scores as "JOSE"
    instead of erroring. Everything else that is not a letter - digits,
    hyphens, apostrophes, punctuation - is dropped, because the table has no
    value for it and inventing one would be worse than ignoring it.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(c for c in decomposed if not unicodedata.combining(c))
    return "".join(c for c in without_marks.upper() if c in CHALDEAN_VALUES)


def name_number(full_name: str) -> NameNumber:
    """Chaldean name number for a full name.

    Raises ValueError when the name contains no scorable letter at all, which
    the caller should surface as a validation message rather than a crash.
    """
    ignored = sorted(
        {
            character
            for character in full_name
            if not character.isspace() and not normalise(character)
        }
    )

    parts: List[NamePart] = []
    for word in full_name.split():
        letters = normalise(word)
        if not letters:
            continue
        total = sum(CHALDEAN_VALUES[letter] for letter in letters)
        parts.append(NamePart(text=letters, total=total, reduced=reduce_to_digit(total)))

    if not parts:
        raise ValueError("name contains no letters that the Chaldean table can score")

    # Cheiro's method: add the reduced digit of each name, not every letter.
    compound = sum(part.reduced for part in parts)
    letter_total = sum(part.total for part in parts)

    return NameNumber(
        value=reduce_to_digit(compound),
        compound=compound,
        letter_total=letter_total,
        parts=parts,
        ignored_characters=ignored,
    )
