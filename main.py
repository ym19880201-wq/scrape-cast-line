import os
import random
import re
import smtplib
import ssl
import time
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from common import send_line_message
from build_blog_html import build_blog_html
from build_blog_schedule import build_blog_schedule
from sites import babydoll
from sites import carina
from sites import cmoon
from sites import exe
from sites import felicia
from sites import galaxy
from sites import haniel
from sites import hosifuluspa
from sites import kuraimax
from sites import resexy
from sites import theratopia
from sites import torihada
from sites import white


TIMEOUT = 20
LINE_SAFE_LIMIT = 4300
GMAIL_ADDRESS = "ym19880201@gmail.com"
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465

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

JST = timezone(timedelta(hours=9))
WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]

TITLE_COLOR_PATTERNS = [
    {
        "background": "linear-gradient(180deg, #45bf88 0%, #2e9f6d 100%)",
        "border": "#22885c",
        "text": "#ffffff",
        "bracket": "#e9fff4",
        "shadow": "0 1px 0 rgba(0,0,0,0.12), 0 2px 4px rgba(0,0,0,0.18)",
        "inset": "0 2px 0 rgba(255,255,255,0.22) inset, 0 5px 12px rgba(0,0,0,0.12)",
    },
    {
        "background": "linear-gradient(180deg, #35c99a 0%, #239d76 100%)",
        "border": "#1d8563",
        "text": "#ffffff",
        "bracket": "#ebfff8",
        "shadow": "0 1px 0 rgba(0,0,0,0.12), 0 2px 4px rgba(0,0,0,0.18)",
        "inset": "0 2px 0 rgba(255,255,255,0.22) inset, 0 5px 12px rgba(0,0,0,0.12)",
    },
    {
        "background": "linear-gradient(180deg, #4d78c9 0%, #355ca8 100%)",
        "border": "#284a89",
        "text": "#ffffff",
        "bracket": "#eef4ff",
        "shadow": "0 1px 0 rgba(0,0,0,0.14), 0 2px 4px rgba(0,0,0,0.20)",
        "inset": "0 2px 0 rgba(255,255,255,0.20) inset, 0 5px 12px rgba(0,0,0,0.12)",
    },
    {
        "background": "linear-gradient(180deg, #b54c70 0%, #903453 100%)",
        "border": "#7c2945",
        "text": "#ffffff",
        "bracket": "#fff0f5",
        "shadow": "0 1px 0 rgba(0,0,0,0.14), 0 2px 4px rgba(0,0,0,0.20)",
        "inset": "0 2px 0 rgba(255,255,255,0.18) inset, 0 5px 12px rgba(0,0,0,0.12)",
    },
    {
        "background": "linear-gradient(180deg, #8a67d4 0%, #6b49b8 100%)",
        "border": "#57369d",
        "text": "#ffffff",
        "bracket": "#f3edff",
        "shadow": "0 1px 0 rgba(0,0,0,0.14), 0 2px 4px rgba(0,0,0,0.20)",
        "inset": "0 2px 0 rgba(255,255,255,0.20) inset, 0 5px 12px rgba(0,0,0,0.12)",
    },
    {
        "background": "linear-gradient(180deg, #e58a47 0%, #c96728 100%)",
        "border": "#ab531a",
        "text": "#ffffff",
        "bracket": "#fff3e9",
        "shadow": "0 1px 0 rgba(0,0,0,0.14), 0 2px 4px rgba(0,0,0,0.20)",
        "inset": "0 2px 0 rgba(255,255,255,0.18) inset, 0 5px 12px rgba(0,0,0,0.12)",
    },
]

