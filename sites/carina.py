import re


SHOP_NAME = "カリーナ"
DOMAIN_KEYWORDS = ["carina-esthe.com"]


def can_handle(url):
    url = (url or "").lower()
    return any(key in url for key in DOMAIN_KEYWORDS)


def _normalize_text(text):
    if not text:
        return ""
    text = text.replace("\u3000", " ")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _dedupe_keep_order(items):
    return list(dict.fromkeys(items))


def _extract_name_from_title_or_lines(soup, lines, fallback_name=""):
    if soup is not None and getattr(soup, "title", None):
        title = _normalize_text(soup.title.get_text(" ", strip=True))

        m = re.search(r"Carina\s*\(カリーナ\)\s+(.+?)\s*$", title)
        if m:
            cand = _normalize_text(m.group(1))
            if cand:
                return cand

        m = re.search(r"【公式サイト】.+?Carina\(カリーナ\)\s+(.+?)\s*$", title)
        if m:
            cand = _normalize_text(m.group(1))
            if cand:
                return cand

    for line in lines:
        m = re.search(r"(.+?)のプロフィール", line)
        if m:
            return _normalize_text(m.group(1))

        m = re.search(r"^(.+?（.+?）)$", line)
        if m:
            cand = _normalize_text(m.group(1))
            if "トップページ" not in cand and "セラピスト一覧ページ" not in cand:
                return cand

    return fallback_name


def extract_name(lines, soup=None, fallback_name=""):
    name = _extract_name_from_title_or_lines(soup, lines, fallback_name="")
    if name:
        return name

    for i, line in enumerate(lines):
        if line in ["Profile", "PROFILE", "プロフィール"]:
            for j in range(i + 1, min(i + 12, len(lines))):
                cand = _normalize_text(lines[j])
                if not cand:
                    continue
                if cand.startswith("Image:"):
                    continue
                if cand in ["Comment", "コメント", "出勤スケジュール", "Schedule", "SCHEDULE"]:
                    continue
                if re.search(r"T\d+", cand):
                    continue
                if re.search(r"^.+?（.+?）$", cand):
                    return cand

    return fallback_name


def _is_off_text(text):
    text = _normalize_text(text)
    return text in ["", "-", "--", "---", "お休み", "休み", "未定", "×", "✕", "✖"]


def _is_work_text(text):
    text = _normalize_text(text)

    if not text or _is_off_text(text):
        return False

    patterns = [
        r"^(?:翌)?\d{1,2}:\d{2}\s*[-～〜~]\s*(?:翌)?\d{1,2}:\d{2}$",
        r"^\d{1,2}時\s*[-～〜~]\s*(?:翌)?\d{1,2}時$",
        r"^予約満了$",
        r"^満了$",
        r"^受付終了$",
        r"^完売$",
    ]

    for pattern in patterns:
        if re.fullmatch(pattern, text):
            return True

    return False


def _extract_shifts_from_soup_table(soup):
    if soup is None:
        return []

    date_pattern = re.compile(r"^(\d{1,2})月(\d{1,2})日\(([月火水木金土日])\)$")
    best_result = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        first_row_cells = rows[0].find_all(["th", "td"])
        second_row_cells = rows[1].find_all(["th", "td"])

        if len(first_row_cells) < 5 or len(second_row_cells) < 5:
            continue

        dates = []
        for cell in first_row_cells:
            text = _normalize_text(cell.get_text(" ", strip=True))
            m = date_pattern.fullmatch(text)
            if m:
                month = int(m.group(1))
                day = int(m.group(2))
                wd = m.group(3)
                dates.append((month, day, wd))
            else:
                dates.append(None)

        if sum(1 for x in dates if x is not None) < 5:
            continue

        statuses = []
        for cell in second_row_cells:
            text = _normalize_text(cell.get_text(" ", strip=True))
            statuses.append(text)

        count = min(len(dates), len(statuses))
        result = []

        for i in range(count):
            date_info = dates[i]
            status = statuses[i]

            if date_info is None:
                continue

            month, day, wd = date_info

            if _is_work_text(status):
                result.append(f"{month:02d}/{day:02d}({wd})")

        result = _dedupe_keep_order(result)

        if len(result) > len(best_result):
            best_result = result

    return best_result


