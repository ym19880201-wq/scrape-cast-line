import re

import requests
from bs4 import BeautifulSoup


SHOP_NAME = "メンズエステWhite"


def fetch_html(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    if response.encoding is None or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding

    return response.text


def clean_line(text):
    return re.sub(r"\s+", " ", text).strip()


def get_lines_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n", strip=True)
    lines = [clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    return lines


def extract_name(lines):
    for line in lines:
        match = re.search(r"^-\s*(.+?)のプロフィール\s*-$", line)
        if match:
            return match.group(1).strip()

    for line in lines:
        match = re.search(r"(.+?)のプロフィール", line)
        if match:
            name = match.group(1).strip()
            name = name.replace("｜メンズエステWhite", "").strip()
            if name:
                return name

    for i, line in enumerate(lines):
        if line == "セラピスト一覧" and i + 2 < len(lines):
            if lines[i + 1] == ">":
                return lines[i + 2].strip()

    return "取得できませんでした"


def extract_schedule(lines):
    schedule_results = []

    date_pattern = re.compile(r"^\d{2}/\d{2}\(.+?\)$")
    time_pattern = re.compile(r"^\d{1,2}:\d{2}$")

    schedule_index = None
    for i, line in enumerate(lines):
        if line == "Schedule":
            schedule_index = i
            break

    if schedule_index is None:
        return "取得できませんでした"

    i = schedule_index + 1

    while i < len(lines):
        line = lines[i]

        if line.startswith("営業時間："):
            break

        if not date_pattern.match(line):
            i += 1
            continue

        date_text = line

        if i + 1 >= len(lines):
            break

        next_line = lines[i + 1]

        if next_line == "--":
            i += 2
            continue

        if time_pattern.match(next_line):
            start_time = next_line
            end_time = None

            j = i + 2
            while j < len(lines):
                if date_pattern.match(lines[j]):
                    break
                if lines[j].startswith("営業時間："):
                    break
                if time_pattern.match(lines[j]):
                    end_time = lines[j]
                    break
                j += 1

            if end_time:
                schedule_results.append(f"{date_text} {start_time}～{end_time}")
                i = j + 1
                continue

        i += 1

    if not schedule_results:
        return "出勤予定なし"

    return ", ".join(schedule_results)


def parse(url):
    html = fetch_html(url)
    lines = get_lines_from_html(html)

    name = extract_name(lines)
    schedule = extract_schedule(lines)

    return {
        "shop": SHOP_NAME,
        "name": name,
        "schedule": schedule,
        "url": url,
    }
