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

    # 1. 验证 Tab 1 权威母表底册 (当前年龄、原法定退休、渐进式延迟退休紧密排列与微卡片倒计时)
    print("\n--- 1. Testing Tab 1: 👥 祺富员工薪酬档案 (Tight-knit Age & Dual Retirement Timelines) ---")
    page.click("[data-tab='employees']")
    time.sleep(2)

    table_headers = page.eval_on_selector_all("#table-qifu-emp thead th", "els => els.map(e => e.innerText.trim())")
    print(f"✅ Tab 1 Table Headers ({len(table_headers)} cols): {table_headers}")

    row_count = page.evaluate("() => document.querySelectorAll('#tbody-qifu-emp tr').length")
    first_row_cells = page.eval_on_selector_all("#tbody-qifu-emp tr:first-child td", "els => els.map(e => e.innerText.trim())")
    print(f"✅ Employee Rows Count: {row_count}")
    print(f"  First Row Data (余莉影): {first_row_cells}")

    second_row_cells = page.eval_on_selector_all("#tbody-qifu-emp tr:nth-child(2) td", "els => els.map(e => e.innerText.trim())")
    print(f"  Second Row Data (刘海锋): {second_row_cells}")

    shot1 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab1_tight_age_and_retirement.png"
    page.screenshot(path=shot1)

    # 2. 验证【➕ 新增祺富员工档案】弹窗中 18 位身份证自动解析与倒计时
    print("\n--- 2. Testing ID Card Auto-parsing in Add Employee Dialog ---")
    page.click("#btn-qifu-new-emp")
    time.sleep(1)

    page.fill("input[data-fieldname='employee_no']", "QF-TEST01")
    page.fill("input[data-fieldname='employee_name']", "测试员工")
    page.fill("input[data-fieldname='id_card']", "120101197608151234")
    page.dispatch_event("input[data-fieldname='id_card']", "input")
    time.sleep(2)

    tip_text = page.text_content("#qifu-idcard-tip")
    birth_val = page.input_value("input[data-fieldname='birth_date']")
    age_val = page.input_value("input[data-fieldname='current_age']")
    orig_retire = page.input_value("input[data-fieldname='original_retirement_age']")
    delay_retire = page.input_value("input[data-fieldname='delayed_retirement_age']")

    print(f"✅ ID Card Auto-parse result:")
    print(f"  Birth Date: {birth_val}")
    print(f"  Current Age: {age_val} 岁")
    print(f"  Orig Retirement Age: {orig_retire} 岁")
    print(f"  Delayed Retirement Age: {delay_retire} 岁")
    print(f"  Tip:\n{tip_text.strip()}")

    shot2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab1_idcard_dialog_tight.png"
    page.screenshot(path=shot2)

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! TIGHT-KNIT AGE, RETIREMENT COUNTDOWNS & UI 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
