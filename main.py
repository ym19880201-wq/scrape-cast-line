import re
import time
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from common import send_line_message
from sites import carina
from sites import churitos
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


TIMEOUT = 20

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


TARGETS = [
    {
        "shop": "エグゼ",
        "url": "https://exe-mensspa.nagoya/profile.html?sid=32",
        "parser": exe,
        "fallback_name": "",
    },
    {
        "shop": "チュリトス",
        "url": "https://churitos01.com/profile?lid=148",
        "parser": churitos,
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
        return {
            "shop": normalize_text(str(parsed.get("shop", "") or shop)),
            "url": normalize_text(str(parsed.get("url", "") or url)),
            "name": normalize_text(str(parsed.get("name", "") or fallback_name)),
            "shifts": ensure_shifts_list(parsed.get("shifts", [])),
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
                return {
                    "shop": normalize_text(str(only.get("shop", "") or shop)),
                    "url": normalize_text(str(only.get("url", "") or url)),
                    "name": normalize_text(str(only.get("name", "") or fallback_name)),
                    "shifts": ensure_shifts_list(only.get("shifts", [])),
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

    if len(message) > 4900:
        message = message[:4900]

    return message


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
    print("[MAIN] メッセージ作成")
    message = build_message(results)
    print(message)
    print("=" * 80)

    try:
        send_line_message(message)
        print("[MAIN] LINE送信成功")
    except Exception as e:
        print(f"[MAIN] LINE送信エラー: {e}")
        raise


if __name__ == "__main__":
    main()
