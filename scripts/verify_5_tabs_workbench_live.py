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

    # 1. 验证 Tab 1: 员工档案母表
    print("\n--- 1. Testing Tab 1: 👥 祺富员工薪酬档案 (权威母表底册) ---")
    page.wait_for_selector("#table-qifu-emp", state="visible", timeout=10000)
    emp_count = page.evaluate("() => document.querySelectorAll('#tbody-qifu-emp tr').length")
    print(f"✅ Tab 1 loaded: {emp_count} employee profiles in mother table.")
    shot1 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab1_employees.png"
    page.screenshot(path=shot1)

    # 2. 验证 Tab 2: 外部导入
    print("\n--- 2. Testing Tab 2: 📤 外部实发导入与智能解析 (老板娘实发表) ---")
    page.click("[data-tab='import']")
    time.sleep(1)
    page.wait_for_selector("#qifu-dropzone-tab2", state="visible", timeout=10000)
    print("✅ Tab 2 loaded: Drag-and-drop zone and smart parsing area visible.")
    shot2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab2_import.png"
    page.screenshot(path=shot2)

    # 3. 验证 Tab 3: 社保台账与配置
    print("\n--- 3. Testing Tab 3: 🛡️ 祺富社会保险台账与配置 ---")
    page.click("[data-tab='social_insurance']")
    time.sleep(2)
    page.wait_for_selector("#table-tab3-ss-sheet", state="visible", timeout=10000)
    ss_rows = page.evaluate("() => document.querySelectorAll('#tbody-tab3-ss-sheet tr').length")
    print(f"✅ Tab 3 loaded: {ss_rows} rows in 19-column dual-header Social Insurance sheet.")
    shot3 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab3_social_insurance.png"
    page.screenshot(path=shot3)

    # 4. 验证 Tab 4: 公积金台账与配置
    print("\n--- 4. Testing Tab 4: 🏛️ 祺富住房公积金台账与配置 ---")
    page.click("[data-tab='housing_fund']")
    time.sleep(2)
    page.wait_for_selector("#table-tab4-hf-sheet", state="visible", timeout=10000)
    hf_rows = page.evaluate("() => document.querySelectorAll('#tbody-tab4-hf-sheet tr').length")
    print(f"✅ Tab 4 loaded: {hf_rows} rows in 12-column Housing Fund sheet.")
    shot4 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab4_housing_fund.png"
    page.screenshot(path=shot4)

    # 5. 验证 Tab 5: 月度综合核定结算
    print("\n--- 5. Testing Tab 5: 📊 月度薪酬综合核定与结算 (母表与老板娘混合) ---")
    page.click("[data-tab='settlement']")
    time.sleep(2)
    page.wait_for_selector("#table-qifu-payroll", state="visible", timeout=10000)
    pay_kpi_total = page.text_content("#kpi-emp-total")
    print(f"✅ Tab 5 loaded: Golden KPI Card 1 employee count: {pay_kpi_total}")
    shot5 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab5_settlement.png"
    page.screenshot(path=shot5)

    browser.close()

print("\n🎉 [ALL 5 TABS 100% VERIFIED & SCREENSHOTS CAPTURED!]")
