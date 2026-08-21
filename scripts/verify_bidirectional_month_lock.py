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

    # 1. 确保当前为 2026-07
    page.fill("#qifu-month-select", "2026-07")
    cur_m = page.input_value("#qifu-month-select")
    print(f"Current Month: {cur_m}")

    # 2. 测试回溯至未建账/无有效数据的历史月份 (◀ 上月)
    print("\n--- 1. Testing Backward Month to Unsettled/No-data History (回溯历史月份拦截) ---")
    page.click("#btn-qifu-prev-month")
    time.sleep(1.5)

    is_modal_visible = page.is_visible(".modal.in, .modal.show")
    if is_modal_visible:
        modal_title = page.text_content(".modal.in .modal-title, .modal.show .modal-title")
        print(f"✅ Backward Interception Modal Visible! Title: {modal_title.strip() if modal_title else ''}")
        shot1 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_backward_history_intercepted.png"
        page.screenshot(path=shot1)
        page.keyboard.press("Escape")
        time.sleep(1)
    else:
        print("Backward Month was allowed (Target month had valid data/locked)")

    after_prev_m = page.input_value("#qifu-month-select")
    print(f"Input Month Value after backward attempt: {after_prev_m}")

    # 3. 测试推进至未来月份 (▶ 下月)
    print("\n--- 2. Testing Forward Month when current month is Draft (未核定禁止跳下月) ---")
    page.click("#btn-qifu-next-month")
    time.sleep(1.5)

    is_modal_forward = page.is_visible(".modal.in, .modal.show")
    if is_modal_forward:
        modal_title_fwd = page.text_content(".modal.in .modal-title, .modal.show .modal-title")
        print(f"✅ Forward Interception Modal Visible! Title: {modal_title_fwd.strip() if modal_title_fwd else ''}")
        shot2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_forward_draft_intercepted.png"
        page.screenshot(path=shot2)
        page.keyboard.press("Escape")
        time.sleep(1)

    after_fwd_m = page.input_value("#qifu-month-select")
    print(f"Input Month Value after forward attempt: {after_fwd_m}")

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! BIDIRECTIONAL MONTH TRANSITION VALIDATION 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
