import re

from common import clean_name, fetch, is_time


def _normalize_text(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("\u3000", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_name(title, lines):
    title = _normalize_text(title)

    m = re.search(r"(.+?)のプロフィール", title)
    if m:
        return clean_name(m.group(1))

    for i, line in enumerate(lines):
        line = _normalize_text(line)

        m = re.search(r"(.+?)のプロフィール", line)
        if m:
            return clean_name(m.group(1))

        if line in ["Photo.3", "Photo3"] and i + 1 < len(lines):
            return clean_name(lines[i + 1])

    return ""


def _extract_shifts(lines):
    start = -1

    for i, line in enumerate(lines):
        if _normalize_text(line) == "WEEKLY SCHEDULE":
            start = i + 1
            break

    if start == -1:
        return []

    block = [_normalize_text(x) for x in lines[start:start + 40] if _normalize_text(x)]

    dates = []
    idx = 0

    while idx < len(block) - 1 and len(dates) < 7:
        date_line = block[idx]
        wd_line = block[idx + 1]

        if re.fullmatch(r"\d{2}/\d{2}", date_line) and re.fullmatch(r"\([月火水木金土日]\)", wd_line):
            dates.append(date_line + wd_line)
            idx += 2
            continue

        idx += 1

    if not dates:
        return []

    statuses = []
    while idx < len(block) and len(statuses) < len(dates):
        line = block[idx]

        if line == "休み":
            statuses.append(line)
        elif is_time(line):
            statuses.append(line)

        idx += 1

    count = min(len(dates), len(statuses))
    shifts = []

    for i in range(count):
        if statuses[i] != "休み":
            shifts.append(dates[i])

    return list(dict.fromkeys(shifts))


def parse(url):
    title, lines = fetch(url)

    name = _extract_name(title, lines)
    shifts = _extract_shifts(lines)

    return name, shifts