TARGETS = [
    {
        "shop": "エグゼ",
        "url": "https://exe-mensspa.nagoya/profile.html?sid=32",
        "parser": exe,
        "fallback_name": "",
    },
    {
        "shop": "クライマックス東岡崎",
        "url": "https://kuraimaxmax.com/profile.php?sid=399",
        "parser": kuraimax,
        "fallback_name": "",
    },
    {
        "shop": "ほしふるスパ",
        "url": "https://hosifuluspa.com/cast/%e3%81%82%e3%82%84%e3%81%ae/",
        "parser": hosifuluspa,
        "fallback_name": "",
    },
    {
        "shop": "トリハダスパ",
        "url": "https://torihada-spa.men-es.jp/profile.html?sid=266",
        "parser": torihada,
        "fallback_name": "",
    },
    {
        "shop": "フェリシア",
        "url": "https://felicia-garden.com/profile.php?sid=210",
        "parser": felicia,
        "fallback_name": "",
    },
    {
        "shop": "ギャラクシー",
        "url": "https://galaxy-nagoya.com/cast/%E3%82%86%E3%82%8A",
        "parser": galaxy,
        "fallback_name": "",
    },
    {
        "shop": "ギャラクシー",
        "url": "https://galaxy-nagoya.com/cast/%E3%82%8C%E3%81%84",
        "parser": galaxy,
        "fallback_name": "",
    },
    {
        "shop": "ギャラクシー",
        "url": "https://galaxy-nagoya.com/cast/%E3%81%8F%E3%82%8B%E3%81%BF",
        "parser": galaxy,
        "fallback_name": "",
    },
    {
        "shop": "ベビードール",
        "url": "https://babydoll-nagoya.com/profile/?id=18",
        "parser": babydoll,
        "fallback_name": "",
    },
    {
        "shop": "セラトピア",
        "url": "https://esthe-theratopia.net/profile.html?sid=176",
        "parser": theratopia,
        "fallback_name": "",
    },
    {
        "shop": "トリハダスパ",
        "url": "https://torihada-spa.men-es.jp/profile.html?sid=305",
        "parser": torihada,
        "fallback_name": "",
    },
    {
        "shop": "ハニエル",
        "url": "https://haniel-nagoya.net/profile.html?5082",
        "parser": haniel,
        "fallback_name": "",
    },
    {
        "shop": "C-MOON",
        "url": "https://www.c-moon.info/profile/_uid/10617/",
        "parser": cmoon,
        "fallback_name": "",
    },
    {
        "shop": "リゼクシー",
        "url": "https://resexy.info/profile.php?sid=2437",
        "parser": resexy,
        "fallback_name": "",
    },
    {
        "shop": "カリーナ",
        "url": "https://carina-esthe.com/profile.php?sid=22044#contents",
        "parser": carina,
        "fallback_name": "",
    },
    {
        "shop": "メンズエステWhite",
        "url": "https://esthe-nagoya.com/profile.html?2203",
        "parser": white,
        "fallback_name": "",
    },
]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u3000", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def dedupe_keep_order(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))


def ensure_shifts_list(value: Any) -> List[str]:
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

    if "," in text:
        result = [normalize_text(x) for x in text.split(",") if normalize_text(x)]
        return dedupe_keep_order(result)

    return [text]


def build_lines_from_soup(soup: BeautifulSoup) -> List[str]:
    text = soup.get_text("\n", strip=True)
    lines: List[str] = []

    for raw in text.splitlines():
        line = normalize_text(raw)
        if line:
            lines.append(line)

    return lines


def fetch_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()

    if not response.encoding or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or "utf-8"

    return BeautifulSoup(response.text, "html.parser")


def parse_existing_site(parser: Any, url: str) -> Any:
    return parser.parse(url)


def parse_new_site(
    parser: Any,
    url: str,
    soup: BeautifulSoup,
    lines: List[str],
    fallback_name: str,
) -> Any:
    return parser.parse(url, soup, lines, fallback_name=fallback_name)


