from common import fetch, clean_name
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

    name = clean_name(name)

    for i in range(len(lines) - 4):
        if re.match(r"\d{2}/\d{2}\(.+\)", lines[i]):
            if lines[i + 1] != "--":
                shifts.append(lines[i])

    return name, list(dict.fromkeys(shifts))
