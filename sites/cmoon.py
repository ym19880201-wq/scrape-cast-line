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

    if not name:
        for i, line in enumerate(lines):
            if line in ["Photo.3", "Photo3"] and i + 1 < len(lines):
                name = lines[i + 1].strip()
                break

    name = clean_name(name)

    try:
        start = lines.index("週間スケジュール") + 1

        dates = []
        i = start
        while i < len(lines) and len(dates) < 7:
            if i + 1 < len(lines) and re.match(r"\d{2}/\d{2}", lines[i]):
                dates.append(lines[i] + lines[i + 1])
                i += 2
            else:
                i += 1

        data = lines[i:i + 20]

        p = 0
        for d in dates:
            if p >= len(data):
                break
            if data[p] not in ["未定", "休み"]:
                shifts.append(d)
                p += 2
            else:
                p += 1

    except Exception:
        pass

    return name, list(dict.fromkeys(shifts))
