"""Tests for the trait mapping.

These are mostly structural rather than known-answer, because there is no
external authority that says Leo's Leadership is exactly 9. What can be
tested, and what matters, is that the rubric is internally consistent, that
every possible result is covered, that scores stay in range, and that the
composed sun-sign scores really are composed rather than hardcoded.
"""

import pytest

from app.engine.chinese_zodiac import chinese_zodiac
from app.engine.life_path import MASTER_NUMBERS
from app.engine.sun_sign import SIGNS
from app.engine.traits import (
    ANIMAL_SCORES,
    ELEMENT_CONTRIBUTIONS,
    LIFE_PATH_SCORES,
    MAX_SCORE,
    MIN_SCORE,
    MODALITY_CONTRIBUTIONS,
    NAME_NUMBER_PLANETS,
    NAME_NUMBER_SCORES,
    NEUTRAL,
    PLANET_SCORES,
    SIGN_ELEMENTS,
    SIGN_MODALITIES,
    SIGN_OVERRIDES,
    TRAITS,
    clamp,
    score_chinese_zodiac,
    score_life_path,
    score_name_number,
    score_sun_sign,
    score_vara,
)
from app.engine.vara import _VARAS

ALL_SCORE_TABLES = (
    ("animal", ANIMAL_SCORES),
    ("life path", LIFE_PATH_SCORES),
    ("name number", NAME_NUMBER_SCORES),
    ("planet", PLANET_SCORES),
)


def test_the_six_traits_are_the_brief_s_six():
    assert TRAITS == (
        "Leadership",
        "Creativity",
        "Emotional depth",
        "Communication",
        "Discipline",
        "Risk appetite",
    )


@pytest.mark.parametrize("label,table", ALL_SCORE_TABLES)
def test_every_row_scores_every_trait_in_range(label, table):
    for key, scores in table.items():
        assert set(scores) == set(TRAITS), (label, key)
        for trait, value in scores.items():
            assert MIN_SCORE <= value <= MAX_SCORE, (label, key, trait, value)


def test_clamp_holds_the_range():
    assert clamp(-4) == MIN_SCORE
    assert clamp(14) == MAX_SCORE
    assert clamp(7) == 7


# --------------------------------------------------------------------------
# Coverage: every possible result of every method must be scorable.
# --------------------------------------------------------------------------


def test_every_sun_sign_is_covered():
    for sign in SIGNS:
        assert set(score_sun_sign(sign).scores) == set(TRAITS)
    assert set(SIGN_ELEMENTS) == set(SIGNS)
    assert set(SIGN_MODALITIES) == set(SIGNS)


def test_every_animal_is_covered():
    """Checked against the zodiac module rather than a copied list."""
    animals = {chinese_zodiac.__globals__["NEW_YEARS"][year][3] for year in range(1901, 2101)}
    assert animals == set(ANIMAL_SCORES)
    assert len(animals) == 12


def test_every_life_path_value_is_covered():
    expected = set(range(1, 10)) | MASTER_NUMBERS
    assert set(LIFE_PATH_SCORES) == expected


def test_every_name_number_is_covered():
    assert set(NAME_NUMBER_SCORES) == set(range(1, 10))
    assert set(NAME_NUMBER_PLANETS) == set(range(1, 10))


def test_every_vara_planet_is_covered():
    planets = {planet for _, _, planet in _VARAS}
    assert planets == set(PLANET_SCORES)


def test_unknown_inputs_are_rejected_rather_than_defaulted():
    """A silent default would fabricate a reading, which is worse than an error."""
    with pytest.raises(ValueError):
        score_sun_sign("Ophiuchus")
    with pytest.raises(ValueError):
        score_chinese_zodiac("Cat")
    with pytest.raises(ValueError):
        score_life_path(44)
    with pytest.raises(ValueError):
        score_name_number(0)
    with pytest.raises(ValueError):
        score_vara("Pluto")


# --------------------------------------------------------------------------
# The sun-sign rubric: is it actually compositional?
# --------------------------------------------------------------------------


