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

        print("1. Logging in and going to /app/my-business...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(2000)
        
        # Navigate to /app/my-business
        page.goto(f"{SITE_URL}/app/my-business")
        page.wait_for_timeout(3000)
        
        initial_reloads = nav_count
        print(f"Current Base URL: {page.url} (Initial reloads: {initial_reloads})")

        print("\n2. Testing Sidebar Workspaces Clicks under /app/ Route...")
        workspaces = [
            "Procurement Management",
            "Stock and Inventory",
            "Accounting and Finance",
            "Vehicle Fuel Hub",
            "Company Compliance Center",
            "My Business"
        ]

        for round_num in range(1, 3):
            print(f"\n--- Click Round {round_num} ---")
            for ws in workspaces:
                loc = page.locator(".desk-sidebar .sidebar-item-container, .body-sidebar .sidebar-item-container").filter(has_text=ws).first
                if not loc.is_visible():
                    loc = page.locator(f":text('{ws}')").first

                if loc.is_visible():
                    loc.click()
                    page.wait_for_timeout(1000)
                    print(f"Clicked '{ws}' -> Current URL: {page.url}")
                else:
                    print(f"WARNING: Workspace link '{ws}' not visible!")

        total_clicks_reloads = nav_count - initial_reloads
        print("\n=== TEST RESULTS SUMMARY ===")
        print(f"Total Page Reloads During 12 Sidebar Clicks on /app/ route: {total_clicks_reloads}")
        if total_clicks_reloads == 0:
            print("SUCCESS! 100% Pure Native SPA Navigation! ZERO Page Reloads on /app/ route!")
        else:
            print(f"FAILURE! Detected {total_clicks_reloads} full page reloads.")

        browser.close()

if __name__ == "__main__":
    main()
