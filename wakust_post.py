import os
from typing import Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait


POST_NEW_URL = "https://wakust.com/mypage/?post_new"
POST_LIST_URL = "https://wakust.com/mypage/?post_list"

PROFILE_DIR = r"C:\Users\Youhei\python_work\wakust_edge_profile"

DEFAULT_CATEGORY_VALUE = "19"
DEFAULT_TAGS = "愛知県,メンズエステ"


def create_driver() -> webdriver.Edge:
    os.makedirs(PROFILE_DIR, exist_ok=True)

    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    return webdriver.Edge(options=options)


def wait_for_post_page(driver: webdriver.Edge) -> None:
    WebDriverWait(driver, 30).until(
        lambda current_driver: current_driver.execute_script(
            "return document.readyState"
        )
        == "complete"
    )

    WebDriverWait(driver, 30).until(
        lambda current_driver: current_driver.find_elements(
            By.NAME,
            "post_title",
        )
    )

    WebDriverWait(driver, 30).until(
        lambda current_driver: current_driver.find_elements(
            By.ID,
            "tinymce_area_ifr",
        )
    )


def confirm_login(driver: webdriver.Edge) -> None:
    current_url = driver.current_url.lower()

    if "/login" in current_url:
        raise RuntimeError(
            "ワクストのログイン状態が切れています。"
            " test.pyで手動ログインを行い、ログイン状態を保存してください。"
        )

    password_elements = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='password']",
    )

    if password_elements:
        raise RuntimeError(
            "ワクストのログイン画面が表示されています。"
            " test.pyで手動ログインを行ってください。"
        )


def set_title(driver: webdriver.Edge, title: str) -> None:
    title_input = driver.find_element(By.NAME, "post_title")
    title_input.clear()
    title_input.send_keys(title)

    print(f"[WAKUST] タイトル入力成功: {title}")


def set_free_body(driver: webdriver.Edge, body_html: str) -> None:
    iframe = driver.find_element(By.ID, "tinymce_area_ifr")
    driver.switch_to.frame(iframe)

    body = WebDriverWait(driver, 20).until(
        lambda current_driver: current_driver.find_element(
            By.ID,
            "tinymce",
        )
    )

    driver.execute_script(
        """
        const body = arguments[0];
        const html = arguments[1];

        body.innerHTML = html;

        body.dispatchEvent(
            new InputEvent(
                "input",
                {
                    bubbles: true,
                    inputType: "insertText",
                    data: null
                }
            )
        );

        body.dispatchEvent(
            new Event(
                "change",
                {
                    bubbles: true
                }
            )
        );
        """,
        body,
        body_html,
    )

    driver.switch_to.default_content()

    driver.execute_script(
        """
        if (
            window.tinymce &&
            tinymce.get("tinymce_area")
        ) {
            tinymce.get("tinymce_area").setContent(arguments[0]);
            tinymce.get("tinymce_area").save();
        }
        """,
        body_html,
    )

    print("[WAKUST] 無料本文入力成功")


def set_category(
    driver: webdriver.Edge,
    category_value: str,
) -> None:
    category_select = Select(
        driver.find_element(
            By.NAME,
            "categorys",
        )
    )

    category_select.select_by_value(category_value)

    print(f"[WAKUST] カテゴリー設定成功: {category_value}")


def add_tags(
    driver: webdriver.Edge,
    tags: str,
) -> None:
    tag_input = driver.find_element(By.ID, "input_tag_f")
    tag_input.clear()
    tag_input.send_keys(tags)

    add_button = driver.find_element(By.ID, "add_tag_btn")

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        add_button,
    )

    driver.execute_script(
        "arguments[0].click();",
        add_button,
    )

    WebDriverWait(driver, 10).until(
        lambda current_driver: current_driver.find_element(
            By.NAME,
            "post_tags",
        ).get_attribute("value")
        not in ["", None]
    )

    post_tags_value = driver.find_element(
        By.NAME,
        "post_tags",
    ).get_attribute("value")

    print(f"[WAKUST] タグ追加成功: {post_tags_value}")


