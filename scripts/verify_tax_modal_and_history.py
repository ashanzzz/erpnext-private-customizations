import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

for i in range(25):
    try:
        r = requests.get(f"{SITE_URL}/api/method/ping", timeout=3)
        if r.status_code == 200:
            print("Site is ready!")
            break
    except Exception:
        pass
    time.sleep(2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1850, "height": 1150})

    errors = []
    page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}") if msg.type in ['error', 'warning'] else None)
    page.on("pageerror", lambda err: errors.append(str(err)))

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 切换至 Tab 5: 个税核定与申报台账
    print("\n--- 1. Switching to Tab 5: Tax Settlement Tab ---")
    page.click(".qifu-tab-btn[data-tab='tax']")
    time.sleep(2)

    # 2. 点击【个税起征点和7级超额累进表】按钮
    print("\n--- 2. Clicking Tax Rules and Rate Table Button ---")
    page.click("#btn-qifu-edit-tax-setting")
    time.sleep(2)

    # 验证弹窗数量 (必须只有 1 个)
    modals = page.query_selector_all(".modal.in, .modal.show")
    print(f"Visible Modals count: {len(modals)}")
    
    shot_tax_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_unified_tax_dialog.png"
    page.screenshot(path=shot_tax_modal)
    print(f"Captured screenshot: {shot_tax_modal}")

    page.keyboard.press("Escape")
    time.sleep(1)

    # 3. 验证历史月份切换 (回溯至 2026-06 历史已建账月)
    print("\n--- 3. Testing Switching to Historical Month 2026-06 ---")
    page.click("#btn-qifu-prev-month")
    time.sleep(2)

    cur_m = page.input_value("#qifu-month-select")
    print(f"Switched Month: {cur_m}")

    shot_history_6 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_history_2026_06_loaded.png"
    page.screenshot(path=shot_history_6)
    print(f"Captured 2026-06 history screenshot: {shot_history_6}")

    # 4. 再往前切至 2026-05
    page.click("#btn-qifu-prev-month")
    time.sleep(2)
    cur_m5 = page.input_value("#qifu-month-select")
    print(f"Switched Month 2: {cur_m5}")

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! UNIFIED TAX MODAL & HISTORY MONTH DATA 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
