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
        0: {"border": "#bfe8ff", "bg": "#ffffff", "header": "#dff4ff"},
        1: {"border": "#f6cbfc", "bg": "#ffffff", "header": "#fdeefe"},
        2: {"border": "#bff0df", "bg": "#ffffff", "header": "#dcf9ef"},
        3: {"border": "#ffe6a7", "bg": "#ffffff", "header": "#fff3c9"},
        4: {"border": "#d8ccff", "bg": "#ffffff", "header": "#ede8ff"},
        5: {"border": "#ffd3a8", "bg": "#ffffff", "header": "#ffe6d1"},
        6: {"border": "#ffbcbc", "bg": "#ffffff", "header": "#ffe0e0"},
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


def detect_article_type(title):
    text = str(title)

    if "GHR" in text:
        return "GHR"
    if "NS" in text:
        return "NS"
    if "NN" in text:
        return "NN"

    return "OTHER"


def get_article_priority(article_type):
    priority = {
        "GHR": 1,
        "NS": 2,
        "NN": 3,
        "OTHER": 99,
    }
    return priority.get(article_type, 99)


def build_type_tag(article_type):
    if article_type == "GHR":
        return (
            '<span style="display:inline-block; width:38px; margin-right:8px; '
            'text-align:center; color:#0066cc; background:#eaf4ff; '
            'border:1px solid #9dccff; font-size:11px; font-weight:bold; '
            'border-radius:3px; line-height:1.6;">GHR</span>'
        )

    if article_type == "NS":
        return (
            '<span style="display:inline-block; width:38px; margin-right:8px; '
            'text-align:center; color:#9a7600; background:#fff7cc; '
            'border:1px solid #ead36a; font-size:11px; font-weight:bold; '
            'border-radius:3px; line-height:1.6;">NS</span>'
        )

    if article_type == "NN":
        return (
            '<span style="display:inline-block; width:38px; margin-right:8px; '
            'text-align:center; color:#cc1f1f; background:#ffecec; '
            'border:1px solid #f1a0a0; font-size:11px; font-weight:bold; '
            'border-radius:3px; line-height:1.6;">NN</span>'
        )

    return (
        '<span style="display:inline-block; width:38px; margin-right:8px; '
        'text-align:center; color:#777; background:#f5f5f5; '
        'border:1px solid #dddddd; font-size:11px; font-weight:bold; '
        'border-radius:3px; line-height:1.6;">他</span>'
    )


def build_notice_html():
    return (
        '<p style="margin:0 0 18px 0; font-size:14px; line-height:1.8; color:#333;">'
        '全て無課金での'
        '<span style="font-size:14pt; font-weight:bold;">体験談</span>'
        'です。'
        '</p>'
    )


def split_title_for_two_lines(title):
    parts = [part.strip() for part in str(title).split("　") if part.strip()]

    if len(parts) >= 2:
        first_line = parts[0]
        second_line = "　".join(parts[1:])
        return first_line, second_line

    return str(title), ""


def build_link_line(title, url, article_type, is_last):
    first_line, second_line = split_title_for_two_lines(title)

    safe_first_line = escape_html(first_line)
    safe_second_line = escape_html(second_line)
    safe_url = escape_html(url)
    tag_html = build_type_tag(article_type)

    border_style = "" if is_last else " border-bottom:1px solid #eeeeee;"

    title_link_html = (
        f'<a href="{safe_url}" style="text-decoration:none; color:#222; font-weight:bold;">'
        f"{safe_first_line}"
        f"</a>"
    )

    if safe_second_line:
        second_line_html = (
            f'<a href="{safe_url}" style="text-decoration:none; color:#333; font-weight:normal;">'
            f"{safe_second_line}"
            f"</a>"
        )

        return (
            f'    <div style="margin:0; padding:10px 0;{border_style}">\n'
            f'      <div style="display:flex; align-items:center; font-size:15px; '
            f'line-height:1.55; font-weight:bold;">\n'
            f"        {tag_html}"
            f"        <span>{title_link_html}</span>\n"
            f"      </div>\n"
            f'      <div style="margin:3px 0 0 46px; font-size:14px; '
            f'line-height:1.65; color:#333; font-weight:normal;">\n'
            f"        {second_line_html}\n"
            f"      </div>\n"
            f"    </div>"
        )

    return (
        f'    <div style="margin:0; padding:10px 0;{border_style}">\n'
        f'      <div style="display:flex; align-items:center; font-size:15px; '
        f'line-height:1.55; font-weight:bold;">\n'
        f"        {tag_html}"
        f"        <span>{title_link_html}</span>\n"
        f"      </div>\n"
        f"    </div>"
    )


def build_day_block(date_str, items):
    date_label = format_date_label(date_str)
    style = get_day_style(date_str)

    sorted_items = sorted(
        items,
        key=lambda x: (
            get_article_priority(x.get("article_type", "OTHER")),
            x.get("title", ""),
        ),
    )

    lines = []

    lines.append(
        f'<div style="margin:0 0 18px 0; border:2px solid {style["border"]}; '
        f'border-radius:8px; background-color:{style["bg"]}; overflow:hidden;">'
    )

    lines.append(
        f'  <p style="margin:0; padding:10px 14px; font-size:22px; '
        f'font-weight:bold; color:#333; background-color:{style["header"]};">'
    )

    lines.append(f"    {escape_html(date_label)}")
    lines.append("  </p>")
    lines.append('  <div style="padding:8px 14px; background:#ffffff;">')

    for i, item in enumerate(sorted_items):
        is_last = i == len(sorted_items) - 1
        lines.append(
            build_link_line(
                item["title"],
                item["url"],
                item.get("article_type", "OTHER"),
                is_last,
            )
        )

    lines.append("  </div>")
    lines.append("</div>")

    return "\n".join(lines)


def group_items_by_date(post_items):
    grouped = OrderedDict()

    for item in sorted(
        post_items,
        key=lambda x: (
            x["date"],
            get_article_priority(x.get("article_type", "OTHER")),
            x.get("title", ""),
        ),
    ):
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

    return '\n\n<div style="height:18px;"></div>\n\n'.join(blocks)


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
        title = post_setting["title"]
        article_type = detect_article_type(title)

        for date_str in date_list:
            result.append(
                {
                    "date": date_str,
                    "title": title,
                    "url": post_setting["url"],
                    "article_type": article_type,
                }
            )

    return result


def build_blog_html(schedule_items):
    post_item_map = get_post_item_map()
    post_items = build_post_items_from_schedule(schedule_items, post_item_map)
    html = build_full_html(post_items)

    if not html:
        return ""

    return build_notice_html() + "\n\n" + html
