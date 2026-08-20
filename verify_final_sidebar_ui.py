import os
import json
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
SITE_URL = 'http://192.168.8.11:6888'
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        print("1. Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3500)
        print("Logged in. Current URL:", page.url)

        # Check if legacy top DOM is visible
        has_legacy = page.is_visible("#ashan-cn-sidebar-container")
        print(f"Legacy container #ashan-cn-sidebar-container visible? {has_legacy}")

        screenshot_path = os.path.join(ARTIFACT_DIR, "final_verified_desk_sidebar.png")
        page.screenshot(path=screenshot_path)
        print(f"Saved screenshot to: {screenshot_path}")

        print("\n2. Navigating to /desk/home...")
        page.goto(f"{SITE_URL}/desk/home")
        page.wait_for_timeout(3500)
        print("URL on /desk/home:", page.url)

        has_legacy_home = page.is_visible("#ashan-cn-sidebar-container")
        print(f"Legacy container on /desk/home visible? {has_legacy_home}")

        home_screenshot_path = os.path.join(ARTIFACT_DIR, "final_verified_desk_home.png")
        page.screenshot(path=home_screenshot_path)
        print(f"Saved screenshot to: {home_screenshot_path}")

        browser.close()

if __name__ == "__main__":
    main()
