"""Known-answer tests for the Chaldean name number.

The headline cases are Cheiro's own worked examples, quoted from his 1926
text, so these assert against the source rather than against our arithmetic.
"""

import pytest

from app.engine.name_number import (
    CHALDEAN_VALUES,
    name_number,
    normalise,
    reduce_to_digit,
)


def test_no_letter_is_ever_nine():
    """Cheiro's defining rule for the Chaldean table."""
    assert 9 not in CHALDEAN_VALUES.values()
    assert set(CHALDEAN_VALUES.values()) == {1, 2, 3, 4, 5, 6, 7, 8}


def test_table_covers_the_whole_alphabet_exactly_once():
    assert len(CHALDEAN_VALUES) == 26
    assert sorted(CHALDEAN_VALUES) == [chr(code) for code in range(ord("A"), ord("Z") + 1)]


@pytest.mark.parametrize(
    "word,total,reduced",
    [
        # Cheiro states these totals himself: "18 = 9", "25 = 7", "22 = 4".
        ("Lloyd", 18, 9),
        ("George", 25, 7),
        ("Baldwin", 22, 4),
        # Cheiro also says David produces "another 7".
        ("David", 16, 7),
    ],
)
def test_cheiro_own_worked_examples(word, total, reduced):
    result = name_number(word)
    assert result.letter_total == total
    assert result.value == reduced


def test_lloyd_george_compound_follows_cheiro_not_a_raw_sum():
    """Cheiro adds the reduced digit of each name, giving 9 + 7 = 16.

    He calls 16 "a Shattered Citadel" and treats it as meaningful, so the
    compound must be 16 and not the raw letter total of 43. Both reduce to 7,
    which is why only the compound distinguishes the two methods.
    """
    result = name_number("Lloyd George")

    assert result.compound == 16
    assert result.letter_total == 43
    assert result.value == 7


def test_david_lloyd_george_compound_is_twenty_three():
    """Cheiro: "the total of the three names the number 23"."""
    result = name_number("David Lloyd George")

    assert result.compound == 23
    assert result.value == 5


@pytest.mark.parametrize(
    "value,expected",
    [(1, 1), (9, 9), (10, 1), (18, 9), (22, 4), (43, 7), (59, 5)],
)
def test_reduce_to_digit_never_stops_early(value, expected):
    """Unlike the Life Path reduction, 11 and 22 are not preserved here."""
    assert reduce_to_digit(value) == expected


def test_master_numbers_are_not_preserved_for_names():
    assert reduce_to_digit(11) == 2
    assert reduce_to_digit(22) == 4
    assert reduce_to_digit(33) == 6


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("José", "JOSE"),
        ("Ayush Mishra", "AYUSHMISHRA"),
        ("O'Brien", "OBRIEN"),
        ("Jean-Luc", "JEANLUC"),
        ("Ay9ush", "AYUSH"),
        ("  padded  ", "PADDED"),
    ],
)
def test_normalise_folds_to_scorable_letters(raw, expected):
    assert normalise(raw) == expected


def test_accents_do_not_change_the_number():
    """Stripping marks rather than rejecting them keeps the result stable."""
    assert name_number("Jose").value == name_number("José").value


def test_punctuation_is_reported_rather_than_silently_dropped():
    result = name_number("O'Brien-Smith")
    assert result.ignored_characters == ["'", "-"]


def test_hyphenated_name_is_one_word_for_scoring():
    """A hyphen joins, so Jean-Luc is one name part, not two."""
    assert len(name_number("Jean-Luc").parts) == 1
    assert len(name_number("Jean Luc").parts) == 2


def test_single_letter_name_is_valid():
    result = name_number("A")
    assert result.value == 1


def test_name_with_no_letters_is_rejected():
    for candidate in ("", "   ", "123", "!!!"):
        with pytest.raises(ValueError):
            name_number(candidate)


def test_value_is_always_a_single_digit():
    for candidate in ("A", "Zz", "Ayush Mishra", "Xavier Q Zzyzx", "W" * 200):
        assert 1 <= name_number(candidate).value <= 9
