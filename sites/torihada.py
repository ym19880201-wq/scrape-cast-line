import re

from common import fetch, parse_torihada_schedule


def pick_name_from_text(text):
    if not text:
        return ""

    text = str(text).strip()

    text = re.sub(r"[|｜¦￨∣].*$", "", text).strip()
    text = re.sub(r"\s*名古屋.*$", "", text).strip()
    text = re.sub(r"\s*TORIHADA.*$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+", " ", text).strip()

    return text


def parse(url):
    title, lines = fetch(url)

    name = ""

    if lines:
        name = pick_name_from_text(lines[0])

    if not name:
        for i, line in enumerate(lines):
            if line == "マイクロ" and i + 1 < len(lines):
                name = pick_name_from_text(lines[i + 1])
                if name:
                    break

    if not name and title:
        name = pick_name_from_text(title)

    shifts = parse_torihada_schedule(lines)

    return name, shifts
