import os
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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

BRAIN_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\a49c8c70-7676-4c94-94f3-1677812d32e8"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 950})

    page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", PASSWORD)
    page.click(".btn-login")
    page.wait_for_timeout(4000)

    print("Navigating via frappe.set_route...")
    page.evaluate("frappe.set_route('procurement-order-picker')")
    page.wait_for_timeout(5000)

    print("Current URL:", page.url)
    screenshot_path = os.path.join(BRAIN_DIR, "debug_picker_page.png")
    page.screenshot(path=screenshot_path)
    print("Screenshot saved to", screenshot_path)

    browser.close()
