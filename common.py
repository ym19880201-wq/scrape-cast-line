import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

LINE_CHANNEL_ACCESS_TOKEN = "H7jR4YDmRg5KF7sYDHByQ0FFMHd5YO/i0tuDfY7AcHXejpZQomTZ+9h0qE8Fghx6kXTwD9CnDx5T2U8EKoIxpBDFzef/eMIoIy//ZN4kSdtHtQS0KTPmcjN2CzkNLnnFcmGZaUSzd/zAjNsx3wdjLgdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U01a41d2bfd8d61e7b708b48aa5056738"


def clean_name(name):
    if not name:
        return ""

    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    name = name.replace("\u3000", " ").strip()

    while name.endswith("の"):
        name = name[:-1].strip()

    return name


def fetch(url):
    last_error = None

    for attempt in range(3):
        try:
            res = requests.get(url, headers=HEADERS, timeout=30)
            res.raise_for_status()
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text("\n", strip=True)
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            title = soup.title.get_text() if soup.title else ""
            return title, lines
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(2)
            else:
                raise last_error


def is_time(s):
    return re.search(r"\d{1,2}:\d{2}", s)


def parse_torihada_schedule(lines):
    shifts = []

    start = -1
    for i, line in enumerate(lines):
        if line == "週間スケジュール":
            start = i + 1
            break

    if start == -1:
        return shifts

    dates = []
    idx = start

    while idx < len(lines) and len(dates) < 7:
        if idx + 1 < len(lines):
            if re.fullmatch(r"\d{2}/\d{2}", lines[idx]) and re.fullmatch(r"\(.+\)", lines[idx + 1]):
                dates.append(lines[idx] + lines[idx + 1])
                idx += 2
                continue
        idx += 1

    statuses = []
    while idx < len(lines) and len(statuses) < 7:
        line = lines[idx]
        if line in ["休み", "未定"] or re.fullmatch(r"\d{1,2}:\d{2}～\d{1,2}:\d{2}", line):
            statuses.append(line)
        idx += 1

    count = min(len(dates), len(statuses))

    for i in range(count):
        if statuses[i] not in ["休み", "未定"]:
            shifts.append(dates[i])

    return list(dict.fromkeys(shifts))


def build_message(results):
    lines = []
    lines.append("出勤確認結果")
    lines.append("")

    for item in results:
        shop = item["shop"] if item["shop"] else "店名不明"
        name = item["name"] if item["name"] else "取得失敗"
        shifts_text = "、".join(item["shifts"]) if item["shifts"] else "出勤予定なし"

        lines.append(f"{shop}　{name}")
        lines.append(f"→ {shifts_text}")
        lines.append("")

    message = "\n".join(lines).strip()

    if len(message) > 4900:
        message = message[:4900]

    return message


def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    res = requests.post(url, headers=headers, json=payload, timeout=20)
    res.raise_for_status()
    return res
