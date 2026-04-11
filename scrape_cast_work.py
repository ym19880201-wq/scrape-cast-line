import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

URLS = [
    "https://exe-mensspa.nagoya/profile.html?sid=32",
    "https://churitos01.com/profile?lid=148",
    "https://kuraimaxmax.com/profile.php?sid=399",
    "https://hosifuluspa.com/cast/%e3%81%82%e3%82%84%e3%81%ae/",
    "https://torihada-spa.men-es.jp/profile.html?sid=266",
    "https://felicia-garden.com/profile.php?sid=210",
    "https://galaxy-nagoya.com/cast/%E3%82%86%E3%82%8A",
    "https://galaxy-nagoya.com/cast/%E3%82%8C%E3%81%84",
    "https://esthe-theratopia.net/profile.html?sid=176",
    "https://torihada-spa.men-es.jp/profile.html?sid=305",
    "https://haniel-nagoya.net/profile.html?5082",
    "https://www.c-moon.info/profile/_uid/10617/"
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")


def fetch(url):
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = soup.title.get_text() if soup.title else ""
    return title, lines


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


def parse(url):
    title, lines = fetch(url)
    host = urlparse(url).netloc

    name = ""
    shifts = []

    if "のプロフィール" in title:
        name = title.split("のプロフィール")[0].strip()

    if "churitos01" in host:
        name = title.split("プロフィール")[0].strip()

        for i in range(len(lines) - 1):
            if re.match(r"\d+\(.+\)", lines[i]) and is_time(lines[i + 1]):
                d = int(re.match(r"(\d+)", lines[i]).group(1))
                shifts.append(f"04/{d:02d}" + lines[i][lines[i].find("("):])

    elif "hosifuluspa" in host:
        name = "あやの"

        for i in range(len(lines) - 1):
            if re.match(r"\d+/\d+", lines[i]) and is_time(lines[i + 1]):
                m, d = lines[i].split("/")
                shifts.append(f"{int(m):02d}/{int(d):02d}")

    elif "galaxy" in host:
        name = title.split("/")[0].strip()

        for i in range(len(lines) - 1):
            if re.match(r"\d+/\d+\(.+\)", lines[i]) and is_time(lines[i + 1]):
                shifts.append(lines[i])

    elif "torihada" in host:
        name = title.split("｜")[0].strip()
        shifts = parse_torihada_schedule(lines)

    elif "exe-mensspa" in host or "theratopia" in host:
        for i in range(len(lines) - 2):
            if re.match(r"\d{2}/\d{2}", lines[i]) and "(" in lines[i + 1] and is_time(lines[i + 2]):
                shifts.append(lines[i] + lines[i + 1])

        for i, line in enumerate(lines):
            if line in ["Photo.3", "Photo3"] and i + 1 < len(lines):
                name = lines[i + 1]

    elif "kuraimax" in host:
        for i in range(len(lines) - 1):
            m = re.match(r"(\d{2})月(\d{2})日(\(.+\))", lines[i])
            if m and is_time(lines[i + 1]):
                shifts.append(f"{m.group(1)}/{m.group(2)}{m.group(3)}")

        for i, line in enumerate(lines):
            if line == "Name" and i + 1 < len(lines):
                name = lines[i + 1]

    elif "felicia" in host:
        for line in lines:
            if "桃瀬ゆいか" in line:
                name = "桃瀬ゆいか"
                break

    elif "haniel" in host:
        for i in range(len(lines) - 4):
            if re.match(r"\d{2}/\d{2}\(.+\)", lines[i]):
                if lines[i + 1] != "--":
                    shifts.append(lines[i])

    elif "c-moon" in host:
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


def build_message(results):
    lines = []
    lines.append("出勤確認結果")
    lines.append("")

    for item in results:
        name = item["name"] if item["name"] else "取得失敗"
        shifts_text = "、".join(item["shifts"]) if item["shifts"] else "出勤予定なし"
        lines.append(f"名前：{name}")
        lines.append(f"出勤：{shifts_text}")
        lines.append("")

    message = "\n".join(lines).strip()

    if len(message) > 4900:
        message = message[:4900]

    return message


def send_line_message(message):
    if not LINE_CHANNEL_ACCESS_TOKEN:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN が未設定です")
    if not LINE_USER_ID:
        raise RuntimeError("LINE_USER_ID が未設定です")

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


results = []

for url in URLS:
    try:
        name, shifts = parse(url)

        print("URL:", url)
        print(" -> 名前:", name if name else "取得失敗")
        print(" -> 出勤:", ", ".join(shifts) if shifts else "出勤予定なし")
        print("")

        results.append({
            "url": url,
            "name": name,
            "shifts": shifts
        })

    except Exception as e:
        print("URL:", url)
        print(" -> エラー:", e)
        print("")

        results.append({
            "url": url,
            "name": "取得失敗",
            "shifts": [f"取得エラー: {e}"]
        })

message = build_message(results)

print("LINE送信メッセージ:")
print(message)
print("")

try:
    send_line_message(message)
    print("LINE送信成功")
except Exception as e:
    print("LINE送信エラー:", e)
    raise
