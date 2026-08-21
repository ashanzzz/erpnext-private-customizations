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

    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/employee-salary-workbench")
    page.wait_for_selector("#emp-data-table", state="visible", timeout=15000)
    time.sleep(2)

    # 勾选前两位员工
    checks = page.locator(".emp-row-check")
    checks.nth(0).check()
    checks.nth(1).check()
    time.sleep(1)

    # 点击批量修改参数
    page.click("#btn-open-batch-modal")
    time.sleep(1)
    page.wait_for_selector(".modal-dialog", state="visible")

    shot_batch_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_employee_batch_modal_open.png"
    page.screenshot(path=shot_batch_modal)
    print("Saved Batch Modal Shot:", shot_batch_modal)

    browser.close()
