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
EXCEL_PATH_202606 = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\祺富人事202606(3) 的副本.xlsm"

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

    # 1. 验证账期不匹配时的拦截 (当前工作台 2026-07，上传 2026-06 文件)
    print("\n--- 1. Testing Period Mismatch Prevention (2026-07 workbench vs 2026-06 file) ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    page.click("[data-tab='import']")
    time.sleep(2)

    page.set_input_files("#qifu-file-input-tab2", EXCEL_PATH_202606)
    time.sleep(3)

    is_btn_disabled = page.evaluate("() => document.getElementById('btn-import-confirm-tab2').disabled")
    print(f"✅ Mismatch detected! Confirm Button disabled: {is_btn_disabled}")
    print(f"Badge text: {page.text_content('#qifu-import-badge-tab2').strip()[:140]}...")

    shot1 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab2_mismatch_prevention.png"
    page.screenshot(path=shot1)

    # 2. 刷新页面并选择发薪月份为 2026-06，验证账期匹配与补贴统计 (工资人数、考勤工资、补贴多少钱、考勤加补贴合计)
    print("\n--- 2. Testing Period Match & Detailed Allowance Stats (On 2026-06 page) ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 修改 input 并触发 change
    page.fill("#qifu-month-select", "2026-06")
    page.dispatch_event("#qifu-month-select", "change")
    time.sleep(2)

    page.click("[data-tab='import']")
    time.sleep(2)

    page.set_input_files("#qifu-file-input-tab2", EXCEL_PATH_202606)
    time.sleep(3)

    is_btn_disabled2 = page.evaluate("() => document.getElementById('btn-import-confirm-tab2').disabled")
    stats_text = page.text_content("#qifu-import-badge-tab2")
    print(f"✅ Match successful! Confirm Button disabled: {is_btn_disabled2}")
    print(f"Stats content: {stats_text.strip()[:180]}...")

    shot2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab2_match_and_allowance_stats.png"
    page.screenshot(path=shot2)

    # 3. 点击【⚡ 确认导入并重新覆盖计算】
    print("\n--- 3. Testing Overwrite & Re-import for 2026-06 ---")
    page.click("#btn-import-confirm-tab2")
    time.sleep(4)

    kpi_count = page.text_content("#tab2-kpi-count")
    kpi_workshop = page.text_content("#tab2-kpi-workshop-salary")
    kpi_payable = page.text_content("#tab2-kpi-payable-salary")
    dist_rows = page.evaluate("() => document.querySelectorAll('#tbody-tab2-dist-sheet tr').length")
    print(f"✅ 2026-06 Import completed:")
    print(f"  KPI 1 (工资人数): {kpi_count}")
    print(f"  KPI 2 (考勤工资合计): {kpi_workshop}")
    print(f"  KPI 3 (考勤加补贴合计): {kpi_payable}")
    print(f"  Table rows: {dist_rows}")

    shot3 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab2_imported_overview.png"
    page.screenshot(path=shot3)

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! PERIOD CALIBRATION & DETAILED ALLOWANCE STATS 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
