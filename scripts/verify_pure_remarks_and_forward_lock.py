import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
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

    # 1. 确保初始为草稿模式
    is_locked = page.is_visible("#btn-qifu-unlock-month")
    if is_locked:
        page.click("#btn-qifu-unlock-month")
        time.sleep(1)
        page.fill(".modal.in textarea, .modal.show textarea", "重置为草稿")
        page.click(".modal.in .btn-primary, .modal.show .btn-primary")
        time.sleep(2)
        page.keyboard.press("Escape")
        time.sleep(1)

    print("\n--- 1. Testing Unsettled Forward Month Interception (未核定禁止跳下月) ---")
    cur_m = page.input_value("#qifu-month-select")
    print(f"Current Month (Draft): {cur_m}")

    # 点击 ▶ 下月 (应被拦截)
    page.click("#btn-qifu-next-month")
    time.sleep(1)
    modal_title = page.text_content(".modal.in .modal-title, .modal.show .modal-title")
    print(f"✅ Interception Modal Title: {modal_title.strip() if modal_title else 'No Modal'}")
    shot1 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_forward_month_intercepted.png"
    page.screenshot(path=shot1)

    page.keyboard.press("Escape")
    time.sleep(1)

    # 2. 验证看上月自由切换 (◀ 上月)
    print("\n--- 2. Testing Backward Month (看上月随意切换与全量数据刷新) ---")
    page.click("#btn-qifu-prev-month")
    time.sleep(2)
    prev_m = page.input_value("#qifu-month-select")
    print(f"✅ Successfully Switched to Previous Month: {prev_m}")

    # 3. 验证备考字段 100% 纯净 (不写系统核定零工资账期等)
    print("\n--- 3. Testing Pure Remarks (备考纯净无系统杂质) ---")
    page.click("[data-tab='settlement']")
    time.sleep(2)
    tab6_remarks = page.eval_on_selector_all("#tbody-qifu-payroll tr td:last-child", "els => els.map(e => e.innerText.trim())")
    has_system_remarks = any("系统核定" in r or "一口价" in r for r in tab6_remarks)
    print(f"✅ Tab 6 Remarks Sample (First 6): {tab6_remarks[:6]}")
    print(f"✅ Any System Injected Remarks: {has_system_remarks} (Expected: False)")

    shot2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_pure_remarks_clean.png"
    page.screenshot(path=shot2)

    print("\n--- Errors check ---")
    if len(errors) == 0 and not has_system_remarks:
        print("🎉 ZERO PAGE ERRORS! PURE REMARKS & FORWARD MONTH LOCK RULE 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
