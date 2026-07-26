import re

import requests
from bs4 import BeautifulSoup


SHOP_NAME = "ゴールドワゴン"

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


def format_date(date_text):
    match = re.fullmatch(
        r"(\d{2})月(\d{2})日\(([月火水木金土日])\)",
        date_text,
    )

    if not match:
        return ""

    month = match.group(1)
    day = match.group(2)
    weekday = match.group(3)

    return f"{month}/{day}({weekday})"


def parse(url):
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n")
    lines = [clean_text(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    cast_name = ""

    for line in lines:
        match = re.fullmatch(
            r"(.+?)\s*[（(]\d{1,2}[）)]",
            line,
        )

        if match:
            name = clean_text(match.group(1))

            if name and not name.startswith("T."):
                cast_name = name
                break

    shifts = []
    seen_dates = set()

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        for row_index, row in enumerate(rows):
            date_cells = row.find_all(["th", "td"])
            date_texts = [
                clean_text(cell.get_text(" ", strip=True))
                for cell in date_cells
            ]

            matched_dates = [
                date_text
                for date_text in date_texts
                if re.fullmatch(
                    r"\d{2}月\d{2}日\([月火水木金土日]\)",
                    date_text,
                )
            ]

            if not matched_dates:
                continue

            if row_index + 1 >= len(rows):
                continue

            time_cells = rows[row_index + 1].find_all(["th", "td"])
            time_texts = [
                clean_text(cell.get_text(" ", strip=True))
                for cell in time_cells
            ]

            for index, date_text in enumerate(date_texts):
                if not re.fullmatch(
                    r"\d{2}月\d{2}日\([月火水木金土日]\)",
                    date_text,
                ):
                    continue

                if index >= len(time_texts):
                    continue

                time_text = time_texts[index]

                if not time_text or time_text == "-":
                    continue

                formatted_date = format_date(date_text)

                if not formatted_date:
                    continue

                if formatted_date in seen_dates:
                    continue

                seen_dates.add(formatted_date)
                shifts.append(formatted_date)

            if shifts:
                break

        if shifts:
            break

    if not cast_name:
        cast_name = "名前取得失敗"

    return {
        "shop": SHOP_NAME,
        "url": url,
        "name": cast_name,
        "shifts": shifts,
    }