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
REMOTE_URL = 'https://erpnext.335356119.xyz'
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

def test_site(url, name):
    with sync_playwright() as p:
        # Launch fresh incognito context with empty cache
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        print(f"\n--- Testing Fresh Login on {name} ({url}) ---")
        try:
            page.goto(f"{url}/login", timeout=15000)
            page.fill("#login_email", USERNAME)
            page.fill("#login_password", PASSWORD)
            page.click(".btn-login")
            page.wait_for_timeout(4000)

            print(f"Current URL after login on {name}: {page.url}")
            
            # Check presence of old legacy container vs native items
            has_old_dom = page.is_visible("#ashan-cn-sidebar-container")
            print(f"Old legacy container #ashan-cn-sidebar-container visible? {has_old_dom}")
            
            screenshot_path = rf"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\user_view_{name}.png"
            page.screenshot(path=screenshot_path)
            print(f"Saved screenshot of user view to {screenshot_path}")

        except Exception as e:
            print(f"Error testing {name}: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_site(SITE_URL, "local_site")
    test_site(REMOTE_URL, "remote_site")
