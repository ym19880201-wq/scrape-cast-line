import requests
from bs4 import BeautifulSoup
import re


def parse(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers, timeout=20)

    html = res.content.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, 'html.parser')

    name = ""
    shifts = []

    text = soup.get_text("\n", strip=True)
    lines = text.split("\n")

    for i in range(len(lines)):
        if "歳" in lines[i] and i > 0:
            name = lines[i - 1].strip()
            break

    for i in range(len(lines) - 1):
        date_text = ""

        if re.match(r"^\d+月\d+日\(.+\)$", lines[i]):
            date_text = lines[i]
            next_index = i + 1

        elif re.match(r"^\d+月\d+日$", lines[i]) and i + 1 < len(lines) and re.match(r"^\(.+\)$", lines[i + 1]):
            date_text = lines[i] + lines[i + 1]
            next_index = i + 2

        else:
            continue

        if next_index >= len(lines):
            continue

        next_line = lines[next_index]

        if "休" in next_line:
            continue

        if re.search(r"\d{1,2}:\d{2}", next_line):
            date_text = re.sub(r"(\d+)月(\d+)日", r"\1/\2", date_text)
            shifts.append(date_text)

    return name, list(dict.fromkeys(shifts))
