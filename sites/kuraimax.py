from common import fetch, is_time
import re


def parse(url):
    title, lines = fetch(url)

    name = ""
    shifts = []

    for i in range(len(lines) - 1):
        m = re.match(r"(\d{2})月(\d{2})日(\(.+\))", lines[i])
        if m and is_time(lines[i + 1]):
            shifts.append(f"{m.group(1)}/{m.group(2)}{m.group(3)}")

    for i, line in enumerate(lines):
        if line == "Name" and i + 1 < len(lines):
            name = lines[i + 1]

    return name, list(dict.fromkeys(shifts))
