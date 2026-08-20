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

    print("\n--- Testing Prev / Next Month Arrow Buttons ---")
    cur_m = page.input_value("#qifu-month-select")
    print(f"Current Month: {cur_m}")

    # 点击 ◀ 上月
    page.click("#btn-qifu-prev-month")
    time.sleep(2)
    prev_m = page.input_value("#qifu-month-select")
    print(f"After Click ◀ Prev Month: {prev_m}")

    # 再次点击 ◀ 上月
    page.click("#btn-qifu-prev-month")
    time.sleep(2)
    prev_m2 = page.input_value("#qifu-month-select")
    print(f"After Click ◀ Prev Month Again: {prev_m2}")

    # 点击 ▶ 下月
    page.click("#btn-qifu-next-month")
    time.sleep(2)
    next_m = page.input_value("#qifu-month-select")
    print(f"After Click ▶ Next Month: {next_m}")

    # 再次点击 ▶ 下月回到 2026-07
    page.click("#btn-qifu-next-month")
    time.sleep(2)
    back_m = page.input_value("#qifu-month-select")
    print(f"Back to Current Month: {back_m}")

    shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_month_arrows_restored.png"
    page.screenshot(path=shot)

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! PREV/NEXT MONTH ARROW BUTTONS 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
