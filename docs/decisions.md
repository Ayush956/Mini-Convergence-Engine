# Design decisions

A running log of choices made while building the Mini Convergence Engine, and why.
Feeds directly into README sections 2 (assumptions), 3 (edge cases) and 4 (trait-mapping rationale).

## Stack

| Layer | Choice | Reason |
| --- | --- | --- |
| Frontend | Angular 21 + Angular Material | Angular CLI 21.2.9 already installed; Material gives usable date/time pickers without hand-rolling them |
| Backend | FastAPI (Python 3.9.6) | Automatic `/docs` lets the calculation engine be verified before any UI exists |
| Repo layout | Monorepo: `frontend/` + `backend/` | Submission checklist asks for a single repository URL |
| Frontend host | Vercel (static build) | No cold start for static assets |
| Backend host | Render + keep-alive cron ping | Free tier spins down after ~15 min idle; a reviewer opening a cold URL would otherwise wait 30-60s, and "if the URL does not open, the submission cannot be evaluated" |

### Python 3.9 constraint

Staying on the macOS system Python 3.9.6, inside a `venv` under `backend/` so the
system installation is untouched.

Consequence for code style: PEP 585 builtin generics (`list[str]`, `dict[str, int]`)
are fine on 3.9, but **PEP 604 unions (`str | None`) fail at runtime inside Pydantic
models**. Use `Optional[str]` / `Union[...]` throughout.

## Calculation strategy

Overall principle: **libraries for plumbing, own code for domain logic.**

The brief says "verify any library or formula you use against authoritative sources"
and "do not assume a library is correct because it is popular". For four of the five
methods, verifying a third-party library costs the same effort as writing the logic
outright — and writing it means every line can be explained and modified during the
live review, which is 30% of the grade.

| Method | Approach | Status |
| --- | --- | --- |
| Western Sun Sign | Solar ecliptic longitude via the low-precision algorithm from Meeus, *Astronomical Algorithms*; sign = floor(longitude / 30) | Research pending |
| Chinese Zodiac | Own code over a hardcoded Chinese New Year date table from an authoritative source | Research pending |
| Numerology Life Path | Own code, Pythagorean | Research pending |
| Name Number | Own code, Chaldean letter table | Research pending |
| Vedic Vara | Own code: weekday with a sunrise day-boundary rule, plus planetary ruler table | Research pending |

Libraries used deliberately: FastAPI, Pydantic, pytest, Angular, Angular Material.

### Why not an ephemeris library for the Sun

`pyswisseph` / `skyfield` / `astropy` would be more accurate, but `skyfield` wants to
download an ephemeris file of tens of megabytes, which is significant weight against
Render's 512 MB free-tier limit. The Meeus low-precision formula is accurate to well
under 0.01 degrees, far more than needed to place a cusp birth in the correct sign.

### Why a Chinese New Year table rather than a lunar-calendar library

The Chinese year begins at Chinese New Year (falling between 21 Jan and 20 Feb), not
1 January, so `year % 12` is wrong for anyone born in Jan or early Feb. The date is
astronomically defined and cannot be derived with simple arithmetic. A hardcoded table
is spot-checkable against a published source row by row, whereas a library would still
need verifying — the same work, with an added dependency.

## Open questions to resolve during research

- Life Path: reduction order (reduce month/day/year separately, or sum all digits then
  reduce?) and whether master numbers 11/22/33 stay unreduced. Pick one, document it.
- Chaldean: confirm the letter-to-value table. Chaldean uses values 1-8 only, never 9.
  Several sources disagree on a few letters; need to pick an authority and cite it.
- Vara: the Vedic day starts at sunrise, not midnight, so a birth at 02:00 Tuesday
  belongs to Monday's vara. True sunrise needs a location, which the brief never asks
  for. Assume a fixed local sunrise (06:00 is the common convention) and document it.
- Timezone: the brief collects a time of birth with no location. Assume IST.
- Sun sign cusps: with a timezone assumption, cusp placement is only as good as that
  assumption. Document the residual error.

## Notable observation

Time of birth affects **only** the Vedic Vara calculation (via the sunrise boundary)
and, marginally, a cusp sun sign. It is irrelevant to Life Path, Name Number and the
Chinese Zodiac. Worth stating explicitly in the README.

## Secrets

The OpenRouter API key lives only in `backend/.env`, which is gitignored. `.gitignore`
was committed first, before any other file, so no key could ever be tracked. The
assignment brief (which contains the key in plain text) is kept outside the repo, and
`*.pdf` / `*.pages` are ignored as a safety net.
