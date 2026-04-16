from collections import OrderedDict
from datetime import datetime

from post_items import get_post_item_map


def weekday_jp(dt):
    names = ["月", "火", "水", "木", "金", "土", "日"]
    return names[dt.weekday()]


def format_date_label(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.month}/{dt.day}({weekday_jp(dt)})"


def get_day_style(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday()

    styles = {
        0: {
            "border": "#bfe8ff",
            "bg": "#f8fdff",
            "header": "#dff4ff",
        },
        1: {
            "border": "#f6cbfc",
            "bg": "#fffafc",
            "header": "#fdeefe",
        },
        2: {
            "border": "#bff0df",
            "bg": "#f8fffb",
            "header": "#dcf9ef",
        },
        3: {
            "border": "#ffe6a7",
            "bg": "#fffef8",
            "header": "#fff3c9",
        },
        4: {
            "border": "#d8ccff",
            "bg": "#fcfbff",
            "header": "#ede8ff",
        },
        5: {
            "border": "#ffd3a8",
            "bg": "#fffaf7",
            "header": "#ffe6d1",
        },
        6: {
            "border": "#ffbcbc",
            "bg": "#fff9f9",
            "header": "#ffe0e0",
        },
    }
    return styles[weekday]


def escape_html(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_link_line(title, url, is_last):
    safe_title = escape_html(title)
    safe_url = escape_html(url)

    margin_style = "margin: 0;" if is_last else "margin: 0 0 8px 0;"

    return (
        f'    <p style="{margin_style} font-size: 16px; line-height: 1.8;">\n'
        f'      ・<a href="{safe_url}" style="text-decoration: none;">{safe_title}</a>\n'
        f"    </p>"
    )


def build_day_block(date_str, items):
    date_label = format_date_label(date_str)
    style = get_day_style(date_str)

    lines = []
    lines.append(
        f'<div style="margin: 0 0 18px 0; border: 2px solid {style["border"]}; '
        f'border-radius: 8px; background-color: {style["bg"]}; overflow: hidden;">'
    )
    lines.append(
        f'  <p style="margin: 0; padding: 10px 14px; font-size: 22px; font-weight: bold; '
        f'color: #333; background-color: {style["header"]};">'
    )
    lines.append(f"    {escape_html(date_label)}")
    lines.append("  </p>")
    lines.append('  <div style="padding: 12px 14px;">')

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        lines.append(build_link_line(item["title"], item["url"], is_last))

    lines.append("  </div>")
    lines.append("</div>")
    return "\n".join(lines)


def group_items_by_date(post_items):
    grouped = OrderedDict()

    for item in sorted(post_items, key=lambda x: x["date"]):
        date_str = item["date"]
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(item)

    return grouped


def build_full_html(post_items):
    if not post_items:
        return ""

    grouped = group_items_by_date(post_items)
    blocks = []

    for date_str, items in grouped.items():
        blocks.append(build_day_block(date_str, items))

    return "\n\n".join(blocks)


def build_post_items_from_schedule(schedule_items, post_item_map):
    result = []

    for schedule_item in schedule_items:
        shop_name = schedule_item["shop_name"]
        cast_name = schedule_item["cast_name"]
        date_list = schedule_item["dates"]

        key = (shop_name, cast_name)

        if key not in post_item_map:
            print(f"投稿設定なし: {shop_name} / {cast_name}")
            continue

        post_setting = post_item_map[key]

        for date_str in date_list:
            result.append(
                {
                    "date": date_str,
                    "title": post_setting["title"],
                    "url": post_setting["url"],
                }
            )

    return result


def build_blog_html(schedule_items):
    post_item_map = get_post_item_map()
    post_items = build_post_items_from_schedule(schedule_items, post_item_map)
    return build_full_html(post_items)


def main():
    schedule_items = [
        {
            "shop_name": "エグゼ",
            "cast_name": "のあ",
            "dates": ["2026-04-21", "2026-04-22"],
        },
    ]

    html = build_blog_html(schedule_items)

    print("====== ここから記事投稿サイトに貼るHTML ======")
    print()

    if html:
        print(html)
    else:
        print("投稿対象データがありません。")

    print()
    print("====== ここまで ======")


if __name__ == "__main__":
    main()
