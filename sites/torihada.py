from common import fetch, parse_torihada_schedule


def parse(url):
    title, lines = fetch(url)

    name = ""
    shifts = []

    name = title.split("｜")[0].strip()

    shifts = parse_torihada_schedule(lines)

    return name, shifts
