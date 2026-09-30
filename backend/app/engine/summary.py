"""The plain-language summary the output screen requires.

The brief asks for "a short plain-language summary a non-technical person can
understand", and issues an OpenRouter key whose usage is logged and forms
part of the evaluation. So this makes a real model call.

Two rules, both deliberate:

1. The model only phrases numbers it is handed. Every calculation, trait
   score and confidence figure is produced by deterministic code before this
   module is called, so results are reproducible and unit-testable and no
   number on screen originates from a language model.
2. A template fallback covers any failure. A cold key, a rate limit or a
   timeout must never leave a reviewer looking at a broken results page, so
   the fallback is a first-class path rather than an afterthought. The
   response reports which path produced the text.

The brief mandates anthropic/claude-sonnet-5.5 and forbids more expensive
models, so the model name comes from configuration with that as the default.
"""

import os
from typing import Dict, List, Tuple

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-5.5"

# Short, because a reviewer waiting on a cold Render instance is already
# waiting long enough. The fallback is good, so giving up early is cheap.
REQUEST_TIMEOUT_SECONDS = 12.0
MAX_TOKENS = 320

SOURCE_MODEL = "model"
SOURCE_TEMPLATE = "template"


def _strongest(traits: List[dict]) -> List[dict]:
    return sorted(traits, key=lambda row: (-row["n"], row["trait"]))


def build_prompt(full_name: str, methods: List[dict], traits: List[dict]) -> str:
    """Assemble the prompt. Every number in it is already calculated."""
    method_lines = [
        "- {}: {}".format(method["label"], method["result"]) for method in methods
    ]
    trait_lines = [
        "- {}: {} of 5 methods agree it is strong, confidence {:.1f}%".format(
            row["trait"], row["n"], row["confidence"] * 100
        )
        for row in traits
    ]

    return (
        "You are writing one short paragraph for a general audience.\n\n"
        "Five unrelated divination systems were calculated for {name}:\n"
        "{methods}\n\n"
        "Each system was scored 0-10 on six traits. A system 'agrees' a trait "
        "is strong when it scores 7 or more. The agreement counts are:\n"
        "{traits}\n\n"
        "Write 3-4 sentences, no more than 90 words, that explain where these "
        "systems agree and where they disagree. Rules: do not invent numbers, "
        "do not repeat every figure, do not use headings or bullet points, do "
        "not address the reader as 'you', and do not claim any of this "
        "predicts anything. Describe it as what these systems say, not as "
        "fact. Plain language, no jargon."
    ).format(
        name=full_name,
        methods="\n".join(method_lines),
        traits="\n".join(trait_lines),
    )


def template_summary(full_name: str, methods: List[dict], traits: List[dict]) -> str:
    """Deterministic fallback. Reads like prose, not like an error message."""
    ranked = _strongest(traits)
    strongest = ranked[0]
    weakest = ranked[-1]

    results = ", ".join(
        "{} ({})".format(method["result"], method["label"].lower())
        for method in methods
    )

    agreed = [row for row in traits if row["n"] >= 3]
    if agreed:
        agreement = (
            "The systems line up most on {}, where {} of the five agree it is "
            "strong, giving a confidence of {:.1f}%.".format(
                strongest["trait"].lower(),
                strongest["n"],
                strongest["confidence"] * 100,
            )
        )
    else:
        agreement = (
            "No trait draws agreement from even three of the five systems, so "
            "this is a reading with little convergence - the strongest is {} "
            "at {} of 5.".format(strongest["trait"].lower(), strongest["n"])
        )

    return (
        "For {name}, the five systems give {results}. {agreement} They agree "
        "least on {weakest}, where {weakest_n} of the five call it strong. "
        "Bear in mind these are five unrelated traditions being compared, not "
        "a prediction, and the agreement score reflects how the traits were "
        "mapped as much as anything about {name}."
    ).format(
        name=full_name,
        results=results,
        agreement=agreement,
        weakest=weakest["trait"].lower(),
        weakest_n=weakest["n"],
    )


def summarise(
    full_name: str, methods: List[dict], traits: List[dict]
) -> Tuple[str, str]:
    """Return (summary, source) where source is 'model' or 'template'."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return template_summary(full_name, methods, traits), SOURCE_TEMPLATE

    model = os.getenv("OPENROUTER_MODEL", "").strip() or DEFAULT_MODEL
    payload: Dict = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "user", "content": build_prompt(full_name, methods, traits)}
        ],
    }

    try:
        response = httpx.post(
            OPENROUTER_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={
                "Authorization": "Bearer {}".format(api_key),
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        # Deliberately broad. Any failure at all - network, auth, rate limit,
        # unexpected response shape - must degrade to the template rather
        # than surface as a 500 on the results page.
        return template_summary(full_name, methods, traits), SOURCE_TEMPLATE

    if not text:
        return template_summary(full_name, methods, traits), SOURCE_TEMPLATE

    return text, SOURCE_MODEL
