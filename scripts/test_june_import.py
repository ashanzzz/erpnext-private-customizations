import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/meal-settlement-workbench")
    page.wait_for_selector(".meal-top-bar", state="visible", timeout=15000)
    time.sleep(1)

    # 切换到 2026-06
    page.click("#btn-prev-month")
    time.sleep(0.5)
    page.click("#btn-prev-month")
    time.sleep(1)

    excel_file = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\订餐记录(2).xlsx"
    page.click("#btn-upload-excel")
    page.wait_for_selector("#inp-meal-excel", state="attached", timeout=5000)
    page.set_input_files("#inp-meal-excel", excel_file)
    time.sleep(1)

    # 点击主操作按钮
    page.click(".modal.show .modal-footer button.btn-primary")
    time.sleep(3)

    # 截图 1: 成功弹窗 (识别出【2026年订餐6月】)
    shot_june_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_june_upload_modal.png"
    page.screenshot(path=shot_june_modal)
    print("Saved June Modal Shot:", shot_june_modal)

    # 关弹窗
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图 2: 6月份完整数据
    shot_june_full = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_june_full_workbench.png"
    page.screenshot(path=shot_june_full)
    print("Saved June Full Workbench Shot:", shot_june_full)

    browser.close()
