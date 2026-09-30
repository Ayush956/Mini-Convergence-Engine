"""FastAPI entry point for the Mini Convergence Engine."""

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Mini Convergence Engine",
    description=(
        "Runs five independent divination systems over one birth record and "
        "measures where they agree."
    ),
    version="0.1.0",
)


def _allowed_origins() -> List[str]:
    """Origins permitted to call this API.

    The deployed frontend origin is injected via FRONTEND_ORIGIN so the
    deployment URL never has to be committed. Local Angular dev servers are
    always allowed because they are harmless and save a config step.
    """
    local = ["http://localhost:4200", "http://127.0.0.1:4200"]
    configured = os.getenv("FRONTEND_ORIGIN", "").strip()
    return local + [configured] if configured else local


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict:
    """Liveness probe, also the target for the keep-alive ping.

    Render's free tier spins a service down after roughly 15 minutes idle and
    a cold start costs 30-60 seconds, so an external scheduler pings this.
    """
    return {"status": "ok"}