def set_public_status(
    driver: webdriver.Edge,
    publish: bool,
) -> None:
    status_select = Select(
        driver.find_element(
            By.NAME,
            "post_st",
        )
    )

    if publish:
        status_select.select_by_value("0")
        print("[WAKUST] 公開設定: 公開")
    else:
        status_select.select_by_value("1")
        print("[WAKUST] 公開設定: 非公開")


def save_editor_content(driver: webdriver.Edge) -> None:
    driver.execute_script(
        """
        if (window.tinymce) {
            tinymce.triggerSave();
        }
        """
    )

    print("[WAKUST] TinyMCE本文保存成功")


def click_post_confirmation(driver: webdriver.Edge) -> None:
    confirmation_button = driver.find_element(
        By.ID,
        "submit_new_s",
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        confirmation_button,
    )

    driver.execute_script(
        "arguments[0].click();",
        confirmation_button,
    )

    WebDriverWait(driver, 20).until(
        lambda current_driver: any(
            element.is_displayed()
            and "投稿する"
            in (
                (element.text or "")
                + (element.get_attribute("value") or "")
            )
            for element in current_driver.find_elements(
                By.CSS_SELECTOR,
                "button, input[type='submit'], input[type='button']",
            )
        )
    )

    print("[WAKUST] 投稿確認画面表示成功")


def find_final_post_button(
    driver: webdriver.Edge,
):
    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "button, input[type='submit'], input[type='button']",
    )

    for element in elements:
        try:
            if not element.is_displayed():
                continue
        except Exception:
            continue

        text = " ".join((element.text or "").split()).strip()
        value = " ".join(
            (element.get_attribute("value") or "").split()
        ).strip()

        label = text or value

        if label == "投稿する":
            return element

    raise RuntimeError(
        "投稿確認画面の「投稿する」ボタンが見つかりませんでした。"
    )


def click_final_post(driver: webdriver.Edge) -> None:
    final_button = find_final_post_button(driver)

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        final_button,
    )

    driver.execute_script(
        "arguments[0].click();",
        final_button,
    )

    WebDriverWait(driver, 30).until(
        lambda current_driver: (
            "?post_list" in current_driver.current_url
            or current_driver.current_url == POST_LIST_URL
            or "投稿一覧" in current_driver.page_source
        )
    )

    print("[WAKUST] 最終投稿処理成功")


def post_to_wakust(
    title: str,
    body_html: str,
    publish: bool = False,
    tags: str = DEFAULT_TAGS,
    category_value: str = DEFAULT_CATEGORY_VALUE,
) -> Dict[str, str]:
    if not title or not title.strip():
        raise ValueError("ワクスト投稿タイトルが空です。")

    if not body_html or not body_html.strip():
        raise ValueError("ワクスト投稿本文が空です。")

    if not tags or not tags.strip():
        raise ValueError("ワクスト投稿タグが空です。")

    print("[WAKUST] 自動投稿開始")
    print(f"[WAKUST] 投稿タイトル: {title}")
    print(f"[WAKUST] 公開設定: {'公開' if publish else '非公開'}")

    driver = create_driver()

    try:
        driver.get(POST_NEW_URL)
        wait_for_post_page(driver)
        confirm_login(driver)

        print("[WAKUST] 新規投稿画面表示成功")

        set_title(driver, title)
        set_free_body(driver, body_html)
        set_category(driver, category_value)
        add_tags(driver, tags)
        set_public_status(driver, publish)
        save_editor_content(driver)
        click_post_confirmation(driver)
        click_final_post(driver)

        result = {
            "title": title,
            "status": "公開" if publish else "非公開",
            "url": driver.current_url,
        }

        print(f"[WAKUST] 投稿後URL: {result['url']}")
        print("[WAKUST] 自動投稿完了")

        return result

    except Exception as error:
        print(f"[WAKUST] 自動投稿エラー: {error}")
        raise

    finally:
        driver.quit()
        print("[WAKUST] ブラウザ終了")


if __name__ == "__main__":
    print(
        "wakust_post.pyは自動投稿用モジュールです。"
        " 単独では記事を投稿しません。"
    )