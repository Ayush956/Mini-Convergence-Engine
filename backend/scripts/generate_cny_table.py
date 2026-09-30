"""Fetch HKO Gregorian-Lunar conversion tables and extract Chinese New Year.

Caches downloads under /tmp/hko so reruns are cheap.

The animal is derived from the earthly branch of the sexagenary year name,
which is canonical, and then cross-checked against the animal character HKO
prints in the header. HKO is not consistent about that character (it writes
Dog as both 狗 and 犬), so the branch is the source of truth and the header
character is only a check.
"""

import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen

URL = "https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T{}c.txt"
CACHE = "/tmp/hko"

# Earthly branch -> animal. The canonical 12-cycle.
BRANCH_ANIMALS = [
    ("子", "Rat"), ("丑", "Ox"), ("寅", "Tiger"), ("卯", "Rabbit"),
    ("辰", "Dragon"), ("巳", "Snake"), ("午", "Horse"), ("未", "Goat"),
    ("申", "Monkey"), ("酉", "Rooster"), ("戌", "Dog"), ("亥", "Pig"),
]
BRANCH_TO_ANIMAL = dict(BRANCH_ANIMALS)

# Characters HKO uses in the "肖X" header, grouped by the animal they mean.
HEADER_SYNONYMS = {
    "Rat": {"鼠"}, "Ox": {"牛"}, "Tiger": {"虎"}, "Rabbit": {"兔"},
    "Dragon": {"龍", "龙"}, "Snake": {"蛇"}, "Horse": {"馬", "马"},
    "Goat": {"羊"}, "Monkey": {"猴"}, "Rooster": {"雞", "鸡"},
    "Dog": {"狗", "犬"}, "Pig": {"豬", "猪"},
}

HEADER = re.compile(r"^\ufeff?(\d{4})\(\s*(.)(.)\s*-\s*肖\s*(.)\s*\)")
DAY_ROW = re.compile(r"^(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\S+)")


def fetch(year):
    path = os.path.join(CACHE, "{}.txt".format(year))
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        with open(path, encoding="utf-8") as handle:
            return year, handle.read()
    for attempt in range(4):
        try:
            with urlopen(URL.format(year), timeout=45) as response:
                text = response.read().decode("utf-8")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            return year, text
        except Exception as exc:  # noqa: BLE001
            if attempt == 3:
                return year, "ERROR: {}".format(exc)
    return year, "ERROR"


def parse(year, text):
    lines = text.splitlines()
    header = HEADER.match(lines[0]) if lines else None
    if not header:
        raise ValueError("{}: no header, got {!r}".format(year, lines[:1]))

    header_year, stem, branch, animal_char = header.groups()
    if int(header_year) != year:
        raise ValueError("{}: header says {}".format(year, header_year))

    animal = BRANCH_TO_ANIMAL.get(branch)
    if animal is None:
        raise ValueError("{}: unknown branch {!r}".format(year, branch))

    # Cross-check: the printed character must agree with the branch.
    if animal_char not in HEADER_SYNONYMS[animal]:
        raise ValueError(
            "{}: branch {} means {} but header prints {!r}".format(
                year, branch, animal, animal_char
            )
        )

    new_year = None
    for line in lines[1:]:
        row = DAY_ROW.match(line)
        if row and row.group(4) == "正月":
            new_year = (int(row.group(1)), int(row.group(2)), int(row.group(3)))
            break

    if new_year is None:
        raise ValueError("{}: no 正月 row found".format(year))

    _, month, day = new_year
    if not ((month == 1 and day >= 21) or (month == 2 and day <= 20)):
        raise ValueError("{}: new year {} outside 21 Jan - 20 Feb".format(year, new_year))

    return new_year, stem + branch, animal


def main():
    os.makedirs(CACHE, exist_ok=True)
    years = list(range(1901, 2101))
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = dict(pool.map(fetch, years))

    failures = [y for y, text in results.items() if text.startswith("ERROR")]
    if failures:
        sys.exit("fetch failed for: {}".format(failures))

    rows = [(year,) + parse(year, results[year]) for year in years]

    # The sexagenary cycle must advance by exactly one every year.
    for index in range(1, len(rows)):
        previous = rows[index - 1][2]
        current = rows[index][2]
        p_branch = BRANCH_ANIMALS.index((previous[1], BRANCH_TO_ANIMAL[previous[1]]))
        c_branch = BRANCH_ANIMALS.index((current[1], BRANCH_TO_ANIMAL[current[1]]))
        if (p_branch + 1) % 12 != c_branch:
            sys.exit("cycle break at {}: {} -> {}".format(rows[index][0], previous, current))

    for year, new_year, ganzhi, animal in rows:
        print("{} {} {} {}".format(year, new_year, ganzhi, animal))


if __name__ == "__main__":
    main()
