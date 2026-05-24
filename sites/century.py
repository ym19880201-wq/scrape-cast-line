import re
import requests
from bs4 import BeautifulSoup


SHOP_NAME = "センチュリー"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "https://www.google.com/",
}


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def fetch(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def parse(url):
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n")
    lines = [clean_text(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    cast_name = ""

    for line in lines:
        if line == "園田まお":
            cast_name = line
            break

    if not cast_name:
        for line in lines:
            if "園田まお" in line:
                cast_name = "園田まお"
                break

    schedule_start_index = None

    for index, line in enumerate(lines):
        if line == "出勤スケジュール":
            schedule_start_index = index + 1
            break

    shifts = []

    if schedule_start_index is not None:
        schedule_lines = lines[schedule_start_index:]

        for index, line in enumerate(schedule_lines):
            if re.fullmatch(r"\d{2}/\d{2}\[[月火水木金土日]\]", line):
                date_text = line

                if index + 1 < len(schedule_lines):
                    time_text = schedule_lines[index + 1]
                else:
                    time_text = ""

                if time_text and time_text != "-":
                    date_text = date_text.replace("[", "(").replace("]", ")")
                    shifts.append(date_text)

    if not cast_name:
        cast_name = "名前取得失敗"

    return {
        "shop": SHOP_NAME,
        "url": url,
        "name": cast_name,
        "shifts": shifts,
    }
