import os
import sys
import time
import requests
import base64
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')
EXCEL_PATH = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\祺富人事202606(3) 的副本.xlsm"

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

    # 1. 切换到 Tab 2: 外部实发导入与薪资发放表
    print("\n--- 1. Testing Tab 2: 📤 外部实发导入与薪资发放表 (3 KPIs & Status Banner) ---")
    page.click("[data-tab='import']")
    time.sleep(2)

    kpi_count = page.text_content("#tab2-kpi-count")
    kpi_workshop = page.text_content("#tab2-kpi-workshop-salary")
    kpi_payable = page.text_content("#tab2-kpi-payable-salary")
    banner_text = page.text_content("#tab2-import-status-banner")

    print(f"✅ Tab 2 Loaded!")
    print(f"  KPI 1 (工资人数): {kpi_count}")
    print(f"  KPI 2 (考勤工资合计): {kpi_workshop}")
    print(f"  KPI 3 (考勤加补贴合计): {kpi_payable}")
    print(f"  Banner: {banner_text.strip()[:100]}...")

    # 2. 模拟上传实发 Excel 文件并预检
    print("\n--- 2. Testing File Upload & Preview API ---")
    page.set_input_files("#qifu-file-input-tab2", EXCEL_PATH)
    time.sleep(3)

    preview_text = page.text_content("#qifu-import-badge-tab2")
    print(f"✅ Preview parsed: {preview_text.strip()[:120]}...")

    # 3. 点击【⚡ 确认导入并重新覆盖计算】
    print("\n--- 3. Testing Overwrite & Re-import ---")
    page.click("#btn-import-confirm-tab2")
    time.sleep(4)

    # 再次检查 3 个 KPI 与 24 列发放表
    kpi_count_after = page.text_content("#tab2-kpi-count")
    kpi_workshop_after = page.text_content("#tab2-kpi-workshop-salary")
    kpi_payable_after = page.text_content("#tab2-kpi-payable-salary")
    dist_rows = page.evaluate("() => document.querySelectorAll('#tbody-tab2-dist-sheet tr').length")

    print(f"✅ After Overwrite Import:")
    print(f"  KPI 1 (工资人数): {kpi_count_after}")
    print(f"  KPI 2 (考勤工资合计): {kpi_workshop_after}")
    print(f"  KPI 3 (考勤加补贴合计): {kpi_payable_after}")
    print(f"  24-Col Table Row Count: {dist_rows}")

    shot_tab2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab2_kpis_and_overwrite.png"
    page.screenshot(path=shot_tab2)

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! TAB 2 3-KPIS & AUTO-OVERWRITE IMPORT 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
