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
PASSWORD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        # Track HTTP document navigations
        doc_reloads = 0
        def on_request(req):
            nonlocal doc_reloads
            if req.is_navigation_request() and req.resource_type == "document":
                doc_reloads += 1
                print(f"  [HTTP Document Fetch #{doc_reloads}] {req.url}")
        page.on("request", on_request)

        print("1. Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3500)
        print("Logged in. Current URL:", page.url)

        # Let's inspect the page title and workspaces
        print("\n2. Visiting /desk/my-business...")
        page.goto(f"{SITE_URL}/desk/my-business")
        page.wait_for_timeout(2500)
        
        my_business_screenshot = os.path.join(ARTIFACT_DIR, "clean_my_business_workspace.png")
        page.screenshot(path=my_business_screenshot)
        print(f"Saved My Business screenshot to: {my_business_screenshot}")

        print("\n3. Visiting /desk/procurement-management...")
        page.goto(f"{SITE_URL}/desk/procurement-management")
        page.wait_for_timeout(2500)

        procurement_screenshot = os.path.join(ARTIFACT_DIR, "clean_procurement_workspace.png")
        page.screenshot(path=procurement_screenshot)
        print(f"Saved Procurement screenshot to: {procurement_screenshot}")

        print(f"\nTotal HTTP Document loads: {doc_reloads}")
        browser.close()

if __name__ == "__main__":
    main()
