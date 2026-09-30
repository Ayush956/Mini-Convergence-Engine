# Mini Convergence Engine

A web app that takes a full name, date of birth and time of birth, runs **five independent divination systems** over that record, scores each result on **six traits**, and measures where the systems agree.

Built for the Decode Stars final-round assignment.

| Layer | Choice |
| --- | --- |
| Live site | [https://mini-convergence-engine-cyan.vercel.app](https://mini-convergence-engine-cyan.vercel.app/) |
| API | [https://mini-convergence-engine.onrender.com](https://mini-convergence-engine.onrender.com/health) |
| Frontend | React 19, Vite, MUI |
| Backend | FastAPI (Python 3.11 on Render; 3.9-compatible code) |
| Repo | One monorepo: `frontend/` + `backend/` |

The browser only talks to the Vercel origin. `/api/*` is rewritten to Render (see `frontend/vercel.json`). The five calculations, trait scores and `1 − 1/2^N` arithmetic are deterministic Python. The LLM is used only to phrase numbers it is handed (summary + chat).

---

## 1. Live URL and how to run the project locally

**Live URL:** [https://mini-convergence-engine-cyan.vercel.app](https://mini-convergence-engine-cyan.vercel.app/)

Health check for the API: [https://mini-convergence-engine.onrender.com/health](https://mini-convergence-engine.onrender.com/health) — expect `{"status":"ok"}`. The first request after idle can take 30–60 seconds on Render’s free tier.

Interactive API docs: [https://mini-convergence-engine.onrender.com/docs](https://mini-convergence-engine.onrender.com/docs)

### Run locally

You need two terminals. The Vite app proxies `/api` and `/health` to `localhost:8000`.

**Backend**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then paste OPENROUTER_API_KEY
uvicorn app.main:app --reload --port 8000
```

`backend/.env` is gitignored. Without a key the engine still calculates; the summary and chat fall back to a template / “unavailable” message.

**Frontend**

```bash
cd frontend
npm install
npm start
```

Open [http://localhost:4200](http://localhost:4200).

**Tests**

```bash
cd backend
./venv/bin/pytest
```

---

## 2. Assumptions

The brief is silent on several things that change the answer. These are the ones we locked and show on the reading when they apply.

**Timezone is IST.** The form collects a clock time and no place. Every timestamp is treated as India Standard Time (UTC+5.5). A birth near a sun-sign cusp or the 06:00 sunrise line can flip if the real local zone is different. That residual error is larger than the ~15 minutes of clock-time uncertainty in the Meeus solar formula.

**Vedic sunrise is fixed at 06:00 IST.** A true savana day starts at local sunrise, which needs a latitude and longitude the brief never asks for. Births before 06:00 take the previous civil day’s vara. The UI lists this when it happens.

**Chinese year follows Hong Kong Observatory New Year dates, not 1 January.** Anyone born in late January or early February can be the *previous* animal. A `year % 12` shortcut would get those births wrong.

**Life Path is component-first, master numbers kept.** Month, day and year are reduced separately (stopping at 11, 22 or 33), then summed, then reduced again. Authorities split on this versus a flat digit sum (Decoz / numerologist.com vs Millman and others). There is no neutral tiebreaker. We chose the per-component rule because it is easier to explain, not because it “preserves more master numbers” — over 1950–2010 the flat method actually produces master numbers more often. Both methods disagree on 13.4% of those dates; every disagreement is a master number versus its reduction.

Worked example, **4 January 1950** (one of the divergent dates):

- Component-first: month 1, day 4, year 15 → 6; sum 11 → **Life Path 11**
- Flat-sum: 1+9+5+0+0+1+0+4 = 20 → 2

**Name number uses the full name as typed, reduced to one digit.** Cheiro reads the two-digit compound and prefers “the most used Christian and Surname”. The brief gives one name field and no way to know a preferred form, so we use the whole string and reduce. Characters with no Chaldean value (digits, punctuation, spaces) are ignored and named in the assumptions list.

**Time of birth only moves Vara and, near a cusp, the sun sign.** Life Path, name number and the Chinese animal ignore the clock.

**Supported dates start at 1902.** That is the start of the verified Chinese New Year table we ship. Future dates are rejected.

**Python 3.9-compatible typing in the backend** (`Optional[...]` rather than `str | None` on Pydantic models) so the same code runs locally and on Render 3.11.

---

## 3. Edge cases and how each is handled

| Case | What we do |
| --- | --- |
| Empty name / no letters | 422 with a plain sentence, not a stack trace |
| Name longer than 120 characters | Rejected with a readable message |
| Punctuation, digits, accents | Accents are accepted; characters with no Chaldean value are skipped and listed |
| Date in the future | Rejected: “A date of birth cannot be in the future.” |
| Date before 1902 | Rejected with the calendar-table reason |
| Malformed date or time | 422 `{message, field}` — the UI never sees Pydantic’s nested error list |
| Leap day (29 Feb) | Accepted; Life Path uses the real day number |
| Midnight (00:00) | Accepted; always before sunrise, so Vara shifts to the previous day |
| Birth before 06:00 | Vara taken from the previous civil date; assumption text explains why |
| Birth in Jan / early Feb | Animal looked up against the HKO New Year date, not `year % 12` |
| Within ~24 hours of a sun-sign cusp | Result still computed from longitude; assumption warns the neighbour is possible |
| Cusp drift across years | No fixed “Aries starts 21 March” table — longitude is computed (tropical year ≠ calendar year) |
| Life Path 11 / 22 / 33 | Left unreduced; 4 Jan 1950 is a regression test |
| OpenRouter missing, slow, or failing | Summary uses a deterministic template; chat returns an unavailable message. The numbers still render |
| Render cold start | UI copy explains a wait of up to a minute |
| Mobile viewport | Chat stays closed until **Ask with AI**; then it is fullscreen and unmounts on close |
| Chat before a reading | Allowed. General questions are answered; personal-score questions are refused until the user runs the five systems |

---

## 4. Trait-mapping rationale and sources

The brief fixes the six traits (Leadership, Creativity, Emotional depth, Communication, Discipline, Risk appetite), the 0–10 range, agreement at **7 or above**, **N** as the count of agreeing methods, and **confidence = 1 − 1/2^N**. The only design freedom is the 312 scores (52 possible results × 6 traits).

There is no single correct mapping. Scores are **rule-derived**, with a few named overrides, so each number traces to a rubric rather than a mood. Changing one rubric row updates every affected result — which matters in a live review.

### How each method is scored

**Western sun signs — element × modality on a base of 5.**  
Every sign is Fire/Earth/Air/Water crossed with Cardinal/Fixed/Mutable. Leo’s Leadership is 5 + Fire + Fixed, not a typed-in 9.

- Elements: Fire assertive; Earth practical; Air sociable; Water feeling.
- Modalities: Cardinal initiates; Fixed persists; Mutable adapts.

Classical structure of elements and modalities: Ptolemy, *Tetrabiblos*. Sign identity (which sign is which element/modality) is the standard tropical scheme used with the Meeus longitude.

**Overrides** where the additive rubric fights well-attested tradition (`SIGN_OVERRIDES` in `backend/app/engine/traits.py`):

| Sign / trait | Composed | Used | Why |
| --- | --- | --- | --- |
| Leo / Creativity | 6 | 9 | Fire+Fixed has no term for theatrical self-expression, which sources treat as central to Leo |
| Virgo / Discipline | 7 | 9 | Mutable subtracts discipline; for Virgo that describes adaptable *method*, not a lax standard |
| Scorpio / Risk appetite | 2 | 7 | Water+Fixed reads as risk-averse; tradition treats Scorpio’s extremes as deliberate high risk |

**Chinese animals — traditional trait lists.**  
No compositional grid, so twelve rows. Example: Ox diligent/stubborn → Discipline 10, Risk 2; Dragon charismatic leader → Leadership 10. Animal identity comes from the [Hong Kong Observatory Gregorian–Lunar tables](https://www.hko.gov.hk/en/gts/time/conversion.htm).

**Life Path — published number meanings, master numbers intensified.**  
1 pioneer/leader; 2 diplomat; 4 builder; 8 executive; 11 as an intensified 2, and so on. Lineage: Hans Decoz / numerologist.com (component-first reduction and master-number preservation). Karmic-debt readings (13, 14, 16, 19) are out of scope.

**Name number — Cheiro’s planet per digit.**  
Cheiro, *Cheiro’s Book of Numbers* (1926): letter table (no 9 in the alphabet, because 9 is reserved) and a planet for each reduced number (1 Sun … 9 Mars). Scores follow those planetary significations. We do **not** keep his two-digit compound reading (see assumptions).

**Vara — planetary lord of the weekday.**  
[Calendar Reform Committee report (CSIR, 1955, Meghnad Saha)](https://archive.org/stream/calendar_reform_comittee_report/calendar_reform_comittee_report_djvu.txt): the savana day runs sunrise to sunrise; Sunday–Saturday lords are Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn. Mars → high risk; Mercury → high communication.

### Calculation sources (identity of each result, not the scores)

| Method | Formula / table | Checked against |
| --- | --- | --- |
| Sun sign | Meeus, *Astronomical Algorithms*, ch. 25 (low-precision solar longitude); sign = floor(λ / 30) | NASA JPL Horizons quantity 31 (`ObsEcLon`), including cusps and a leap year |
| Chinese zodiac | Hardcoded New Year dates from HKO | Published HKO rows; Jan/Feb births that `year % 12` gets wrong |
| Life Path | Component-first reduction | Hand cases including 4 Jan 1950 |
| Name number | Cheiro 1926 letter table | Cheiro’s own worked names (Lloyd George, Baldwin) |
| Vara | Weekday + 06:00 boundary | Cases either side of 06:00 and midnight |

No astronomy or numerology library is a dependency. The Sun method is ~0.01° (about 15 minutes at a cusp). The IST/place guess dominates that error, which is why we did not pull in `pyswisseph`.

---

## 5. Sample outputs for five test inputs

All five were computed by the same engine the live site uses (`build_reading` in `backend/app/engine/reading.py`). Reproduce them at [the live URL](https://mini-convergence-engine-cyan.vercel.app/) — first load may wait for Render to wake.

Agreement means a trait score ≥ 7. Confidence is `1 − 1/2^N`.

### 1. Ayush Mishra — 15 Aug 1995, 10:30

A mid-range “ordinary” adult birth after sunrise, used as the API fixture.

| Method | Result |
| --- | --- |
| Sun sign | Leo |
| Chinese zodiac | Pig |
| Life Path | 2 |
| Name number | 5 |
| Vara | Mangalavara (Mars) |

| Trait | N | Confidence |
| --- | --- | --- |
| Leadership | 2 | 75% |
| Creativity | 2 | 75% |
| Emotional depth | 2 | 75% |
| Communication | 2 | 75% |
| Discipline | 1 | 50% |
| Risk appetite | 3 | **87.5%** |

### 2. Lloyd George — 4 Jan 1950, 07:15

Cheiro’s worked name plus a date that **must** yield Life Path 11 under our rule. Also before Chinese New Year 1950-02-17.

| Method | Result |
| --- | --- |
| Sun sign | Capricorn |
| Chinese zodiac | Ox (not the 1950 Tiger) |
| Life Path | **11** |
| Name number | 7 |
| Vara | Budhavara (Mercury) |

| Trait | N | Confidence |
| --- | --- | --- |
| Leadership | 2 | 75% |
| Creativity | 3 | **87.5%** |
| Emotional depth | 2 | 75% |
| Communication | 2 | 75% |
| Discipline | 2 | 75% |
| Risk appetite | 0 | **0%** |

### 3. Priya Sharma — 23 Jan 1993, 03:03

Before assumed sunrise, so Vara uses **22 Jan**. Tests the 06:00 boundary.

| Method | Result |
| --- | --- |
| Sun sign | Aquarius |
| Chinese zodiac | Rooster |
| Life Path | 1 |
| Name number | 2 |
| Vara | Shukravara (Venus) — from 22 Jan |

| Trait | N | Confidence |
| --- | --- | --- |
| Leadership | 2 | 75% |
| Creativity | 1 | 50% |
| Emotional depth | 2 | 75% |
| Communication | 4 | **93.75%** |
| Discipline | 3 | 87.5% |
| Risk appetite | 1 | 50% |

### 4. James Baldwin — 20 Mar 1964, 23:45

Another Cheiro-era name, chosen to sit **about four hours from a sign cusp** so the timezone warning fires.

| Method | Result |
| --- | --- |
| Sun sign | Aries (cusp warning) |
| Chinese zodiac | Dragon |
| Life Path | 7 |
| Name number | 9 |
| Vara | Shukravara (Venus) |

| Trait | N | Confidence |
| --- | --- | --- |
| Leadership | 3 | 87.5% |
| Creativity | 4 | **93.75%** |
| Emotional depth | 2 | 75% |
| Communication | 3 | 87.5% |
| Discipline | 1 | 50% |
| Risk appetite | 3 | 87.5% |

### 5. Mei Chen — 4 Feb 2000, 05:59

Double boundary: one minute before assumed sunrise **and** the day before Chinese New Year 2000-02-05 (Rabbit, not Dragon).

| Method | Result |
| --- | --- |
| Sun sign | Aquarius |
| Chinese zodiac | Rabbit |
| Life Path | 8 |
| Name number | 1 |
| Vara | Guruvara (Jupiter) — from 3 Feb |

| Trait | N | Confidence |
| --- | --- | --- |
| Leadership | 3 | 87.5% |
| Creativity | 2 | 75% |
| Emotional depth | 2 | 75% |
| Communication | 3 | 87.5% |
| Discipline | 4 | **93.75%** |
| Risk appetite | 2 | 75% |

---

## 6. Critique of the confidence formula `1 − 1/2^N`

The code implements the brief **as written**. This section is the critique the brief asks for, not a silent replacement.

The ladder:

| N | 0 | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- | --- |
| Confidence | 0% | 50% | 75% | 87.5% | 93.75% | 96.875% |

It can express certainty of **nothing** (`N = 0`) but never certainty of **anything**. That asymmetry is already odd for something labelled “confidence”.

**Weaknesses, strongest first**

1. **We control the input, so the output measures the rubric.** N is a count of *our* scores crossing 7. Moving a few 6s to 7s raises “confidence” with no new fact about the person. Sample 2 shows Risk appetite at 0% and Creativity at 87.5% for the same birth — that gap is a property of how we scored Capricorn, Ox, 11, 7 and Mercury, not a measurement of Lloyd George.

2. **The independence premise is false.** `1/2^N` is the chance that N independent fair coins agree. These methods are not independent: Life Path and name number are both digit reductions; sun sign, Chinese animal and vara are all functions of the same instant. Correlated votes are weaker evidence than the formula assumes, so it **overstates**.

3. **The threshold is a cliff.** 6.9 and 7.0 are opposites. One method drifting by 0.1 can move a trait from 75% to 87.5%.

4. **It throws away the shape of disagreement.** Scores `7,7,7,2,2` and `7,8,9,6,6` both give N = 3 and the same confidence. The second picture is much more coherent.

5. **The first step is huge; the last is tiny.** One lonely method agreeing is “50% confidence”. A fifth corroborating method adds 3.1 points, so unanimity barely beats a bare majority.

**What I would change (and still show the brief’s number beside it)**

- Report the **mean score and spread** (or a proper agreement coefficient) so a tight cluster at 7 is distinct from a bimodal 9-vs-2 split.
- **Down-weight methods that share an input.** Three readings from the same birth instant should not count as three independent votes.
- Soften the cliff: treat 6 vs 7 as a small difference, not a binary.

I would keep `1 − 1/2^N` on screen because the brief requires it and the critique is part of the exercise.

---

## 7. Known limitations and what I would improve with more time

- **No birthplace.** IST + 06:00 sunrise is the largest error. A city field (or lat/long) would fix Vara and tighten cusps.
- **Meeus low-precision Sun** is fine next to that timezone guess; with a location I would consider a real ephemeris.
- **Trait rubric is additive and crude.** Tradition is not a vector sum. More overrides, or a published per-sign table with citations per cell, would be more honest than seven rules plus three exceptions.
- **Chinese table is hardcoded** through the HKO range we verified. Extending it or documenting the 2057/2089 caveats in-product would be tidier.
- **Render free tier sleeps.** A keep-alive ping (cron-job.org or GitHub Actions hitting `/health` every ~12 minutes) should be added so a reviewer does not wait a minute.
- **One `FRONTEND_ORIGIN`.** Preview deployments on other Vercel URLs are not in the CORS list.
- **Chat context is one reading JSON**, not a persistent user profile.
- **README / docs duplication.** `docs/decisions.md` is the working log; this file is the submission surface.

---

## 8. AI usage summary

**In the product (required by the brief)**  
OpenRouter, model `anthropic/claude-sonnet-5.5` only, using the issued key. Two calls:

- Plain-language summary on the results screen
- “Ask with AI” chat, grounded in the reading JSON when present

Usage is billed on that key and is part of the evaluation. Calculations, scores and N are **never** produced by a model. If the key is missing or the call fails, a template summary / unavailable chat reply is used so the page cannot go blank.

**In development**  
Cursor (agent chat, including implementation, tests, UI, theming, deploy wiring, and this README). Research for sources (Meeus, HKO, Cheiro, Calendar Reform Committee, Decoz vs Millman) was done in that same workflow and checked against the named texts, not left as unverified model recall.

No other coding assistants were used as a second pair of hands on the repo.

**Approximate time**  
On the order of **20–25 hours** of assisted build and review: engine + pytest, React UI, grounded chat, light/dark theme, Render/Vercel hosting, and documentation. That is wall-clock working time on the assignment, not model-token time.

---

## Repository layout

```
backend/     FastAPI app, engine, tests, .env.example
frontend/    React + Vite app (dev server on port 4200)
docs/        working design-decision log
render.yaml  Render service definition
```
