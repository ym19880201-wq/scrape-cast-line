import os
from typing import Dict, Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait


LOGIN_URL = "https://wakust.com/login/"
POST_NEW_URL = "https://wakust.com/mypage/?post_new"
POST_LIST_URL = "https://wakust.com/mypage/?post_list"

PROFILE_DIR = r"C:\Users\Youhei\python_work\wakust_edge_profile"

DEFAULT_CATEGORY_VALUE = "19"
DEFAULT_TAGS = "愛知県,メンズエステ"

IS_GITHUB_ACTIONS = (
    os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true"
)


def create_local_driver() -> webdriver.Edge:
    os.makedirs(PROFILE_DIR, exist_ok=True)

    options = EdgeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    return webdriver.Edge(options=options)


def create_github_driver() -> webdriver.Chrome:
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions")

    return webdriver.Chrome(options=options)


def create_driver() -> Union[webdriver.Edge, webdriver.Chrome]:
    if IS_GITHUB_ACTIONS:
        print("[WAKUST] GitHub Actions用Chromeを起動します")
        return create_github_driver()

    print("[WAKUST] ローカル用Edgeを起動します")
    return create_local_driver()


def wait_for_page_complete(driver: WebDriver) -> None:
    WebDriverWait(driver, 30).until(
        lambda current_driver: current_driver.execute_script(
            "return document.readyState"
        )
        == "complete"
    )


def click_age_confirmation_if_present(driver: WebDriver) -> None:
    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "button, input[type='button'], input[type='submit']",
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

        if label == "はい":
            driver.execute_script(
                "arguments[0].click();",
                element,
            )
            print("[WAKUST] 年齢確認を通過しました")
            return


def find_email_input(driver: WebDriver):
    selectors = [
        "input[type='email']",
        "input[name*='mail' i]",
        "input[name*='email' i]",
    ]

    for selector in selectors:
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector,
        )

        for element in elements:
            try:
                if element.is_displayed():
                    return element
            except Exception:
                continue

    raise RuntimeError(
        "ワクストのメールアドレス入力欄が見つかりませんでした。"
    )


def find_password_input(driver: WebDriver):
    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='password']",
    )

    for element in elements:
        try:
            if element.is_displayed():
                return element
        except Exception:
            continue

    raise RuntimeError(
        "ワクストのパスワード入力欄が見つかりませんでした。"
    )


def find_login_button(driver: WebDriver):
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

        if label == "ログイン":
            return element

    raise RuntimeError(
        "ワクストのログインボタンが見つかりませんでした。"
    )


def get_wakust_login_credentials() -> Dict[str, str]:
    email = os.getenv("WAKUST_EMAIL", "").strip()
    password = os.getenv("WAKUST_PASSWORD", "").strip()

    if not email:
        raise RuntimeError(
            "GitHub SecretsのWAKUST_EMAILが設定されていません。"
        )

    if not password:
        raise RuntimeError(
            "GitHub SecretsのWAKUST_PASSWORDが設定されていません。"
        )

    return {
        "email": email,
        "password": password,
    }


def login_to_wakust(driver: WebDriver) -> None:
    credentials = get_wakust_login_credentials()

    print("[WAKUST] GitHub Actions用ログイン開始")

    driver.get(LOGIN_URL)
    wait_for_page_complete(driver)
    click_age_confirmation_if_present(driver)

    email_input = WebDriverWait(driver, 30).until(
        lambda current_driver: find_email_input(
            current_driver
        )
    )

    password_input = find_password_input(driver)

    email_input.clear()
    email_input.send_keys(credentials["email"])

    password_input.clear()
    password_input.send_keys(credentials["password"])

    login_button = find_login_button(driver)

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        login_button,
    )

    driver.execute_script(
        "arguments[0].click();",
        login_button,
    )

    WebDriverWait(driver, 30).until(
        lambda current_driver: (
            "/login" not in current_driver.current_url.lower()
            and not current_driver.find_elements(
                By.CSS_SELECTOR,
                "input[type='password']",
            )
        )
    )

    print("[WAKUST] GitHub Actions用ログイン成功")


def open_post_page(driver: WebDriver) -> None:
    driver.get(POST_NEW_URL)
    wait_for_page_complete(driver)
    click_age_confirmation_if_present(driver)

    current_url = driver.current_url.lower()

    if "/login" in current_url:
        if not IS_GITHUB_ACTIONS:
            raise RuntimeError(
                "ワクストのログイン状態が切れています。"
                " test.pyで手動ログインを行い、"
                "ログイン状態を保存してください。"
            )

        login_to_wakust(driver)

        driver.get(POST_NEW_URL)
        wait_for_page_complete(driver)
        click_age_confirmation_if_present(driver)


def wait_for_post_page(driver: WebDriver) -> None:
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


