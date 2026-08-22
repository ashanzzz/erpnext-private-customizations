import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def test_direct_root_and_desk():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 950})
        page = context.new_page()

        # 1. 登录
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_timeout(4000)

        # 2. 模拟用户直接在地址栏访问根路径 / 或 /desk
        print("Testing direct navigation to / ...")
        page.goto(f"{SITE_URL}/")
        page.wait_for_timeout(3000)
        print(f"Current URL after /: {page.url}")

        print("Testing direct navigation to /desk ...")
        page.goto(f"{SITE_URL}/desk")
        page.wait_for_timeout(3000)
        print(f"Current URL after /desk: {page.url}")

        # 3. 模拟用户点击左上角 Desktop 下拉项
        print("Testing sidebar Desktop click ...")
        page.evaluate("() => frappe.set_route('/desk')")
        page.wait_for_timeout(2000)
        print(f"Current route after set_route('/desk'): {page.evaluate('() => frappe.get_route_str()')}")

        shot = os.path.join(ARTIFACT_DIR, "verify_direct_root_landing.png")
        page.screenshot(path=shot)
        print(f"Screenshot saved: {shot}")

        browser.close()

if __name__ == '__main__':
    test_direct_root_and_desk()
