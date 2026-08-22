import os
import time
from playwright.sync_api import sync_playwright

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def test_fresh_uncached_desk():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. Login via /login
        print("1. Logging in via /login...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button.btn-login")
        page.wait_for_timeout(3000)

        # 2. Visit /desk
        print("2. Visiting /desk...")
        page.goto(f"{SITE_URL}/desk")
        page.wait_for_timeout(3000)
        print(f"   Landed on URL: {page.url}")

        # 3. Check for any 'not found' or error modal
        modals = page.locator(".modal:visible").all_text_contents()
        print(f"3. Visible modals on /desk: {modals}")
        assert not any("not found" in m.lower() or "未找到" in m for m in modals), f"Error modal detected: {modals}"

        # 4. Take screenshot
        shot_path = os.path.join(ARTIFACT_DIR, "live_acceptance_fresh_uncached_desk.png")
        page.screenshot(path=shot_path)
        print(f"   Saved fresh uncached /desk screenshot: {shot_path}")

        # 5. Visit /desk/home directly
        print("5. Visiting /desk/home directly...")
        page.goto(f"{SITE_URL}/desk/home")
        page.wait_for_timeout(3000)
        modals_home = page.locator(".modal:visible").all_text_contents()
        print(f"   Visible modals on /desk/home: {modals_home}")
        assert not any("not found" in m.lower() or "未找到" in m for m in modals_home), f"Error modal detected on /desk/home: {modals_home}"

        shot_home = os.path.join(ARTIFACT_DIR, "live_acceptance_fresh_uncached_desk_home.png")
        page.screenshot(path=shot_home)
        print(f"   Saved fresh uncached /desk/home screenshot: {shot_home}")

        browser.close()

if __name__ == '__main__':
    test_fresh_uncached_desk()
