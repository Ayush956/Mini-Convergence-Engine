"""Compare our Meeus solar longitude against JPL Horizons.

Horizons quantity 31 (ObsEcLon) for target Sun (COMMAND=10) seen from the
geocentre (CENTER=500@399) is the apparent ecliptic-of-date longitude, the
same quantity Meeus's apparent longitude computes.

Uses curl because urllib cannot verify the certificate chain in this
environment.
"""

import os
import re
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app.engine.sun_sign import apparent_solar_longitude  # noqa: E402

MOMENTS = [
    datetime(1995, 8, 15, 5, 0),
    datetime(2000, 1, 1, 12, 0),
    datetime(2026, 9, 30, 16, 0),
    datetime(1950, 1, 3, 18, 30),
    datetime(1901, 3, 1, 0, 0),
    datetime(2099, 11, 11, 11, 11),
    # Near the cardinal points, where a cusp decision is most delicate.
    datetime(2024, 3, 20, 3, 6),
    datetime(2024, 6, 20, 20, 51),
    datetime(2024, 9, 22, 12, 43),
    datetime(2024, 12, 21, 9, 20),
]


def horizons_longitude(moment):
    from datetime import timedelta

    start = moment.strftime("%Y-%m-%d %H:%M")
    # Horizons needs a non-empty interval to return any rows at all.
    stop = (moment + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
    command = [
        "curl", "-s", "--max-time", "60", "-G",
        "https://ssd.jpl.nasa.gov/api/horizons.api",
        "--data-urlencode", "format=text",
        "--data-urlencode", "COMMAND='10'",
        "--data-urlencode", "OBJ_DATA='NO'",
        "--data-urlencode", "MAKE_EPHEM='YES'",
        "--data-urlencode", "EPHEM_TYPE='OBSERVER'",
        "--data-urlencode", "CENTER='500@399'",
        "--data-urlencode", "START_TIME='{}'".format(start),
        "--data-urlencode", "STOP_TIME='{}'".format(stop),
        "--data-urlencode", "STEP_SIZE='1 m'",
        "--data-urlencode", "QUANTITIES='31'",
        "--data-urlencode", "CSV_FORMAT='YES'",
    ]
    text = subprocess.run(command, capture_output=True, text=True, check=True).stdout

    block = re.search(r"\$\$SOE\n(.*?)\$\$EOE", text, re.S)
    if not block:
        raise RuntimeError("no ephemeris block for {}".format(start))
    first = block.group(1).strip().splitlines()[0]
    numbers = [f.strip() for f in first.split(",") if re.match(r"^\s*-?\d+\.\d+\s*$", f)]
    return float(numbers[0])


def main():
    worst = 0.0
    print("{:<20} {:>12} {:>12} {:>11}".format("UTC", "horizons", "ours", "diff deg"))
    fixtures = []
    for moment in MOMENTS:
        reference = horizons_longitude(moment)
        ours = apparent_solar_longitude(moment)
        diff = abs((ours - reference + 180) % 360 - 180)
        worst = max(worst, diff)
        fixtures.append((moment, reference))
        print(
            "{:<20} {:>12.6f} {:>12.6f} {:>11.6f}".format(
                moment.strftime("%Y-%m-%d %H:%M"), reference, ours, diff
            )
        )

    print("\nworst disagreement: {:.6f} deg".format(worst))
    print("Meeus states ~0.01 deg for this method")
    print("worst, as clock time at a cusp: {:.1f} minutes".format(
        worst / 0.9856 * 24 * 60))

    print("\n--- fixtures for the test file ---")
    for moment, reference in fixtures:
        print("    (datetime({}, {}, {}, {}, {}), {}),".format(
            moment.year, moment.month, moment.day, moment.hour, moment.minute,
            reference))


if __name__ == "__main__":
    main()
