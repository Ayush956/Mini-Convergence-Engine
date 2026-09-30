"""Convergence scoring, exactly as the brief specifies it.

"For each trait dimension, count how many methods agree that the trait is
strong. A method 'agrees' when its score for that dimension is 7 or higher.
Call this count N (from 0 to 5). Then calculate the confidence for that
dimension using this formula: confidence = 1 - 1 / 2^N"

Implemented as written, including the parts we think are wrong. The brief
asks for a critique of the formula in the README, not a replacement for it,
so the criticism belongs in prose and the code stays faithful.

For the record, the ladder this produces is 0%, 50%, 75%, 87.5%, 93.75% and
96.875%. It can express certainty of nothing but never certainty of anything,
the first agreeing method is worth 50 points while the fifth is worth 3, and
1/2^N is the probability of N independent fair coins agreeing when three of
these five methods are functions of the same birth instant. See
docs/decisions.md for the full critique.
"""

from typing import Dict, List, NamedTuple, Sequence

# The brief's threshold: "a method 'agrees' when its score ... is 7 or higher".
AGREEMENT_THRESHOLD = 7

MIN_METHODS = 0
MAX_METHODS = 5


class TraitConvergence(NamedTuple):
    """Convergence for one trait dimension across all five methods."""

    trait: str
    scores: Dict[str, int]
    agreeing: List[str]
    n: int
    confidence: float


def confidence_for(n: int) -> float:
    """confidence = 1 - 1 / 2^N, per the brief.

    N=0 gives exactly 0.0 and N=5 gives 0.96875, so the result is never 1.0.
    """
    if n < MIN_METHODS or n > MAX_METHODS:
        raise ValueError(
            "N must be between {} and {}, got {}".format(MIN_METHODS, MAX_METHODS, n)
        )
    return 1.0 - 1.0 / (2 ** n)


def converge_trait(trait: str, scores_by_method: Dict[str, int]) -> TraitConvergence:
    """Count agreement on one trait and turn it into a confidence."""
    # Sorted so the output order is stable rather than dict-insertion luck.
    agreeing = sorted(
        method
        for method, score in scores_by_method.items()
        if score >= AGREEMENT_THRESHOLD
    )
    n = len(agreeing)
    return TraitConvergence(
        trait=trait,
        scores=dict(scores_by_method),
        agreeing=agreeing,
        n=n,
        confidence=confidence_for(n),
    )


def converge(
    traits: Sequence[str], scores_by_method: Dict[str, Dict[str, int]]
) -> List[TraitConvergence]:
    """Convergence for every trait, given each method's full score vector.

    `scores_by_method` maps a method id to its trait scores. Every method
    must score every trait; a missing score would silently lower N and
    overstate disagreement, so it raises instead.
    """
    if not scores_by_method:
        raise ValueError("no methods supplied")

    for method, scores in scores_by_method.items():
        missing = set(traits) - set(scores)
        if missing:
            raise ValueError(
                "method {} is missing scores for: {}".format(
                    method, ", ".join(sorted(missing))
                )
            )

    return [
        converge_trait(
            trait, {method: scores[trait] for method, scores in scores_by_method.items()}
        )
        for trait in traits
    ]
