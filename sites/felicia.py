from common import fetch


def parse(url):
    title, lines = fetch(url)

    name = ""
    shifts = []

    for line in lines:
        if "桃瀬ゆいか" in line:
            name = "桃瀬ゆいか"
            break

    return name, shifts
