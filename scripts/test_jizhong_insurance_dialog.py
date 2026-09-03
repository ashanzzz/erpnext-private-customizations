import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USER', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

def test_jizhong_insurance_dialog():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})

        print("Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(2)

        print("Navigating to workbench...")
        page.goto(f"{SITE_URL}/desk/jizhong-hr-salary-workbench")
        page.wait_for_selector("#table-jz-payroll tbody tr", timeout=15000)
        time.sleep(1)

        print("Opening Tab 6...")
        page.click(".jz-tab-btn[data-tab='insurance']")
        time.sleep(2)

        print("Clicking '修改吉众社保公积金费率'...")
        page.click("#btn-jz-edit-insurance")
        time.sleep(1)

        page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\41d118a3-40e9-4f3f-9275-84276c35966c\live_jizhong_tab6_insurance_dialog.png")
        print("Captured modal screenshot!")
        browser.close()

if __name__ == "__main__":
    test_jizhong_insurance_dialog()
