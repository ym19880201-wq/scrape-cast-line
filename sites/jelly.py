import re

from common import clean_name, fetch


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

    match = re.match(r"(.+?)\s*[|｜]", title)

    if match:
        name = clean_name(match.group(1))

        if name:
            return name

    for index, line in enumerate(lines):
        line = _normalize_text(line)

        if line == "年齢" and index > 0:
            name = clean_name(lines[index - 1])

            if name:
                return name

    return ""


def _format_date(date_text):
    match = re.fullmatch(
        r"(\d{1,2})月(\d{1,2})日\(([月火水木金土日])\)",
        date_text,
    )

    if not match:
        return ""

    month = int(match.group(1))
    day = int(match.group(2))
    weekday = match.group(3)

    return f"{month:02d}/{day:02d}({weekday})"


def _is_shift_time(text):
    text = _normalize_text(text)

    return bool(
        re.fullmatch(
            r"\d{1,2}:\d{2}\s*[～〜~-]\s*\d{1,2}:\d{2}",
            text,
        )
    )


def _extract_shifts(lines):
    normalized_lines = [
        _normalize_text(line)
        for line in lines
        if _normalize_text(line)
    ]

    date_pattern = re.compile(
        r"\d{1,2}月\d{1,2}日\([月火水木金土日]\)"
    )

    shifts = []
    seen_dates = set()

    for index, line in enumerate(normalized_lines):
        if not date_pattern.fullmatch(line):
            continue

        formatted_date = _format_date(line)

        if not formatted_date:
            continue

        has_work_time = False
        next_index = index + 1

        while next_index < len(normalized_lines):
            next_line = normalized_lines[next_index]

            if date_pattern.fullmatch(next_line):
                break

            if _is_shift_time(next_line):
                has_work_time = True
                break

            next_index += 1

        if not has_work_time:
            continue

        if formatted_date in seen_dates:
            continue

        seen_dates.add(formatted_date)
        shifts.append(formatted_date)

    return shifts


def parse(url):
    title, lines = fetch(url)

    name = _extract_name(title, lines)
    shifts = _extract_shifts(lines)

    return name, shifts