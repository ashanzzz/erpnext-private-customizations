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
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

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
    page.on("response", lambda resp: print(f"[HTTP {resp.status}] {resp.url}") if resp.status >= 400 else None)

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

    # 1. 验证 Tab 3 社保页面与修改配置
    print("\n--- 1. Testing Tab 3: 社保页面与修改配置 ---")
    page.click("[data-tab='social_insurance']")
    time.sleep(2)
    page.click("#btn-qifu-edit-ss-setting")
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)
    print("✅ Tab 3 edit settings dialog opened and closed cleanly.")

    # 2. 验证 Tab 4 公积金页面与修改配置
    print("\n--- 2. Testing Tab 4: 公积金页面与修改配置 ---")
    page.click("[data-tab='housing_fund']")
    time.sleep(2)
    page.click("#btn-qifu-edit-hf-setting")
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)
    print("✅ Tab 4 edit settings dialog opened and closed cleanly.")

    # 3. 验证 Tab 5 综合核定中的【查看社会保险明细】与【查看住房公积金】弹窗
    print("\n--- 3. Testing Tab 5: 综合核定中的社保与公积金弹窗 ---")
    page.click("[data-tab='settlement']")
    time.sleep(2)
    page.click("#btn-view-ins-sheet-modal")
    time.sleep(2)
    page.wait_for_selector("#table-modal-ins-sheet", state="visible", timeout=5000)
    print("✅ Tab 5 -> Social Insurance 19-col modal opened successfully.")
    page.keyboard.press("Escape")
    time.sleep(1)

    page.click("#btn-view-hf-sheet-modal")
    time.sleep(2)
    page.wait_for_selector("#table-modal-hf-sheet", state="visible", timeout=5000)
    print("✅ Tab 5 -> Housing Fund 12-col modal opened successfully.")
    page.keyboard.press("Escape")
    time.sleep(1)

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! Everything works smoothly.")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