def test_sign_elements_and_modalities_are_the_traditional_four_by_three():
    assert sorted(set(SIGN_ELEMENTS.values())) == ["Air", "Earth", "Fire", "Water"]
    assert sorted(set(SIGN_MODALITIES.values())) == ["Cardinal", "Fixed", "Mutable"]

    # Four signs per modality, three per element.
    for element in set(SIGN_ELEMENTS.values()):
        assert sum(1 for e in SIGN_ELEMENTS.values() if e == element) == 3
    for modality in set(SIGN_MODALITIES.values()):
        assert sum(1 for m in SIGN_MODALITIES.values() if m == modality) == 4


def test_every_element_modality_pair_occurs_exactly_once():
    """Twelve signs, twelve pairs. A duplicate would mean two signs score
    identically, which would be a mistake in the traditional attributions."""
    pairs = [(SIGN_ELEMENTS[sign], SIGN_MODALITIES[sign]) for sign in SIGNS]
    assert len(set(pairs)) == 12


def test_sun_sign_scores_are_composed_not_hardcoded():
    """Recompute from the contribution tables and require agreement.

    This is the test that would fail if someone quietly replaced the rubric
    with hand-written numbers, which is the whole design claim.
    """
    for sign in SIGNS:
        element = SIGN_ELEMENTS[sign]
        modality = SIGN_MODALITIES[sign]
        result = score_sun_sign(sign)

        for trait in TRAITS:
            if (sign, trait) in SIGN_OVERRIDES:
                continue
            expected = clamp(
                NEUTRAL
                + ELEMENT_CONTRIBUTIONS[element][trait]
                + MODALITY_CONTRIBUTIONS[modality][trait]
            )
            assert result.scores[trait] == expected, (sign, trait)


def _raw_composed(sign: str, trait: str) -> int:
    """The composed value before clamping, so clamping can be reasoned about."""
    return (
        NEUTRAL
        + ELEMENT_CONTRIBUTIONS[SIGN_ELEMENTS[sign]][trait]
        + MODALITY_CONTRIBUTIONS[SIGN_MODALITIES[sign]][trait]
    )


def test_signs_sharing_an_element_differ_only_by_modality():
    """Any two same-element signs must differ only by their modality term.

    Stated on the unclamped composition, because clamping legitimately
    flattens differences at the 0 and 10 boundaries: Aries Leadership
    composes to 11 and is capped at 10, so the raw value is what carries the
    invariant.
    """
    for element in sorted(set(SIGN_ELEMENTS.values())):
        group = [s for s in SIGNS if SIGN_ELEMENTS[s] == element]
        assert len(group) == 3, element

        for trait in TRAITS:
            recovered = {
                _raw_composed(sign, trait)
                - MODALITY_CONTRIBUTIONS[SIGN_MODALITIES[sign]][trait]
                for sign in group
            }
            assert recovered == {NEUTRAL + ELEMENT_CONTRIBUTIONS[element][trait]}, (
                element,
                trait,
            )


def test_clamping_is_rare_and_only_at_the_extremes():
    """Clamping costs information, so it is worth knowing how often it bites.

    Where it does, the composed value must have genuinely run past the range
    rather than the clamp masking a rubric mistake in the middle.
    """
    clamped = []
    for sign in SIGNS:
        for trait in TRAITS:
            if (sign, trait) in SIGN_OVERRIDES:
                continue
            raw = _raw_composed(sign, trait)
            if raw != clamp(raw):
                assert raw < MIN_SCORE or raw > MAX_SCORE, (sign, trait, raw)
                clamped.append((sign, trait, raw))

    # 12 signs x 6 traits = 72 composed scores. A handful hitting the ceiling
    # is expected; most of them doing so would mean the contributions are
    # scaled too aggressively.
    assert len(clamped) <= 10, clamped


