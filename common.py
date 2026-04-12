import re
import time
import unicodedata

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


LINE_USER_ID = "U01a41d2bfd8d61e7b708b48aa5056738"
LINE_CHANNEL_ACCESS_TOKEN = "H7jR4YDmRg5KF7sYDHByQ0FFMHd5YO/i0tuDfY7AcHXejpZQomTZ+9h0qE8Fghx6kXTwD9CnDx5T2U8EKoIxpBDFzef/eMIoIy//ZN4kSdtHtQS0KTPmcjN2CzkNLnnFcmGZaUSzd/zAjNsx3wdjLgdB04t89/1O/w1cDnyilFU="

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}

CONNECT_TIMEOUT = 20
READ_TIMEOUT = 40
REQUEST_TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

RETRY_TOTAL = 3
RETRY_BACKOFF = 2.0


def normalize_text(text):
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u3000", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def clean_name(text):
    text = normalize_text(text)

    text = re.sub(r"\s*のプロフィール.*$", "", text)
    text = re.sub(r"\s*プロフィール.*$", "", text)

    text = text.split("|")[0].strip()
    text = text.split("｜")[0].strip()
    text = text.split("/")[0].strip()

    remove_words = [
        "名古屋メンズエステ〜TORIHADA SPA〜",
        "名古屋メンズエステ TORIHADA SPA",
        "TORIHADA SPA",
        "名古屋 メンズエステ | EXE～エグゼ",
        "名古屋 メンズエステ EXE～エグゼ",
        "メンズエステ",
    ]
    for word in remove_words:
        text = text.replace(word, "")

    text = re.sub(r"\s*\(.*?\)\s*$", "", text)
    text = re.sub(r"[ 　]+", " ", text).strip()

    text = re.sub(r"^[^0-9A-Za-zぁ-んァ-ヶ一-龠々ー]+", "", text)
    text = re.sub(r"[^0-9A-Za-zぁ-んァ-ヶ一-龠々ー%❤️]+$", "", text)

    text = re.sub(r"[⚜️☆★◆◇●○◎◉◯□■△▲▽▼♡♥❤]+", "", text)
    text = re.sub(r"[ 　]+", " ", text).strip()

    if re.fullmatch(r".+\s+の", text):
        text = re.sub(r"\s+の$", "", text).strip()

    if re.fullmatch(r".+の", text) and len(text) <= 8:
        text = re.sub(r"の$", "", text).strip()

    return text.strip()


def dedupe_keep_order(items):
    return list(dict.fromkeys(items))


def is_time(text):
    text = normalize_text(text)
    return bool(re.search(r"\d{1,2}:\d{2}", text))


def build_session():
    session = requests.Session()

    retry = Retry(
        total=RETRY_TOTAL,
        connect=RETRY_TOTAL,
        read=RETRY_TOTAL,
        status=RETRY_TOTAL,
        backoff_factor=RETRY_BACKOFF,
        allowed_methods=frozenset(["GET", "HEAD", "POST"]),
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)

    return session


def fetch_response(url, headers=None, timeout=REQUEST_TIMEOUT):
    session = build_session()
    request_headers = dict(DEFAULT_HEADERS)

    if headers:
        request_headers.update(headers)

    last_error = None

    for attempt in range(1, RETRY_TOTAL + 2):
        try:
            response = session.get(url, headers=request_headers, timeout=timeout)
            response.raise_for_status()

            if not response.encoding or response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding or "utf-8"

            return response

        except requests.exceptions.RequestException as e:
            last_error = e

            if attempt >= RETRY_TOTAL + 1:
                break

            time.sleep(RETRY_BACKOFF * attempt)

    raise last_error


def fetch_html(url, headers=None, timeout=REQUEST_TIMEOUT):
    response = fetch_response(url, headers=headers, timeout=timeout)
    return response.text


def fetch(url, headers=None, timeout=REQUEST_TIMEOUT):
    html = fetch_html(url, headers=headers, timeout=timeout)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [normalize_text(line) for line in text.splitlines() if normalize_text(line)]
    title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    return title, lines


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
        line = normalize_text(lines[idx])
        if line in ["休み", "未定"] or re.fullmatch(r"\d{1,2}:\d{2}\s*[～〜~\-]\s*\d{1,2}:\d{2}", line):
            statuses.append(line)
        idx += 1

    count = min(len(dates), len(statuses))

    for i in range(count):
        if statuses[i] not in ["休み", "未定"]:
            shifts.append(dates[i])

    return dedupe_keep_order(shifts)


def build_message(results):
    lines = []
    lines.append("出勤確認結果")
    lines.append("")

    for item in results:
        if not isinstance(item, dict):
            continue

        shop = normalize_text(item.get("shop", ""))
        name = normalize_text(item.get("name", ""))
        shifts = item.get("shifts", [])

        if isinstance(shifts, str):
            shifts_list = [normalize_text(shifts)] if normalize_text(shifts) else []
        else:
            shifts_list = [normalize_text(x) for x in shifts if normalize_text(x)]

        if shop:
            lines.append(f"店名：{shop}")

        lines.append(f"名前：{name if name else '取得失敗'}")
        lines.append(f"出勤：{'、'.join(shifts_list) if shifts_list else '出勤予定なし'}")
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

    response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response
