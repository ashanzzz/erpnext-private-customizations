import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USER', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

def test_person_filter():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})

        print("Logging in to Frappe Desk...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(2)

        print("Navigating to workbench...")
        page.goto(f"{SITE_URL}/desk/jizhong-hr-salary-workbench")
        page.wait_for_selector("#table-jz-payroll tbody tr", timeout=15000)
        time.sleep(2)

        # 1. Check all employees (23)
        rows_all = page.locator("#tbody-jz-payroll tr").count()
        print(f"All employees count: {rows_all}")

        # 2. Click 正式员工
        page.click("button.jz-segment-btn[data-mode='regular']")
        time.sleep(1)
        rows_reg = page.locator("#tbody-jz-payroll tr").count()
        print(f"Regular employees count: {rows_reg}")

        # 3. Click 其他员工
        page.click("button.jz-segment-btn[data-mode='other']")
        time.sleep(1)
        rows_other = page.locator("#tbody-jz-payroll tr").count()
        print(f"Other employees count: {rows_other}")

        page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\41d118a3-40e9-4f3f-9275-84276c35966c\live_jizhong_tab1_other_emps.png")

        # 4. Click 临时工
        page.click("button.jz-segment-btn[data-mode='temporary']")
        time.sleep(1)
        rows_temp = page.locator("#tbody-jz-payroll tr").count()
        print(f"Temporary employees count: {rows_temp}")

        browser.close()
        print("Test finished successfully!")

if __name__ == "__main__":
    test_person_filter()
