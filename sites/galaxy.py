from common import fetch, is_time
import re


def parse(url):
    title, lines = fetch(url)

    name = ""
    shifts = []

    name = title.split("/")[0].strip()

    for i in range(len(lines) - 1):
        if re.match(r"\d+/\d+\(.+\)", lines[i]) and is_time(lines[i + 1]):
            shifts.append(lines[i])

    return name, list(dict.fromkeys(shifts))