def test_element_significations_point_the_expected_way():
    """Sanity-check the rubric against what the elements are supposed to mean."""
    assert ELEMENT_CONTRIBUTIONS["Water"]["Emotional depth"] > 0
    assert ELEMENT_CONTRIBUTIONS["Earth"]["Discipline"] > 0
    assert ELEMENT_CONTRIBUTIONS["Air"]["Communication"] > 0
    assert ELEMENT_CONTRIBUTIONS["Fire"]["Risk appetite"] > 0

    assert MODALITY_CONTRIBUTIONS["Cardinal"]["Leadership"] > 0
    assert MODALITY_CONTRIBUTIONS["Fixed"]["Discipline"] > 0
    assert MODALITY_CONTRIBUTIONS["Mutable"]["Communication"] > 0


# --------------------------------------------------------------------------
# Overrides: few, explained, and actually changing something.
# --------------------------------------------------------------------------


def test_overrides_are_documented_and_in_range():
    for (sign, trait), (value, reason) in SIGN_OVERRIDES.items():
        assert sign in SIGN_ELEMENTS, sign
        assert trait in TRAITS, trait
        assert MIN_SCORE <= value <= MAX_SCORE
        # The reason feeds README section 4, so it has to be a real sentence.
        assert len(reason) > 60, (sign, trait)


def test_overrides_stay_a_small_minority():
    """312 scores in total; overriding many of them would mean the rubric
    does not work and should be replaced rather than patched."""
    assert len(SIGN_OVERRIDES) <= 6


def test_each_override_actually_changes_the_composed_value():
    """An override equal to the composed score is dead weight and misleading,
    because it implies a disagreement with the rubric that does not exist."""
    for (sign, trait), (value, _) in SIGN_OVERRIDES.items():
        composed = clamp(
            NEUTRAL
            + ELEMENT_CONTRIBUTIONS[SIGN_ELEMENTS[sign]][trait]
            + MODALITY_CONTRIBUTIONS[SIGN_MODALITIES[sign]][trait]
        )
        assert clamp(value) != composed, (sign, trait)


def test_overrides_are_reported_in_the_notes():
    leo = score_sun_sign("Leo")
    assert leo.scores["Creativity"] == 9
    assert any("Creativity" in note and "overridden" in note for note in leo.notes)

    # A sign with no override carries no notes, so the UI can stay quiet.
    assert score_sun_sign("Aries").notes == []


def test_basis_string_is_present_for_every_method():
    """The UI shows this, and the live review will be asked about it."""
    assert "Fire" in score_sun_sign("Leo").basis
    assert "Fixed" in score_sun_sign("Leo").basis
    assert "Dragon" in score_chinese_zodiac("Dragon").basis
    assert "Life Path" in score_life_path(7).basis
    assert "Cheiro" in score_name_number(5).basis
    assert "Mars" in score_vara("Mars").basis


# --------------------------------------------------------------------------
# Distribution: the scores must be able to produce interesting convergence.
# --------------------------------------------------------------------------


def test_no_trait_is_universally_strong_or_universally_weak():
    """If every row scored a trait 7+, N would always be 5 for it and the
    convergence measure would carry no information."""
    for trait in TRAITS:
        values = []
        for sign in SIGNS:
            values.append(score_sun_sign(sign).scores[trait])
        for table in (ANIMAL_SCORES, LIFE_PATH_SCORES, NAME_NUMBER_SCORES, PLANET_SCORES):
            values.extend(scores[trait] for scores in table.values())

        assert any(value >= 7 for value in values), trait
        assert any(value < 7 for value in values), trait


def test_every_result_has_at_least_one_strong_and_one_weak_trait():
    """A row that is 7+ on everything, or on nothing, is a suspicious row -
    it would mean the mapping is not discriminating between dimensions."""
    rows = [(sign, score_sun_sign(sign).scores) for sign in SIGNS]
    rows += [(a, s) for a, s in ANIMAL_SCORES.items()]
    rows += [("life path {}".format(k), s) for k, s in LIFE_PATH_SCORES.items()]
    rows += [("name {}".format(k), s) for k, s in NAME_NUMBER_SCORES.items()]
    rows += [(p, s) for p, s in PLANET_SCORES.items()]

    for label, scores in rows:
        strong = sum(1 for value in scores.values() if value >= 7)
        assert 1 <= strong <= 5, (label, scores)
