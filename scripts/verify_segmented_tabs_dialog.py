import os
import json
import time
from playwright.sync_api import sync_playwright

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1150})

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")

    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 前往水电费工作台
    page.goto(f"{SITE_URL}/desk/property-settlement-workbench")
    page.wait_for_selector(".prop-unified-header-bar", state="visible", timeout=15000)
    time.sleep(2)

    # 点击 [ ➕ 添加调整 ] 打开弹窗
    page.click("#btn-add-adj")
    page.wait_for_selector(".prop-modal-tab-group", state="visible", timeout=5000)
    time.sleep(1)

    # 截图1: 默认分段选项卡弹窗
    shot_default = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_segmented_tab_default.png"
    page.screenshot(path=shot_default)
    print("Saved Segmented Tab Default Shot:", shot_default)

    # 单击 [ 🔢 按用量调整 (度/m³) ]
    page.click("#grp-adj-type .prop-tab-item[data-val='按用量']")
    time.sleep(0.5)

    # 单击 [ 💧 自来水费 ]
    page.click("#grp-util-type .prop-tab-item[data-val='水费']")
    time.sleep(0.5)

    # 截图2: 1次点击即生效的用量+水费切换
    shot_usage = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_segmented_tab_usage_water.png"
    page.screenshot(path=shot_usage)
    print("Saved Segmented Tab Usage Shot:", shot_usage)

    # 单击 [ 🏢 单公司独立调整 ]
    page.click("#grp-adj-scope .prop-tab-item[data-val='单公司']")
    time.sleep(0.5)

    # 截图3: 1次点击即生效的单公司模式
    shot_single = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_segmented_tab_single_comp.png"
    page.screenshot(path=shot_single)
    print("Saved Segmented Tab Single Comp Shot:", shot_single)

    browser.close()