def normalize_parsed_result(
    parsed: Any,
    shop: str,
    url: str,
    fallback_name: str,
) -> Dict[str, Any]:
    if isinstance(parsed, dict):
        shifts_value = parsed.get("shifts", None)

        if shifts_value is None:
            shifts_value = parsed.get("schedule", [])

        return {
            "shop": normalize_text(str(parsed.get("shop", "") or shop)),
            "url": normalize_text(str(parsed.get("url", "") or url)),
            "name": normalize_text(str(parsed.get("name", "") or fallback_name)),
            "shifts": ensure_shifts_list(shifts_value),
        }

    if isinstance(parsed, (list, tuple)):
        items = list(parsed)

        if len(items) >= 3:
            return {
                "shop": normalize_text(str(items[0] or shop)),
                "url": normalize_text(url),
                "name": normalize_text(str(items[1] or fallback_name)),
                "shifts": ensure_shifts_list(items[2]),
            }

        if len(items) == 2:
            return {
                "shop": normalize_text(shop),
                "url": normalize_text(url),
                "name": normalize_text(str(items[0] or fallback_name)),
                "shifts": ensure_shifts_list(items[1]),
            }

        if len(items) == 1:
            only = items[0]
            if isinstance(only, dict):
                shifts_value = only.get("shifts", None)

                if shifts_value is None:
                    shifts_value = only.get("schedule", [])

                return {
                    "shop": normalize_text(str(only.get("shop", "") or shop)),
                    "url": normalize_text(str(only.get("url", "") or url)),
                    "name": normalize_text(str(only.get("name", "") or fallback_name)),
                    "shifts": ensure_shifts_list(shifts_value),
                }
            return {
                "shop": normalize_text(shop),
                "url": normalize_text(url),
                "name": normalize_text(str(only or fallback_name)),
                "shifts": [],
            }

    text = normalize_text(str(parsed))

    return {
        "shop": normalize_text(shop),
        "url": normalize_text(url),
        "name": normalize_text(fallback_name),
        "shifts": [text] if text else [],
    }


def build_weekly_blog_title() -> str:
    today_jst = datetime.now(JST).date()
    monday = today_jst - timedelta(days=today_jst.weekday())
    sunday = monday + timedelta(days=6)

    start_text = f"{monday.month}/{monday.day}({WEEKDAY_JA[monday.weekday()]})"
    end_text = f"{sunday.month}/{sunday.day}({WEEKDAY_JA[sunday.weekday()]})"

    return f"【{start_text}～{end_text} HRセラピ出勤予定】"


def build_weekly_blog_subject() -> str:
    return build_weekly_blog_title()


def choose_title_color_pattern() -> Dict[str, str]:
    return random.choice(TITLE_COLOR_PATTERNS)


def build_blog_title_html() -> str:
    title = build_weekly_blog_title()
    pattern = choose_title_color_pattern()

    inner_title = title
    if title.startswith("【") and title.endswith("】"):
        inner_title = title[1:-1]

    return (
        '<div style="text-align:center; font-size:22px; font-weight:bold; '
        'line-height:1.4; margin:0 0 18px 0; padding:12px 8px; '
        f'background:{pattern["background"]}; '
        f'border-top:4px solid {pattern["border"]}; '
        f'border-bottom:4px solid {pattern["border"]}; '
        'border-radius:9px; '
        f'color:{pattern["text"]}; '
        f'box-shadow:{pattern["inset"]}; '
        f'text-shadow:{pattern["shadow"]}; '
        'white-space:nowrap;">'
        f'<span style="font-size:26px; color:{pattern["bracket"]};">【</span>'
        f"{inner_title}"
        f'<span style="font-size:26px; color:{pattern["bracket"]};">】</span>'
        "</div>"
    )


def build_blog_spacer_html() -> str:
    return '<div style="height: 18px;"></div>'


