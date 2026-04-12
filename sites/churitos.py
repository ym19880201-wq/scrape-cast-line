from common import fetch, is_time
import re

def parse(url):
    title, lines = fetch(url)

    name = ""
    shifts = []

    if "プロフィール" in title:
        name = title.split("プロフィール")[0].strip()

    for i in range(len(lines) - 1):
        if re.match(r"\d+\(.+\)", lines[i]) and is_time(lines[i + 1]):
            d = int(re.match(r"(\d+)", lines[i]).group(1))
            shifts.append(f"04/{d:02d}" + lines[i][lines[i].find("("):])

    return name, list(dict.fromkeys(shifts))
