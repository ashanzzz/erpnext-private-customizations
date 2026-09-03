import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USER', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

def test_jizhong_insurance_and_nav():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})

        print("Logging in to Frappe Desk...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(3)

        print("Navigating to workbench...")
        page.goto(f"{SITE_URL}/desk/jizhong-hr-salary-workbench")
        page.wait_for_selector("#table-jz-payroll tbody tr", timeout=15000)
        time.sleep(1)

        print("Clicking Tab 6: 社保公积金配置...")
        page.click(".jz-tab-btn[data-tab='insurance']")
        time.sleep(2)

        # Check values in Tab 6
        injury = page.locator("#jz-ins-injury").inner_text()
        doc_tip = page.locator("#jz-ins-docname-tip").inner_text()
        print(f"Tab 6 loaded successfully: injury rate = {injury}, tip = {doc_tip}")

        page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\41d118a3-40e9-4f3f-9275-84276c35966c\live_jizhong_tab6_insurance_dynamic.png")

        browser.close()
        print("Test passed successfully!")

if __name__ == "__main__":
    test_jizhong_insurance_and_nav()
