# Design decisions

A running log of choices made while building the Mini Convergence Engine, and why.
Feeds directly into README sections 2 (assumptions), 3 (edge cases), 4 (trait-mapping
rationale), 6 (confidence-formula critique) and 8 (AI usage).

## Stack

| Layer | Choice | Reason |
| --- | --- | --- |
| Frontend | Angular 21 + Angular Material | Angular CLI 21.2.9 already installed; Material gives usable date/time pickers without hand-rolling them |
| Backend | FastAPI (Python 3.9.6) | Automatic `/docs` lets the calculation engine be verified before any UI exists |
| Repo layout | Monorepo: `frontend/` + `backend/` | Submission checklist asks for a single repository URL |
| Frontend host | Vercel (static build) | No cold start for static assets |
| Backend host | Render + keep-alive cron ping | Free tier spins down after ~15 min idle; a reviewer opening a cold URL would otherwise wait 30-60s, and "if the URL does not open, the submission cannot be evaluated". Render's own cron jobs are not on the free tier, so the ping has to come from outside (GitHub Actions schedule or a free cron service) |

### Python 3.9: a choice, not a constraint

Using the macOS system Python 3.9.6, inside a `venv` under `backend/` so the system
installation is untouched. This is a deliberate trade-off, not something forced:
`pyenv` or Homebrew could supply 3.12 just as easily.

Accepted downside: **3.9 reached end of life in October 2025**, so it receives no
further security patches, and FastAPI/Pydantic will eventually drop support for it.
Taken anyway because the dependency set here is small and the deployment is a
throwaway demo, so the benefit of zero toolchain setup outweighs the risk over the
life of this project. Render defaults to a much newer interpreter, so the version
must be pinned explicitly there (`runtime.txt` or `PYTHON_VERSION`).

Consequence for code style: PEP 585 builtin generics (`list[str]`, `dict[str, int]`)
are fine on 3.9, but **PEP 604 unions (`str | None`) fail wherever the annotation is
evaluated at runtime** — which includes every Pydantic model, since Pydantic resolves
annotations to build its validators. Use `Optional[str]` / `Union[...]` throughout.

## Calculation strategy

Overall principle: **libraries for plumbing, own code for domain logic.**

The brief says "verify any library or formula you use against authoritative sources"
and "do not assume a library is correct because it is popular". For all five methods,
verifying a third-party library costs the same effort as writing the logic outright —
and writing it means every line can be explained and modified during the live review,
which is 30% of the grade. The Sun sign is the only one where the *formula* comes from
a published source rather than being derived here; the code implementing it is still
our own.

Approach and source are settled for all five.

| Method | Approach (settled) | Source |
| --- | --- | --- |
| Western Sun Sign | Solar ecliptic longitude via the low-precision algorithm from Meeus, *Astronomical Algorithms*; sign = floor(longitude / 30) | Meeus ch. 25 |
| Chinese Zodiac | Own code over a hardcoded Chinese New Year date table | Hong Kong Observatory |
| Numerology Life Path | Own code, Pythagorean, component-first reduction, master numbers preserved | Decoz lineage; see below |
| Name Number | Own code, Chaldean letter table | Cheiro (1926), primary text |
| Vedic Vara | Own code: weekday with a sunrise day-boundary rule, plus planetary ruler table | Calendar Reform Committee (1955) |

Libraries used deliberately: FastAPI, Pydantic, pytest, Angular, Angular Material.
No astronomy, lunar-calendar or numerology library is a dependency, not even a
development one. Date arithmetic uses the standard library `datetime` only.

**Settled:** all five methods are own code. For four of them the choice is not really
a trade-off — Life Path, Name Number, Vara and the Chinese Zodiac lookup are each on
the order of ten to fifteen lines, so any library would cost more code in adaptation
than it saved, and would still need verifying. The Sun sign is the only one where a
library (`pyswisseph`) would have saved real work; own Meeus code was chosen anyway
so the cusp behaviour can be explained and modified live.

