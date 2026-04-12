import re


SHOP_NAME = "リゼクシー"
DOMAIN_KEYWORDS = ["resexy.info"]


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
    title_texts = []

    if soup is not None and getattr(soup, "title", None):
        title = soup.title.get_text(" ", strip=True)
        if title:
            title_texts.append(_normalize_text(title))

    for txt in title_texts:
        m = re.search(r"(.+?)のプロフィール", txt)
        if m:
            return _normalize_text(m.group(1))

        m = re.search(r"^(.+?)[｜|/]", txt)
        if m:
            cand = _normalize_text(m.group(1))
            if cand and "メンズエステ" not in cand and "PROFILE" not in cand.upper():
                return cand

    for line in lines:
        m = re.search(r"(.+?)のプロフィール", line)
        if m:
            return _normalize_text(m.group(1))

    return fallback_name


def extract_name(lines, soup=None, fallback_name=""):
    name = _extract_name_from_title_or_lines(soup, lines, fallback_name="")
    if name:
        return name

    for i, line in enumerate(lines):
        if line in ["プロフィール", "PROFILE", "プロフィール PROFILE", "PROFILE プロフィール"]:
            for j in range(i + 1, min(i + 12, len(lines))):
                cand = _normalize_text(lines[j])
                if not cand:
                    continue
                if cand.startswith("Image:"):
                    continue
                if cand in ["駅ちかブログ", "X", "お店のコメント", "Schedule", "SCHEDULE"]:
                    continue
                if re.search(r"T\.\d+", cand):
                    continue
                if re.search(r"\(\d+\)", cand):
                    return _normalize_text(re.sub(r"\(\d+\).*", "", cand))
                if len(cand) <= 20 and re.search(r"[ぁ-んァ-ヶ一-龠]", cand):
                    return cand

    return fallback_name


def _is_off_text(text):
    text = _normalize_text(text)
    return text in ["お休み", "休み", "未定", "-", "--", "---", "×", "✕", "✖"]


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


def _extract_schedule_block(lines):
    start = -1

    for i, line in enumerate(lines):
        if _normalize_text(line) == "Schedule":
            start = i
            break

    if start == -1:
        return []

    return [_normalize_text(x) for x in lines[start + 1:start + 80]]


def _extract_shifts_from_schedule_block(lines):
    block = _extract_schedule_block(lines)
    if not block:
        return []

    date_pattern = re.compile(r"^(\d{1,2})月(\d{1,2})日\(([月火水木金土日])\)$")

    dates = []
    statuses = []

    idx = 0
    while idx < len(block):
        m = date_pattern.fullmatch(block[idx])
        if not m:
            idx += 1
            continue

        while idx < len(block):
            m = date_pattern.fullmatch(block[idx])
            if not m:
                break
            month = int(m.group(1))
            day = int(m.group(2))
            wd = m.group(3)
            dates.append((month, day, wd))
            idx += 1
        break

    while idx < len(block):
        line = _normalize_text(block[idx])

        if not line:
            idx += 1
            continue

        if date_pattern.fullmatch(line):
            break

        if _is_off_text(line) or _is_work_text(line):
            statuses.append(line)

        idx += 1

    if not dates or not statuses:
        return []

    count = min(len(dates), len(statuses))
    result = []

    for i in range(count):
        month, day, wd = dates[i]
        status = statuses[i]

        if _is_work_text(status):
            result.append(f"{month:02d}/{day:02d}({wd})")

    return _dedupe_keep_order(result)


def _extract_shifts_nearby(lines):
    result = []
    date_pattern = re.compile(r"^(\d{1,2})月(\d{1,2})日\(([月火水木金土日])\)$")

    for i, raw_line in enumerate(lines):
        line = _normalize_text(raw_line)
        m = date_pattern.fullmatch(line)
        if not m:
            continue

        month = int(m.group(1))
        day = int(m.group(2))
        wd = m.group(3)

        window = []
        for j in range(i + 1, min(i + 6, len(lines))):
            nxt = _normalize_text(lines[j])
            if date_pattern.fullmatch(nxt):
                break
            window.append(nxt)

        has_off = any(_is_off_text(x) for x in window)
        has_work = any(_is_work_text(x) for x in window)

        if has_work and not has_off:
            result.append(f"{month:02d}/{day:02d}({wd})")

    return _dedupe_keep_order(result)


def extract_shifts(lines):
    result = _extract_shifts_from_schedule_block(lines)
    if result:
        return result

    result = _extract_shifts_nearby(lines)
    if result:
        return result

    return []


def parse(url, soup, lines, fallback_name=""):
    name = extract_name(lines, soup=soup, fallback_name=fallback_name)
    shifts = extract_shifts(lines)

    return {
        "shop": SHOP_NAME,
        "url": url,
        "name": name,
        "shifts": shifts,
    }
