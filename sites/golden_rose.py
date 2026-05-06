import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup


SHOP_NAME = "ゴールデンローズ"

WEEKDAY_MAP = {
    "月曜日": "月",
    "火曜日": "火",
    "水曜日": "水",
    "木曜日": "木",
    "金曜日": "金",
    "土曜日": "土",
    "日曜日": "日",
    "月": "月",
    "火": "火",
    "水": "水",
    "木": "木",
    "金": "金",
    "土": "土",
    "日": "日",
}


def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    response.encoding = response.apparent_encoding
    return response.text


def clean_text(value):
    return re.sub(r"\s+", " ", value).strip()


def extract_cast_name(soup):
    heading = soup.find("h3")
    if heading:
        name = clean_text(heading.get_text(" ", strip=True))
        if name:
            return name

    text = soup.get_text("\n", strip=True)
    lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]

    for i, line in enumerate(lines):
        if "Therapist" in line and "セラピスト情報" in line:
            if i + 1 < len(lines):
                return lines[i + 1]

    return "名前取得失敗"


def normalize_date(date_text, weekday_text):
    today = datetime.now()

    date_text = clean_text(date_text)
    weekday_text = clean_text(weekday_text)

    if date_text == "本日":
        month = today.month
        day = today.day
        weekday = ["月", "火", "水", "木", "金", "土", "日"][today.weekday()]
        return f"{month:02d}/{day:02d}({weekday})"

    match = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})", date_text)
    if not match:
        return ""

    month = int(match.group(1))
    day = int(match.group(2))

    weekday = ""
    weekday_match = re.search(r"([月火水木金土日]曜日?)", weekday_text)
    if weekday_match:
        weekday = WEEKDAY_MAP.get(weekday_match.group(1), "")

    if weekday:
        return f"{month:02d}/{day:02d}({weekday})"

    return f"{month:02d}/{day:02d}"


def extract_schedule(soup):
    text = soup.get_text("\n", strip=True)
    lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]

    schedules = []

    for i, line in enumerate(lines):
        is_today = line == "本日"
        is_date = re.fullmatch(r"\d{1,2}\s*/\s*\d{1,2}", line)

        if not is_today and not is_date:
            continue

        weekday_text = ""
        time_text = ""

        if is_today:
            if i + 1 < len(lines):
                time_text = lines[i + 1]
        else:
            if i + 1 < len(lines):
                weekday_text = lines[i + 1]
            if i + 2 < len(lines):
                time_text = lines[i + 2]

        if not time_text:
            continue

        if "未定" in time_text or "休" in time_text:
            continue

        if not re.search(r"\d{1,2}:\d{2}\s*[～〜-]\s*\d{1,2}:\d{2}", time_text):
            continue

        formatted_date = normalize_date(line, weekday_text)

        if formatted_date:
            schedules.append(formatted_date)

    return schedules


def parse_golden_rose(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    cast_name = extract_cast_name(soup)
    schedules = extract_schedule(soup)

    return {
        "shop": SHOP_NAME,
        "name": cast_name,
        "shifts": schedules,
        "url": url,
        "shop_name": SHOP_NAME,
        "cast_name": cast_name,
        "schedule": ", ".join(schedules) if schedules else "出勤予定なし",
    }


def parse(url):
    return parse_golden_rose(url)
