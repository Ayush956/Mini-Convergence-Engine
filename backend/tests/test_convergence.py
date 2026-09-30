"""Tests for the convergence score.

The brief specifies this completely, including a worked example, so these are
genuine known-answer tests rather than structural ones.
"""

import pytest

from app.engine.convergence import (
    AGREEMENT_THRESHOLD,
    confidence_for,
    converge,
    converge_trait,
)
from app.engine.traits import TRAITS


def test_threshold_is_the_brief_s_seven():
    assert AGREEMENT_THRESHOLD == 7


@pytest.mark.parametrize(
    "n,expected",
    [
        (0, 0.0),
        (1, 0.5),
        (2, 0.75),
        (3, 0.875),
        (4, 0.9375),
        (5, 0.96875),
    ],
)
def test_the_full_confidence_ladder(n, expected):
    assert confidence_for(n) == pytest.approx(expected)


def test_the_brief_s_worked_example():
    """"if 3 methods score Leadership at 7 or above, N = 3 and
    confidence = 1 - 1/8 = 87.5%"."""
    assert confidence_for(3) == pytest.approx(0.875)


def test_zero_agreement_is_exactly_zero_not_near_zero():
    """1 - 1/2^0 = 1 - 1 = 0. Worth pinning, because an earlier reading of
    the formula assumed it could never reach 0."""
    assert confidence_for(0) == 0.0


def test_unanimity_never_reaches_certainty():
    """Even all five agreeing tops out below 100%, which is one of the
    formula's odder asymmetries."""
    assert confidence_for(5) < 1.0
    assert confidence_for(5) == pytest.approx(0.96875)


def test_confidence_is_strictly_increasing():
    values = [confidence_for(n) for n in range(6)]
    assert values == sorted(values)
    assert len(set(values)) == 6


def test_first_agreeing_method_is_worth_far_more_than_the_last():
    """The criticism in the README, asserted so it cannot be misquoted:
    the step from 0 to 1 is 50 points, from 4 to 5 about 3."""
    first_step = confidence_for(1) - confidence_for(0)
    last_step = confidence_for(5) - confidence_for(4)

    assert first_step == pytest.approx(0.5)
    assert last_step == pytest.approx(0.03125)
    assert first_step > last_step * 15


def test_n_outside_zero_to_five_is_rejected():
    with pytest.raises(ValueError):
        confidence_for(-1)
    with pytest.raises(ValueError):
        confidence_for(6)


# --------------------------------------------------------------------------
# Counting agreement.
# --------------------------------------------------------------------------


def test_seven_agrees_and_six_does_not():
    """The threshold is inclusive, so 7 counts and 6.9 would not.

    This is the cliff the README criticises: a hair's difference flips a
    method from disagreeing to agreeing and moves confidence a long way.
    """
    result = converge_trait("Leadership", {"a": 7, "b": 6, "c": 6, "d": 6, "e": 6})

    assert result.agreeing == ["a"]
    assert result.n == 1
    assert result.confidence == pytest.approx(0.5)


def test_all_five_agreeing():
    result = converge_trait("Leadership", {"a": 7, "b": 8, "c": 9, "d": 10, "e": 7})
    assert result.n == 5
    assert result.confidence == pytest.approx(0.96875)


def test_none_agreeing():
    result = converge_trait("Leadership", {"a": 0, "b": 3, "c": 6, "d": 1, "e": 6})
    assert result.agreeing == []
    assert result.n == 0
    assert result.confidence == 0.0


def test_agreeing_methods_are_named_not_just_counted():
    """The UI needs to show which methods agree, so the reader can see why
    N is what it is rather than trusting a number."""
    result = converge_trait(
        "Leadership", {"sun_sign": 9, "vara": 8, "life_path": 3, "name_number": 6, "chinese_zodiac": 5}
    )
    assert result.agreeing == ["sun_sign", "vara"]
    assert result.n == 2


def test_shape_of_disagreement_is_discarded_by_design():
    """Another documented weakness: 7,7,7,2,2 and 7,8,9,6,6 both give N=3
    and therefore identical confidence, though they are different pictures.

    Asserted so the README claim is backed by the implementation.
    """
    bimodal = converge_trait("Leadership", {"a": 7, "b": 7, "c": 7, "d": 2, "e": 2})
    coherent = converge_trait("Leadership", {"a": 7, "b": 8, "c": 9, "d": 6, "e": 6})

    assert bimodal.n == coherent.n == 3
    assert bimodal.confidence == coherent.confidence


# --------------------------------------------------------------------------
# Converging all six traits at once.
# --------------------------------------------------------------------------


def _full_scores(value: int):
    return {trait: value for trait in TRAITS}


def test_converge_returns_one_row_per_trait_in_order():
    scores = {
        "sun_sign": _full_scores(8),
        "chinese_zodiac": _full_scores(3),
        "life_path": _full_scores(7),
        "name_number": _full_scores(6),
        "vara": _full_scores(9),
    }
    results = converge(TRAITS, scores)

    assert [row.trait for row in results] == list(TRAITS)
    for row in results:
        assert row.n == 3
        assert row.agreeing == ["life_path", "sun_sign", "vara"]
        assert row.confidence == pytest.approx(0.875)


def test_converge_rejects_a_method_missing_a_trait():
    """Silently treating a missing score as disagreement would understate N
    and quietly corrupt the headline number."""
    incomplete = dict(_full_scores(8))
    del incomplete["Discipline"]

    with pytest.raises(ValueError) as error:
        converge(TRAITS, {"sun_sign": incomplete})
    assert "Discipline" in str(error.value)


def test_converge_rejects_no_methods():
    with pytest.raises(ValueError):
        converge(TRAITS, {})


def test_converge_preserves_the_raw_scores_for_display():
    """The brief requires the matrix to show every score, so they must
    survive the convergence step rather than being reduced away."""
    scores = {
        "sun_sign": _full_scores(9),
        "chinese_zodiac": _full_scores(2),
    }
    results = converge(TRAITS, scores)

    for row in results:
        assert row.scores == {"sun_sign": 9, "chinese_zodiac": 2}
