from common import fetch, is_time
import re


def parse(url):
    title, lines = fetch(url)

    name = "あやの"
    shifts = []

    for i in range(len(lines) - 1):
        if re.match(r"\d+/\d+", lines[i]) and is_time(lines[i + 1]):
            m, d = lines[i].split("/")
            shifts.append(f"{int(m):02d}/{int(d):02d}")

    return name, list(dict.fromkeys(shifts))