### Sources

**Sun sign — Meeus, *Astronomical Algorithms*, ch. 25 (low-accuracy solar method).**
Verified against NASA JPL Horizons, quantity 31 (`ObsEcLon`) with target = Sun and
observer = geocenter, which returns the geocentric apparent ecliptic-of-date longitude
corrected for light-time, deflection and aberration — the same quantity Meeus's
"apparent longitude" computes, so the comparison is apples to apples. The Horizons
manual itself points at exactly this configuration for Earth-season work.
<https://ssd.jpl.nasa.gov/horizons/manual.html>

**Chinese zodiac — Hong Kong Observatory, Gregorian-Lunar Calendar Conversion Table,
1901-2100.** A government meteorological authority, published per year as text and
PDF, and also as an open dataset with an API on `data.gov.hk`.
<https://www.hko.gov.hk/en/gts/time/conversion.htm>

Two consequences worth noting. The HKO tables carry the sexagenary (ganzhi) year name
directly, so the animal can be *read from the source* rather than derived with a
modulo-12 offset from an epoch year — which removes the most likely off-by-one bug in
this method entirely. And HKO publishes its own accuracy caveat: where a new moon or
solar term falls near midnight, the tabulated date can be out by a day, and they name
the specific cases (the new moons of 28 Sep 2057, 4 Sep 2089, 7 Aug 2097, and a few
solar terms). None of these is a Chinese New Year inside any plausible birth date, so
this does not affect us, but it is documented rather than discovered later.

**Name number — Cheiro (Count Louis Hamon), *Cheiro's Book of Numbers* (1926).**
Checked against the primary text, not a secondary table. Cheiro sets the values out
inline and explains the missing 9: "there is no number 9 given in the above alphabet,
for the simple reason that those ancient masters of Occultism knew that in the
'Highest Sphere' the number 9 represents the 9-lettered name of God."

| A | B | C | D | E | F | G | H | I | J | K | L | M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 3 | 4 | 5 | 8 | 3 | 5 | 1 | 1 | 2 | 3 | 4 |

| N | O | P | Q | R | S | T | U | V | W | X | Y | Z |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 7 | 8 | 1 | 2 | 3 | 4 | 6 | 6 | 6 | 5 | 1 | 7 |

Two Cheiro rules that are *not* about the table, and that we depart from deliberately:
he reads the two-digit compound total for its own meaning before reducing, and he says
to use "the most used Christian and Surname" rather than the full legal name. The brief
collects one full name field and gives no way to know which part a person goes by, so
we use the full name as entered and reduce to a single digit. Both departures go in the
README assumptions section.

**Life path — component-first reduction, master numbers preserved.** This one is a
documented assumption rather than a correctness claim, because the authorities split:
Hans Decoz and numerologist.com prescribe reducing month, day and year separately and
call it the only correct method, while Dan Millman and others sum every digit at once
and call *that* the traditional Pythagorean method. There is no neutral tiebreaker.

Chosen rule, stated unambiguously so the code has one reading:

1. Reduce the month, the day, and the year to a single digit each, stopping early if
   an intermediate total is 11, 22 or 33.
2. Sum those three results.
3. Reduce the sum, stopping if it is 11, 22 or 33.

Preserving the master numbers at the final stage is not contested — every source found
agrees, and the ones that reduce 11/22/33 to 2/4/6 are described as mistaken even by
sources that otherwise disagree with each other.

How much the choice matters, measured rather than assumed: across every date from 1950
to 2010 (22,280 days), the two methods disagree on **2,994 of them, 13.4%**. Every
disagreement is a master number versus its own reduction — the pairs are only ever
(11, 2), (22, 4) and (33, 6) in one direction or the other, never anything else.