def trim_message(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def get_gmail_app_password() -> str:
    password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if not password:
        raise RuntimeError(
            "GMAIL_APP_PASSWORD が設定されていません。"
            " 実行前に環境変数 GMAIL_APP_PASSWORD に Gmail のアプリパスワードを設定してください。"
        )
    return password


def send_gmail_code(subject: str, body_text: str) -> None:
    app_password = get_gmail_app_password()

    message = MIMEText(body_text, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = GMAIL_ADDRESS

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, context=context) as server:
        server.login(GMAIL_ADDRESS, app_password)
        server.sendmail(GMAIL_ADDRESS, [GMAIL_ADDRESS], message.as_string())


def scrape_target(target: Dict[str, Any]) -> Dict[str, Any]:
    shop = target["shop"]
    url = target["url"]
    parser = target["parser"]
    fallback_name = target.get("fallback_name", "")

    print("")
    print("#" * 80)
    print(f"[START] shop={shop}")
    print(f"[START] url={url}")
    print("=" * 80)

    if parser in [resexy, carina]:
        soup = fetch_soup(url)
        lines = build_lines_from_soup(soup)
        parsed = parse_new_site(parser, url, soup, lines, fallback_name)
    else:
        parsed = parse_existing_site(parser, url)

    return normalize_parsed_result(parsed, shop, url, fallback_name)


def build_message(results: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
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
    return trim_message(message, LINE_SAFE_LIMIT)


def build_blog_message(results: List[Dict[str, Any]]) -> str:
    raw_items: List[Dict[str, Any]] = []

    for item in results:
        shop = normalize_text(str(item.get("shop", "")))
        name = normalize_text(str(item.get("name", "")))
        shifts = ensure_shifts_list(item.get("shifts", []))

        valid_shifts = []
        for shift in shifts:
            shift_text = normalize_text(shift)
            if not shift_text:
                continue
            if shift_text == "出勤予定なし":
                continue
            if shift_text.startswith("取得エラー:"):
                continue
            valid_shifts.append(shift_text)

        if not shop or not name or not valid_shifts:
            continue

        raw_items.append(
            {
                "shop_name": shop,
                "cast_name": name,
                "dates": valid_shifts,
            }
        )

    schedule_items = build_blog_schedule(raw_items)
    title_html = build_blog_title_html()
    spacer_html = build_blog_spacer_html()

    if not schedule_items:
        return title_html + "\n" + spacer_html + "\n" + "投稿対象データがありません。"

    html = build_blog_html(schedule_items)
    return title_html + "\n" + spacer_html + "\n" + html


def main() -> None:
    print("[MAIN] 開始")
    print(f"[MAIN] targets={len(TARGETS)}")

    results: List[Dict[str, Any]] = []

    for index, target in enumerate(TARGETS, start=1):
        print("")
        print(f"[MAIN] {index}/{len(TARGETS)} 処理中")

        try:
            result = scrape_target(target)

            print(f"[OK] {result['shop']}")
            print(f" -> 名前: {result['name'] if result['name'] else '取得失敗'}")
            print(f" -> 出勤: {', '.join(result['shifts']) if result['shifts'] else '出勤予定なし'}")

            results.append(result)

        except Exception as e:
            print(f"[ERROR] {target['shop']}")
            print(f" -> {e}")

            results.append(
                {
                    "shop": target["shop"],
                    "url": target["url"],
                    "name": "取得失敗",
                    "shifts": [f"取得エラー: {e}"],
                }
            )

        time.sleep(1)

    print("")
    print("=" * 80)
    print("[MAIN] 1通目メッセージ作成")
    message = build_message(results)
    print(message)
    print("=" * 80)

    try:
        send_line_message(message)
        print("[MAIN] 1通目LINE送信成功")
    except Exception as e:
        print(f"[MAIN] 1通目LINE送信エラー: {e}")
        raise

    print("")
    print("=" * 80)
    print("[MAIN] 2通目Gmailコード作成")
    blog_message = build_blog_message(results)
    blog_subject = build_weekly_blog_subject()
    print(blog_subject)
    print(blog_message)
    print("=" * 80)

    try:
        send_gmail_code(blog_subject, blog_message)
        print("[MAIN] 2通目Gmail送信成功")
    except Exception as e:
        print(f"[MAIN] 2通目Gmail送信エラー: {e}")
        raise


if __name__ == "__main__":
    main()
