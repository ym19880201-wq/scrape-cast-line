from datetime import datetime
import re


def parse_date_to_iso(text, default_year=None):
    if text is None:
        return None

    value = str(text).strip()
    if not value:
        return None

    if default_year is None:
        default_year = datetime.now().year

    value = value.replace("（", "(").replace("）", ")")
    value = re.sub(r"\s+", "", value)

    match_with_time = re.search(r"(\d{1,2})[/-](\d{1,2})(?:\([月火水木金土日]\))?", value)
    if match_with_time:
        month = int(match_with_time.group(1))
        day = int(match_with_time.group(2))
        try:
            dt = datetime(default_year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    value = re.sub(r"\([月火水木金土日]\)$", "", value)

    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    try:
        dt = datetime.strptime(value, "%Y/%m/%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    match = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})", value)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        try:
            dt = datetime(default_year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def normalize_date_list(value, default_year=None):
    if value is None:
        return []

    if isinstance(value, list):
        raw_parts = value
    else:
        text = str(value).strip()
        if not text:
            return []

        separators = [",", "、", "\n"]
        temp = text
        for sep in separators:
            temp = temp.replace(sep, "|")
        raw_parts = [part.strip() for part in temp.split("|") if part.strip()]

    result = []
    for part in raw_parts:
        iso_date = parse_date_to_iso(part, default_year=default_year)
        if iso_date:
            result.append(iso_date)

    return sorted(set(result))


def pick_first(item, keys, default=""):
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return default


def build_blog_schedule(raw_items, default_year=None):
    schedule_items = []

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        shop_name = str(
            pick_first(raw_item, ["shop_name", "shop", "store_name", "store"], "")
        ).strip()

        cast_name = str(
            pick_first(raw_item, ["cast_name", "name", "therapist_name"], "")
        ).strip()

        raw_dates = pick_first(
            raw_item,
            ["dates", "date_list", "schedule_dates", "shift_dates", "work_dates", "date"],
            [],
        )

        dates = normalize_date_list(raw_dates, default_year=default_year)

        if not shop_name or not cast_name or not dates:
            continue

        schedule_items.append(
            {
                "shop_name": shop_name,
                "cast_name": cast_name,
                "dates": dates,
            }
        )

    return schedule_items
