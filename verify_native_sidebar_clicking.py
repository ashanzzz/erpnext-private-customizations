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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        nav_count = 0
        def on_nav(frame):
            nonlocal nav_count
            if frame == page.main_frame:
                nav_count += 1
                print(f"[FULL PAGE RELOAD #{nav_count}] {frame.url}")

        page.on("framenavigated", on_nav)

        print("1. Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        
        initial_reloads = nav_count
        print(f"Logged in. Base URL: {page.url} (Initial reloads: {initial_reloads})")

        print("\n2. Checking if legacy DOM container #ashan-cn-sidebar-container is present:")
        is_legacy_present = page.is_visible("#ashan-cn-sidebar-container")
        print(f"Legacy container present? {is_legacy_present}")

        print("\n3. Testing 12 consecutive clicks on native Workspaces:")
        native_workspaces = [
            "Procurement Management",
            "Stock and Inventory",
            "Accounting and Finance",
            "Vehicle Fuel Hub",
            "Company Compliance Center",
            "My Business"
        ]

        for round_num in range(1, 3):
            print(f"\n--- Round {round_num} ---")
            for ws in native_workspaces:
                start_reloads = nav_count
                loc = page.locator(".body-sidebar .sidebar-item-container").filter(has_text=ws).first
                if loc.is_visible():
                    loc.click()
                    page.wait_for_timeout(1200)
                    click_reloads = nav_count - start_reloads
                    print(f"Clicked '{ws}' -> URL: {page.url} | Reloads during click: {click_reloads}")
                else:
                    print(f"WARNING: Native workspace '{ws}' not visible!")

        total_click_reloads = nav_count - initial_reloads
        print("\n=== VERIFICATION RESULT ===")
        print(f"Legacy DOM container eliminated? {not is_legacy_present}")
        print(f"Total Full Page Reloads During 12 Native Clicks: {total_click_reloads}")

        screenshot_path = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\native_clean_sidebar_verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Saved screenshot to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    main()
