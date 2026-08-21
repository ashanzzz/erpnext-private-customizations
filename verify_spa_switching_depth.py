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
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        http_doc_fetches = 0
        def on_request(req):
            nonlocal http_doc_fetches
            if req.is_navigation_request() and req.resource_type == "document":
                http_doc_fetches += 1
                print(f"  [HTTP Document Fetch #{http_doc_fetches}] {req.url}")
        page.on("request", on_request)

        print("1. Login...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click(".btn-login")
        page.wait_for_timeout(3500)
        print("Logged in. URL:", page.url)

        base_fetches = http_doc_fetches
        print(f"\nInitial page load document fetches: {base_fetches}")
        print("--- Starting Pure SPA Navigation Test ---")

        # 1. Click on Sidebar item: Procurement Management
        print("\nStep 1: Clicking sidebar link 'Procurement Management'...")
        page.click("a[href='/desk/procurement-management'], .sidebar-item-a:has-text('Procurement Management')")
        page.wait_for_timeout(2000)
        print("URL:", page.url)

        # 2. Click on Sidebar item: Stock and Inventory
        print("\nStep 2: Clicking sidebar link 'Stock and Inventory'...")
        page.click("a[href='/desk/stock-and-inventory'], .sidebar-item-a:has-text('Stock and Inventory')")
        page.wait_for_timeout(2000)
        print("URL:", page.url)

        # 3. Click on Shortcut: 物料主数据 (Item List)
        print("\nStep 3: Clicking shortcut card '物料主数据'...")
        page.click(".shortcut-widget-box:has-text('物料主数据'), a[href='/desk/item']")
        page.wait_for_timeout(2500)
        print("URL (in Item List):", page.url)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "live_spa_item_list.png"))

        # 4. Click Back to My Business via sidebar
        print("\nStep 4: Clicking sidebar link 'My Business'...")
        page.click("a[href='/desk/my-business'], .sidebar-item-a:has-text('My Business')")
        page.wait_for_timeout(2000)
        print("URL (back to My Business):", page.url)

        new_fetches = http_doc_fetches - base_fetches
        print("\n==================================================")
        print(f"Total Full HTTP Document Reloads during navigation: {new_fetches}")
        print(f"SPA Status: {'100% PURE SPA (0 Reloads) - PASSED' if new_fetches == 0 else 'FAILED (Reload occurred)'}")
        print("==================================================")

        browser.close()

if __name__ == "__main__":
    main()
