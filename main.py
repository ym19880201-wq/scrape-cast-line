from common import build_message, send_line_message
from sites import churitos, kuraimax, galaxy, torihada, exe, hosifuluspa, felicia, haniel, cmoon, theratopia

TARGETS = [
    {"shop": "チュリトス", "url": "https://churitos01.com/profile?lid=148", "parser": churitos},
    {"shop": "クライマックス東岡崎", "url": "https://kuraimaxmax.com/profile.php?sid=399", "parser": kuraimax},
    {"shop": "ギャラクシー", "url": "https://galaxy-nagoya.com/cast/%E3%82%86%E3%82%8A", "parser": galaxy},
    {"shop": "ギャラクシー", "url": "https://galaxy-nagoya.com/cast/%E3%82%8C%E3%81%84", "parser": galaxy},
    {"shop": "トリハダスパ", "url": "https://torihada-spa.men-es.jp/profile.html?sid=266", "parser": torihada},
    {"shop": "トリハダスパ", "url": "https://torihada-spa.men-es.jp/profile.html?sid=305", "parser": torihada},
    {"shop": "エグゼ", "url": "https://exe-mensspa.nagoya/profile.html?sid=32", "parser": exe},
    {"shop": "ほしふるスパ", "url": "https://hosifuluspa.com/cast/%e3%81%82%e3%82%84%e3%81%ae/", "parser": hosifuluspa},
    {"shop": "フェリシア", "url": "https://felicia-garden.com/profile.php?sid=210", "parser": felicia},
    {"shop": "ハニエル", "url": "https://haniel-nagoya.net/profile.html?5082", "parser": haniel},
    {"shop": "C-MOON", "url": "https://www.c-moon.info/profile/_uid/10617/", "parser": cmoon},
    {"shop": "セラトピア", "url": "https://esthe-theratopia.net/profile.html?sid=176", "parser": theratopia}
]


def main():
    results = []

    for target in TARGETS:
        shop = target["shop"]
        url = target["url"]
        parser = target["parser"]

        try:
            name, shifts = parser.parse(url)

            print("URL:", url)
            print(" -> 店:", shop)
            print(" -> 名前:", name if name else "取得失敗")
            print(" -> 出勤:", ", ".join(shifts) if shifts else "出勤予定なし")
            print("")

            results.append({
                "shop": shop,
                "name": name,
                "shifts": shifts
            })

        except Exception as e:
            print("URL:", url)
            print(" -> エラー:", e)
            print("")

            results.append({
                "shop": shop,
                "name": "取得失敗",
                "shifts": [f"取得エラー: {e}"]
            })

    message = build_message(results)

    print("LINE送信メッセージ:")
    print(message)
    print("")

    send_line_message(message)


if __name__ == "__main__":
    main()
