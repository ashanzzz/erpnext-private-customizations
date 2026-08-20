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

    # 截图1: 单行顶栏默认视图
    shot_single_line = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_single_line_header.png"
    page.screenshot(path=shot_single_line)
    print("Saved Single Line Header Shot:", shot_single_line)

    # 修改一个读数并失焦，触发自动保存
    first_input = page.locator(".cell-reading-input").first
    first_input.fill("2781")
    first_input.blur()
    time.sleep(1.5)

    # 截图2: 自动保存完成后的时间戳胶囊
    shot_autosaved = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_autosaved_with_time.png"
    page.screenshot(path=shot_autosaved)
    print("Saved Auto-Saved Shot:", shot_autosaved)

    # 点击 [ 💾 保存草稿 ] 手动保存
    page.click("#btn-save-draft")
    time.sleep(1.5)

    # 截图3: 手动保存完成后的状态
    shot_manual_saved = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_manual_saved_with_time.png"
    page.screenshot(path=shot_manual_saved)
    print("Saved Manual-Saved Shot:", shot_manual_saved)

    browser.close()
