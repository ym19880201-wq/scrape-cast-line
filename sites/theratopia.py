from common import fetch, is_time
import re


def parse(url):
    title, lines = fetch(url)

    name = ""
    shifts = []

    title = title.strip()

    if "プロフィール" in title:
        name = title.split("プロフィール")[0].strip()
    elif "｜" in title:
        name = title.split("｜")[0].strip()
    elif "|" in title:
        name = title.split("|")[0].strip()

    if not name:
        for i, line in enumerate(lines):
            if line in ["Photo.3", "Photo3"] and i + 1 < len(lines):
                name = lines[i + 1].strip()
                break

    for i in range(len(lines) - 2):
        if re.match(r"\d{2}/\d{2}", lines[i]) and "(" in lines[i + 1] and is_time(lines[i + 2]):
            shifts.append(lines[i] + lines[i + 1])

    return name, list(dict.fromkeys(shifts))
