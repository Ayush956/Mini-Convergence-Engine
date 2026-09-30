"""Grounded Q&A over a completed reading, using the same OpenRouter model as the summary."""

import json
import os
from typing import Dict, List, Optional, Tuple

import httpx

from app.engine.summary import DEFAULT_MODEL, OPENROUTER_URL, REQUEST_TIMEOUT_SECONDS

SOURCE_MODEL = "model"
SOURCE_UNAVAILABLE = "unavailable"

MAX_HISTORY_TURNS = 6
MAX_TOKENS = 480


def _reading_payload(reading: dict) -> str:
    """Compact JSON the model can cite; numbers only, no invented fields."""
    return json.dumps(reading, indent=2, default=str)


def build_system_prompt(reading: Optional[dict]) -> str:
    if reading:
        return (
            "You are a helpful assistant for the Mini Convergence Engine. The user "
            "has already run five divination systems on one birth record. Every "
            "number below was calculated by deterministic code; do not change or "
            "invent any score, result, N value, or confidence percentage.\n\n"
            "Answer in plain language, 2-5 short paragraphs unless they ask for "
            "one sentence. If they ask about something not in the data, say so. "
            "Do not claim to predict the future or state psychological facts as "
            "truth — describe what these systems say and how the convergence "
            "formula interpreted them.\n\n"
            "Reading data (JSON):\n"
            "{data}"
        ).format(data=_reading_payload(reading))

    return (
        "You are a helpful assistant for the Mini Convergence Engine web app.\n\n"
        "The user has NOT run a reading yet. There is no calculated data — no sun "
        "sign, Chinese animal, numerology numbers, vara, trait scores, N values, "
        "or confidence for any person.\n\n"
        "You MAY answer general questions: what the five systems are, the six "
        "traits, how scores and convergence work (agreement at 7 or above, "
        "confidence = 1 - 1/2^N), how to use the form, or what the app does.\n\n"
        "If the user asks anything that needs THEIR specific results — my sun "
        "sign, my animal, my matrix, my scores, why I got this trait, explain "
        "my reading, my name number, my convergence — you MUST NOT guess or "
        "invent any number or sign. Say clearly they have not run the five "
        "systems yet: enter full name, date and time of birth on the left, "
        "click Run the five systems, then ask again and you will answer from "
        "that data.\n\n"
        "If they mix a general question with a data question, answer the general "
        "part briefly, then tell them to run a reading for anything personal."
    )


def _messages(
    reading: Optional[dict], history: List[dict], user_message: str
) -> List[Dict[str, str]]:
    system = build_system_prompt(reading)
    out: List[Dict[str, str]] = [{"role": "system", "content": system}]

    for turn in history[-MAX_HISTORY_TURNS * 2 :]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            out.append({"role": role, "content": content})

    out.append({"role": "user", "content": user_message})
    return out


def unavailable_reply() -> str:
    return (
        "The assistant is not available right now because the OpenRouter API "
        "key is missing or the model call failed. Try again in a moment."
    )


def chat(
    user_message: str, reading: Optional[dict], history: List[dict]
) -> Tuple[str, str]:
    """Return (reply, source) where source is 'model' or 'unavailable'."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return unavailable_reply(), SOURCE_UNAVAILABLE

    model = os.getenv("OPENROUTER_MODEL", "").strip() or DEFAULT_MODEL
    payload = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": _messages(reading, history, user_message),
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
        return unavailable_reply(), SOURCE_UNAVAILABLE

    if not text:
        return unavailable_reply(), SOURCE_UNAVAILABLE

    return text, SOURCE_MODEL
