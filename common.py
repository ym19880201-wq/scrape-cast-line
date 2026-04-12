import re
import requests
from bs4 import BeautifulSoup


LINE_CHANNEL_ACCESS_TOKEN = "H7jR4YDmRg5KF7sYDHByQ0FFMHd5YO/i0tuDfY7AcHXejpZQomTZ+9h0qE8Fghx6kXTwD9CnDx5T2U8EKoIxpBDFzef/eMIoIy//ZN4kSdtHtQS0KTPmcjN2CzkNLnnFcmGZaUSzd/zAjNsx3wdjLgdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U01a41d2bfd8d61e7b708b48aa5056738"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}


def normalize_text(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("\u3000", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def clean_name(text):
    text = normalize_text(text)

    text = re.sub(r"\s*\(\d+\)\s*$", "", text)
    text = re.sub(r"\s*（\d+）\s*$", "", text)
    text = re.sub(r"\s*\d+\s*歳\s*$", "", text)
    text = re.sub(r"\s*T\d+.*$", "", text)
    text = re.sub(r"\s*身長.*$", "", text)
    text = re.sub(r"\s*年齢[:：].*$", "", text)
    text = re.sub(r"\s*プロフィール.*$", "", text)
    text = re.sub(r"\s*のプロフィール.*$", "", text)
    text = re.sub(r"\s*の$", "", text)

    text = text.strip(" 　|｜/:：・")
    text = re.sub(r"^[^ぁ-んァ-ヶ一-龠A-Za-z0-9]+", "", text)
    text = re.sub(r"[^ぁ-んァ-ヶ一-龠A-Za-z0-9]+$", "", text)

    return normalize_text(text)


def dedupe_keep_order(items):
    return list(dict.fromkeys(items))


def fetch(url, timeout=20, verify=True):
    res = requests.get(url, headers=HEADERS, timeout=timeout, verify=verify)
    res.raise_for_status()

    if not res.encoding or res.encoding.lower() == "iso-8859-1":
        res.encoding = res.apparent_encoding or "utf-8"

    soup = BeautifulSoup(res.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [normalize_text(l) for l in text.splitlines() if normalize_text(l)]
    title = soup.title.get_text() if soup.title else ""
    return title, lines


def fetch_html(url, timeout=20, verify=True):
    res = requests.get(url, headers=HEADERS, timeout=timeout, verify=verify)
    res.raise_for_status()

    if not res.encoding or res.encoding.lower() == "iso-8859-1":
        res.encoding = res.apparent_encoding or "utf-8"

    return res.text


def get_soup(url, timeout=20, verify=True):
    html = fetch_html(url, timeout=timeout, verify=verify)
    return BeautifulSoup(html, "html.parser")


def build_lines_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    return [normalize_text(l) for l in text.splitlines() if normalize_text(l)]


def build_lines_from_soup(soup):
    text = soup.get_text("\n", strip=True)
    return [normalize_text(l) for l in text.splitlines() if normalize_text(l)]


def is_time(s):
    s = normalize_text(s)
    return bool(re.search(r"\d{1,2}:\d{2}", s))


def is_off(text):
    text = normalize_text(text)
    return text in ["", "-", "--", "---", "休み", "お休み", "未定", "×", "✕", "✖"]


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


def ensure_shifts_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        result = [normalize_text(str(x)) for x in value if normalize_text(str(x))]
        return dedupe_keep_order(result)

    if isinstance(value, tuple):
        result = [normalize_text(str(x)) for x in value if normalize_text(str(x))]
        return dedupe_keep_order(result)

    text = normalize_text(str(value))
    if not text:
        return []

    if "、" in text:
        result = [normalize_text(x) for x in text.split("、") if normalize_text(x)]
        return dedupe_keep_order(result)

    return [text]


def build_message(results):
    lines = []
    lines.append("出勤確認結果")
    lines.append("")

    for item in results:
        shop = normalize_text(str(item.get("shop", "")))
        name = normalize_text(str(item.get("name", ""))) or "取得失敗"
        shifts = ensure_shifts_list(item.get("shifts", []))
        shifts_text = "、".join(shifts) if shifts else "出勤予定なし"

        lines.append(f"店名：{shop}")
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
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message,
            }
        ],
    }

    res = requests.post(url, headers=headers, json=payload, timeout=20)
    res.raise_for_status()
    return res