def _find_schedule_start(lines):
    date_pattern = re.compile(r"^\d{1,2}月\d{1,2}日\([月火水木金土日]\)$")

    for i in range(len(lines)):
        count = 0
        j = i
        while j < len(lines) and date_pattern.fullmatch(_normalize_text(lines[j])):
            count += 1
            j += 1

        if count >= 5:
            return i

    return -1


def _extract_shifts_from_vertical_dates_and_statuses(lines):
    start = _find_schedule_start(lines)
    if start == -1:
        return []

    date_pattern = re.compile(r"^(\d{1,2})月(\d{1,2})日\(([月火水木金土日])\)$")

    dates = []
    idx = start

    while idx < len(lines):
        line = _normalize_text(lines[idx])
        m = date_pattern.fullmatch(line)
        if not m:
            break

        month = int(m.group(1))
        day = int(m.group(2))
        wd = m.group(3)
        dates.append((month, day, wd))
        idx += 1

    if not dates:
        return []

    raw_statuses = []
    while idx < len(lines):
        line = _normalize_text(lines[idx])

        if date_pattern.fullmatch(line):
            break

        if line in ["TEL", "LINE", "求人", "HOME", "GUIDELINES", "THERAPIST", "SYSTEM", "SCHEDULE", "EVENTLIST", "ACCESS", "RECRUIT", "ENQUETE", "MAGAZINE", "LINK", "©"]:
            break

        raw_statuses.append(line)
        idx += 1

    statuses = []
    for line in raw_statuses:
        if _is_work_text(line):
            statuses.append(line)
        elif _is_off_text(line):
            statuses.append("お休み")

    if not statuses:
        return []

    count = min(len(dates), len(statuses))
    result = []

    for i in range(count):
        month, day, wd = dates[i]
        status = statuses[i]

        if _is_work_text(status):
            result.append(f"{month:02d}/{day:02d}({wd})")

    return _dedupe_keep_order(result)


def _extract_shifts_from_inline_table_text(lines):
    for i in range(len(lines) - 1):
        date_matches = re.findall(r"(\d{1,2})月(\d{1,2})日\(([月火水木金土日])\)", _normalize_text(lines[i]))
        if len(date_matches) < 5:
            continue

        status_line = _normalize_text(lines[i + 1])

        status_tokens = re.findall(
            r"(?:翌)?\d{1,2}:\d{2}\s*[-～〜~]\s*(?:翌)?\d{1,2}:\d{2}|お休み|休み|未定|予約満了|満了|受付終了|完売|-|--|---|×|✕|✖",
            status_line
        )

        if not status_tokens:
            continue

        count = min(len(date_matches), len(status_tokens))
        result = []

        for idx in range(count):
            month, day, wd = date_matches[idx]
            status = _normalize_text(status_tokens[idx])

            if _is_work_text(status):
                result.append(f"{int(month):02d}/{int(day):02d}({wd})")

        if result:
            return _dedupe_keep_order(result)

    return []


def extract_shifts(lines, soup=None):
    result = _extract_shifts_from_soup_table(soup)
    if result:
        return result

    result = _extract_shifts_from_vertical_dates_and_statuses(lines)
    if result:
        return result

    result = _extract_shifts_from_inline_table_text(lines)
    if result:
        return result

    return []


def parse(url, soup, lines, fallback_name=""):
    normalized_lines = [_normalize_text(x) for x in lines if _normalize_text(x)]

    name = extract_name(normalized_lines, soup=soup, fallback_name=fallback_name)
    shifts = extract_shifts(normalized_lines, soup=soup)

    return {
        "shop": SHOP_NAME,
        "url": url,
        "name": name,
        "shifts": shifts,
    }
