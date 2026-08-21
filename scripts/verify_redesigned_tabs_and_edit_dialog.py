import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1750, "height": 1100})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#table-qifu-payroll", state="visible", timeout=15000)
    time.sleep(2)

    # 1. 截图 Tab 1 重构后的明细表（职位补贴与租房补贴单独成列）
    shot_tab1 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_redesigned_tab1.png"
    page.screenshot(path=shot_tab1)
    print("Saved Tab 1 Redesign Shot:", shot_tab1)

    # 2. 切换到 Tab 2 员工档案 (母表)
    print("Switching to Tab 2 (Employees)...")
    page.click(".qifu-tab-btn[data-tab='employees']")
    page.wait_for_selector("#tbody-qifu-emp tr", state="visible", timeout=10000)
    time.sleep(1)

    shot_tab2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_tab2_master_employees.png"
    page.screenshot(path=shot_tab2)
    print("Saved Tab 2 Master Employees Shot:", shot_tab2)

    # 3. 点击第一位员工的 ✏️ 修改档案 按钮
    print("Clicking ✏️ 修改档案...")
    page.click("#tbody-qifu-emp tr:first-child .btn-qifu-edit-emp")
    page.wait_for_selector(".modal-title:has-text('修改员工薪酬档案')", state="visible", timeout=10000)
    time.sleep(1)

    shot_edit_dialog = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_employee_edit_dialog.png"
    page.screenshot(path=shot_edit_dialog)
    print("Saved Employee Edit Dialog Shot:", shot_edit_dialog)

    browser.close()

print("\n[ALL VERIFICATION SHOTS CAPTURED!]")