One popular justification for component-first turns out to be false and should not be
repeated in the README: it is widely claimed to "preserve master numbers that the flat
method loses". In aggregate the opposite holds. Over that same range, flat-sum yields a
master number on 2,281 of the divergent dates and component-first on only 713, so
component-first produces master numbers about three times *less* often. It is chosen
for the per-component structure being easier to explain and defend, not for master
numbers.

Worked example, 4 January 1950, which is one of the divergent dates:

- Component-first: month 1, day 4, year 1+9+5+0 = 15 → 6. Sum 1 + 4 + 6 = 11, a master
  number, so stop. **Life Path 11.**
- Flat-sum, for contrast: 1+9+5+0+0+1+0+4 = 20 → 2. Life Path 2.

Also worth a note: some sources apply karmic-debt readings (13, 14, 16, 19) to
intermediate totals. Not implemented — out of scope for a convergence score, and it
would add another contested rule to defend.

**Vara — Report of the Calendar Reform Committee, Government of India (CSIR, 1955),
chaired by Meghnad Saha.** The authority for the sunrise day boundary, in its own
words: "the civil day (savana), according to Hindu religious practices, should start
from sunrise", and elsewhere it defines the savana day as running "between sunrise to
sunrise". The seven planetary lords (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
for Sunday through Saturday) are not contested by any source found; the ordering falls
out of the hora sequence, where the lord of the first hora after sunrise rules the day.
<https://archive.org/stream/calendar_reform_comittee_report/calendar_reform_comittee_report_djvu.txt>

### Verification strategy

The brief grades verification, not just correctness, so every method gets pytest
known-answer cases against a named external source rather than against its own output:

| Method | Verified against |
| --- | --- |
| Western Sun Sign | JPL Horizons solar longitude for a handful of dates, deliberately including cusp births and a leap year |
| Chinese Zodiac | The published Chinese New Year table, spot-checked row by row; plus Jan/early-Feb birthdays that `year % 12` would get wrong |
| Life Path | Hand-computed cases including 4 Jan 1950 (a master-number result) and a date where the flat-sum method diverges, asserting our documented answer |
| Name Number | The two worked examples in Cheiro's own text (Lloyd George, Baldwin), plus a name containing every letter class |
| Vedic Vara | Hand-computed cases either side of the 06:00 sunrise boundary, including just before and just after midnight |

Note on the Sun sign: a fixed table of sign date ranges is not acceptable, because
cusp dates drift by about a day across years (the tropical year is 365.2422 days and
the Gregorian calendar only approximates it, so Aries can begin on 19, 20 or 21
March). Computing longitude handles that; a table silently misplaces cusp births.

### Why not an ephemeris library for the Sun

`pyswisseph` / `skyfield` / `astropy` would all be more accurate. The reason for not
using one is the general rule above — own code can be explained line by line in the
live review — and not a technical objection to any of them. Stated precisely, so the
answer holds up if a reviewer names a specific library:

- `skyfield` downloads an ephemeris file of tens of megabytes at first use. Real
  friction on a free tier, but it is disk and cold-start cost, not memory; Render's
  512 MB free-tier figure is a RAM limit and would not be threatened by it.
- `pyswisseph` has **no** such problem: it ships with the built-in Moshier ephemeris
  and needs no data files at all to compute solar position. Size is not an argument
  against it. It is not used purely because of the explain-it-live rule.

Accuracy is sufficient either way. Meeus gives the low-accuracy solar method an
accuracy of about 0.01 degrees (*Astronomical Algorithms*, ch. 25; the ~0.0001 degree
figure in the same chapter belongs to the truncated VSOP87 method, which is not what
is used here). At the Sun's mean motion of roughly 0.9856 degrees per day, 0.01
degrees is about 15 minutes of clock time at a sign cusp. That is negligible next to
the IST assumption below, where an unknown birthplace can put the true local time out
by hours. The dominant error is the timezone guess, not the formula.

### Why a Chinese New Year table rather than a lunar-calendar library

