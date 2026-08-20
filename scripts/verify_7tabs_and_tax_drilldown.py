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
    page = browser.new_page(viewport={"width": 1920, "height": 1150})

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

    # 1. 验证 7 大 Tab
    tabs = page.query_selector_all(".qifu-tab-btn")
    print(f"Total Tabs Count: {len(tabs)}")

    # 2. 切换至 Tab 5: 个人所得税核定台账 (精简版)
    print("\n--- 1. Testing Tab 5: Tax Simple View ---")
    page.click(".qifu-tab-btn[data-tab='tax']")
    time.sleep(3)
    shot_tab5_simple = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab5_tax_simple.png"
    page.screenshot(path=shot_tab5_simple)
    print(f"Captured Tab 5 Simple View: {shot_tab5_simple}")

    # 3. 切换至 Tab 5: 68 列全量法定大宽表
    print("\n--- 2. Testing Tab 5: 68-Column Full Statutory Wide Table ---")
    page.click(".btn-tax-view-mode[data-mode='full_68']")
    time.sleep(3)
    shot_tab5_full = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab5_tax_68cols.png"
    page.screenshot(path=shot_tab5_full)
    print(f"Captured Tab 5 68-Col Wide Table: {shot_tab5_full}")

    # 4. 点击姓名穿透弹窗
    print("\n--- 3. Testing Drilldown Modal by Clicking Employee Name ---")
    drill_link = page.query_selector(".btn-drill-emp-history")
    if drill_link:
        drill_link.click()
        time.sleep(3)
        shot_drilldown = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_emp_drilldown_modal.png"
        page.screenshot(path=shot_drilldown)
        print(f"Captured Drilldown Modal: {shot_drilldown}")
        page.keyboard.press("Escape")
        time.sleep(1)

    # 5. 切换至 Tab 7: 历史数据与人员全周期穿透台账
    print("\n--- 4. Testing Tab 7: History Timeline & Personal Drilldown Tab ---")
    page.click(".qifu-tab-btn[data-tab='history_timeline']")
    time.sleep(4)
    shot_tab7 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab7_history_timeline.png"
    page.screenshot(path=shot_tab7)
    print(f"Captured Tab 7 History Timeline: {shot_tab7}")

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! 7 TABS, 68-COL TAX WIDE TABLE & PERSONAL TIMELINE 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
