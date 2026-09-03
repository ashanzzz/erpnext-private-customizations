import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USER', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

def verify_sidebar():
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

        # Look for text in body
        content = page.content()
        print("Page contains '祺富人事薪酬与用工':", "祺富人事薪酬与用工" in content)
        print("Page contains '吉众人事薪酬与用工':", "吉众人事薪酬与用工" in content)

        page.screenshot(path=r"C:\Users\ashan\.gemini\antigravity\brain\41d118a3-40e9-4f3f-9275-84276c35966c\live_sidebar_qifu_jizhong_split.png", full_page=False)
        print("Saved sidebar screenshot!")
        browser.close()

if __name__ == "__main__":
    verify_sidebar()
