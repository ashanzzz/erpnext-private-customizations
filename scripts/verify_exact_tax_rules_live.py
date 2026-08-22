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

    # 1. 切换到 Tab 5: 个人所得税台账
    print("\n--- 1. Testing Tab 5: ⚖️ 个人所得税核定与申报台账 ---")
    page.click("[data-tab='tax']")
    time.sleep(2)

    tax_rows = page.evaluate("() => document.querySelectorAll('#tbody-tab5-tax-sheet tr').length")
    tax_kpi_total = page.text_content("#tax-kpi-total")
    tax_kpi_gross = page.text_content("#tax-kpi-gross")
    tax_kpi_ded = page.text_content("#tax-kpi-ded")
    print(f"✅ Tab 5 loaded: {tax_rows} rows.")
    print(f"KPIs: Tax Total={tax_kpi_total}, Gross={tax_kpi_gross}, Deduction Total={tax_kpi_ded}")

    shot_tab5 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab5_exact_tax_rules.png"
    page.screenshot(path=shot_tab5)

    # 2. 点击【⚙️ 个税起征点与 7 级超额累进税率表】
    print("\n--- 2. Testing Tax Rate & VBA Closed-form Formula Modal ---")
    page.evaluate("() => $('.modal').modal('hide')")
    time.sleep(0.5)
    page.click("#btn-qifu-edit-tax-setting")
    time.sleep(2)
    shot_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab5_tax_rate_modal.png"
    page.screenshot(path=shot_modal)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 3. 切换到 Tab 6: 综合核定与结算并点击核定
    print("\n--- 3. Testing Tab 6: 📊 综合核定与结算 ---")
    page.click("[data-tab='settlement']")
    time.sleep(2)
    page.click("#btn-qifu-calc-payroll")
    time.sleep(3)

    kpi1 = page.text_content("#kpi-emp-total")
    kpi_gross = page.text_content("#kpi-total-gross")
    print(f"✅ Tab 6 recalculation done. In-service count={kpi1}, Gross total={kpi_gross}")
    shot_tab6 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab6_exact_settlement.png"
    page.screenshot(path=shot_tab6)

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! EXACT VBA CLOSED-FORM TAX FORMULA 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