The Chinese year begins at Chinese New Year (falling between 21 Jan and 20 Feb), not
1 January, so `year % 12` is wrong for anyone born in Jan or early Feb. The date is
astronomically defined and cannot be derived with simple arithmetic. A hardcoded table
is spot-checkable against a published source row by row, whereas a library would still
need verifying — the same work, with an added dependency.

## Trait mapping and convergence scoring

**Undecided — this is the core of the assignment and nothing is settled yet.** The five
systems each emit a different kind of token (a sign, an animal, two integers, a
weekday ruler), so they cannot be compared until every one is projected onto a single
shared trait vocabulary. Decisions still needed:

- The trait vocabulary itself: fixed closed list, or derived from the sources? A closed
  list is defensible and testable; a derived one is more faithful but unbounded.
- Per-system mapping tables, each with a cited source. This is README section 4 and is
  graded, so every row needs an authority behind it, not an invented association.
- Whether a system contributes one trait or several, and whether traits carry weights.
  Unweighted is easier to defend; weighted needs a justification for each weight.
- What "agreement" means: identical trait, or traits in the same cluster. Clustering
  raises convergence scores and needs its own defence.

## The `1 - 1/2^N` confidence formula

**Critique still to be written — README section 6.** Initial observations to develop:

- It depends only on `N`, the count of agreeing systems, and ignores how many systems
  were consulted. Two agreeing out of two scores the same as two out of five, though
  the second is much weaker evidence.
- It treats the systems as independent. They are not: Life Path and Name Number are
  both digit reductions, and Sun sign, Chinese zodiac and Vara are all functions of the
  same birth instant. `1/2^N` is the probability of `N` independent coin flips
  agreeing, so the premise fails.
- It cannot return 0, and approaches 1 fast: `N = 4` already gives 93.75%, which
  overstates confidence in what is an unfalsifiable domain.
- Needs a concrete proposal for something better, or a reasoned argument for keeping it
  as specified while naming its flaws.

## AI usage

**To be recorded as the build proceeds — README section 8.** The OpenRouter key
provided with the brief implies an LLM call somewhere in the product; decide and
document what it is actually for (narrative summary of the convergence result is the
obvious candidate) versus what stays deterministic. Keep the boundary explicit: the
five calculations and the convergence score must be pure code, so results are
reproducible and testable, with the model used only for presentation. Also log which
AI tools were used during development, since the brief asks for that separately.

## Open questions to resolve during research

- ~~Life Path: reduction order and master numbers.~~ **Closed.** Component-first, master
  numbers preserved; the 13.4% divergence from the alternative is quantified above.
- ~~Chaldean: confirm the letter-to-value table.~~ **Closed.** Checked against Cheiro's
  primary text; the table there matches the mainstream secondary tables letter for
  letter, all 26. The earlier worry that "several sources disagree on a few letters"
  did not survive checking — the variation is between Chaldean and Pythagorean systems,
  not within Chaldean.
- Vara: the sunrise boundary itself is settled and cited. What is still assumed is the
  sunrise *time*: true sunrise needs a location, which the brief never asks for, so a
  fixed 06:00 stands in. Document the consequence — a birth between local true sunrise
  and 06:00 (or the reverse) gets the neighbouring vara.
- Timezone: the brief collects a time of birth with no location. Assume IST.
- Sun sign cusps: with a timezone assumption, cusp placement is only as good as that
  assumption. Document the residual error.

## Notable observation

Time of birth affects **only** the Vedic Vara calculation (via the sunrise boundary)
and, marginally, a cusp sun sign. It is irrelevant to Life Path, Name Number and the
Chinese Zodiac. Worth stating explicitly in the README.

## Secrets

The OpenRouter API key lives only in `backend/.env`, which is gitignored. `.gitignore`
was part of the very first commit, alongside `README.md` and ahead of any code or
config, so no secret has ever been tracked. The assignment brief (which contains the
key in plain text) is kept outside the repo, and `*.pdf` / `*.pages` are ignored as a
safety net — `*.pages` was added one commit later than the rest.
