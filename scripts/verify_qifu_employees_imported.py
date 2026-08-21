import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 950})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    print("Navigating to Ashan Employee Salary Profile list...")
    page.goto(f"{SITE_URL}/desk/ashan-employee-salary-profile")
    page.wait_for_selector(".frappe-list", state="visible", timeout=15000)
    time.sleep(3)

    shot_emp_list = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_employee_salary_profile_list.png"
    page.screenshot(path=shot_emp_list)
    print("Saved Employee List Shot:", shot_emp_list)

    # 点击打开第一个员工详情 (余莉影 A0001)
    first_row = page.locator(".list-row-container").first
    if first_row.is_visible():
        first_row.click()
        time.sleep(2)
        shot_emp_detail = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_employee_detail_view.png"
        page.screenshot(path=shot_emp_detail)
        print("Saved Employee Detail Shot:", shot_emp_detail)

    browser.close()

print("\n[ALL QIFU EMPLOYEE PROFILE SCREENSHOTS COMPLETED!]")