def confirm_login(driver: WebDriver) -> None:
    current_url = driver.current_url.lower()

    if "/login" in current_url:
        raise RuntimeError(
            "ワクストのログインに失敗しています。"
        )

    password_elements = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='password']",
    )

    visible_password_elements = []

    for element in password_elements:
        try:
            if element.is_displayed():
                visible_password_elements.append(element)
        except Exception:
            continue

    if visible_password_elements:
        raise RuntimeError(
            "ワクストのログイン画面が表示されています。"
        )


def set_title(
    driver: WebDriver,
    title: str,
) -> None:
    title_input = driver.find_element(
        By.NAME,
        "post_title",
    )
    title_input.clear()
    title_input.send_keys(title)

    print(f"[WAKUST] タイトル入力成功: {title}")


def set_free_body(
    driver: WebDriver,
    body_html: str,
) -> None:
    iframe = driver.find_element(
        By.ID,
        "tinymce_area_ifr",
    )
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
    driver: WebDriver,
    category_value: str,
) -> None:
    category_select = Select(
        driver.find_element(
            By.NAME,
            "categorys",
        )
    )

    category_select.select_by_value(
        category_value
    )

    print(
        "[WAKUST] カテゴリー設定成功: "
        f"{category_value}"
    )


def add_tags(
    driver: WebDriver,
    tags: str,
) -> None:
    tag_input = driver.find_element(
        By.ID,
        "input_tag_f",
    )
    tag_input.clear()
    tag_input.send_keys(tags)

    add_button = driver.find_element(
        By.ID,
        "add_tag_btn",
    )

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

    print(
        "[WAKUST] タグ追加成功: "
        f"{post_tags_value}"
    )


def set_public_status(
    driver: WebDriver,
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


def save_editor_content(
    driver: WebDriver,
) -> None:
    driver.execute_script(
        """
        if (window.tinymce) {
            tinymce.triggerSave();
        }
        """
    )

    print("[WAKUST] TinyMCE本文保存成功")


def click_post_confirmation(
    driver: WebDriver,
) -> None:
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
                + (
                    element.get_attribute("value")
                    or ""
                )
            )
            for element in current_driver.find_elements(
                By.CSS_SELECTOR,
                (
                    "button, input[type='submit'], "
                    "input[type='button']"
                ),
            )
        )
    )

    print("[WAKUST] 投稿確認画面表示成功")


def find_final_post_button(
    driver: WebDriver,
):
    elements = driver.find_elements(
        By.CSS_SELECTOR,
        (
            "button, input[type='submit'], "
            "input[type='button']"
        ),
    )

    for element in elements:
        try:
            if not element.is_displayed():
                continue
        except Exception:
            continue

        text = " ".join(
            (element.text or "").split()
        ).strip()

        value = " ".join(
            (
                element.get_attribute("value")
                or ""
            ).split()
        ).strip()

        label = text or value

        if label == "投稿する":
            return element

    raise RuntimeError(
        "投稿確認画面の「投稿する」ボタンが"
        "見つかりませんでした。"
    )


def click_final_post(
    driver: WebDriver,
) -> None:
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
            "?post_list"
            in current_driver.current_url
            or current_driver.current_url
            == POST_LIST_URL
            or "投稿一覧"
            in current_driver.page_source
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
        raise ValueError(
            "ワクスト投稿タイトルが空です。"
        )

    if not body_html or not body_html.strip():
        raise ValueError(
            "ワクスト投稿本文が空です。"
        )

    if not tags or not tags.strip():
        raise ValueError(
            "ワクスト投稿タグが空です。"
        )

    print("[WAKUST] 自動投稿開始")
    print(f"[WAKUST] 投稿タイトル: {title}")
    print(
        "[WAKUST] 公開設定: "
        f"{'公開' if publish else '非公開'}"
    )

    driver = create_driver()

    try:
        open_post_page(driver)
        wait_for_post_page(driver)
        confirm_login(driver)

        print("[WAKUST] 新規投稿画面表示成功")

        set_title(
            driver,
            title,
        )
        set_free_body(
            driver,
            body_html,
        )
        set_category(
            driver,
            category_value,
        )
        add_tags(
            driver,
            tags,
        )
        set_public_status(
            driver,
            publish,
        )
        save_editor_content(driver)
        click_post_confirmation(driver)
        click_final_post(driver)

        result = {
            "title": title,
            "status": (
                "公開"
                if publish
                else "非公開"
            ),
            "url": driver.current_url,
        }

        print(
            "[WAKUST] 投稿後URL: "
            f"{result['url']}"
        )
        print("[WAKUST] 自動投稿完了")

        return result

    except Exception as error:
        print(
            "[WAKUST] 自動投稿エラー: "
            f"{error}"
        )
        raise

    finally:
        driver.quit()
        print("[WAKUST] ブラウザ終了")


if __name__ == "__main__":
    print(
        "wakust_post.pyは自動投稿用モジュールです。"
        " 単独では記事を投稿しません。"
    )