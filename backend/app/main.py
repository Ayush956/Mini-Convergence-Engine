"""FastAPI entry point for the Mini Convergence Engine."""

import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.engine.reading import ReadingError, build_reading
from app.engine.summary import summarise
from app.models import ReadingRequest, ReadingResponse

app = FastAPI(
    title="Mini Convergence Engine",
    description=(
        "Runs five independent divination systems over one birth record and "
        "measures where they agree."
    ),
    version="1.0.0",
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


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    """Turn Pydantic's error shape into one plain sentence.

    The brief asks for clear messages and no crashes. Pydantic's default
    payload is a nested list of dicts that no UI should have to interpret,
    and that no user should ever see.
    """
    first = error.errors()[0] if error.errors() else {}
    message = str(first.get("msg", "That input could not be read."))
    # Pydantic prefixes custom ValueError messages with "Value error, ".
    message = message.replace("Value error, ", "")

    location = [part for part in first.get("loc", ()) if part != "body"]
    return JSONResponse(
        status_code=422,
        content={"message": message, "field": location[0] if location else None},
    )


@app.get("/health")
def health() -> dict:
    """Liveness probe, also the target for the keep-alive ping.

    Render's free tier spins a service down after roughly 15 minutes idle and
    a cold start costs 30-60 seconds, so an external scheduler pings this.
    """
    return {"status": "ok"}


@app.post("/api/reading", response_model=ReadingResponse)
def reading(request: ReadingRequest) -> ReadingResponse:
    """Calculate all five methods, score the traits, and converge them."""
    try:
        methods, traits, assumptions = build_reading(
            request.full_name, request.date_of_birth, request.time_of_birth
        )
    except ReadingError as error:
        raise HTTPException(status_code=422, detail=str(error))

    summary, source = summarise(
        full_name=request.full_name, methods=methods, traits=traits
    )

    return ReadingResponse(
        full_name=request.full_name,
        date_of_birth=request.date_of_birth,
        time_of_birth=request.time_of_birth,
        methods=methods,
        traits=traits,
        summary=summary,
        summary_source=source,
        assumptions=assumptions,
    )
