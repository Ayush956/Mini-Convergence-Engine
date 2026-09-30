"""Shared test setup.

The one thing worth saying here: importing the app loads .env, which sets a
real OpenRouter key. Left alone, the API tests would each make a real,
billed model call - slow, dependent on the network, and charged against a
ten dollar budget that has to last the assignment.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def no_model_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the deterministic summary path for every test.

    Autouse rather than opt-in, because a test that accidentally reaches the
    network is a test that fails on a train. The model call itself is
    exercised by hand against the live key, not from the suite.
    """
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert not os.getenv("OPENROUTER_API_KEY")
