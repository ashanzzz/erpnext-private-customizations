import os
import json
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
SITE_URL = 'http://192.168.8.11:6888'
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Fresh context without cache
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        http_document_reloads = 0
        def on_response(response):
            nonlocal http_document_reloads
            if response.request.resource_type == "document" and response.status == 200:
                http_document_reloads += 1
                print(f"  [HTTP Document Fetch #{http_document_reloads}] {response.url}")

        page.on("response", on_response)

        print("=== STEP 1: Login to ERPNext ===")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3500)
        print(f"Logged in. Current URL: {page.url}")

        print("\n=== STEP 2: Navigate directly to http://192.168.8.11:6888/desk/home ===")
        page.goto(f"{SITE_URL}/desk/home")
        page.wait_for_timeout(3500)
        print(f"Final URL on /desk/home visit: {page.url}")
        
        home_screenshot = os.path.join(ARTIFACT_DIR, "live_acceptance_desk_home.png")
        page.screenshot(path=home_screenshot)
        print(f"Saved screenshot of /desk/home to: {home_screenshot}")

        print("\n=== STEP 3: Inspect Left Sidebar DOM Structure ===")
        has_custom_dom = page.is_visible("#ashan-cn-sidebar-container")
        print(f"Is custom top DOM #ashan-cn-sidebar-container visible? {has_custom_dom}")

        sidebar_items = page.eval_on_selector_all(".body-sidebar a, .desk-sidebar a", """
            els => els.map(e => ({
                text: e.innerText.trim(),
                href: e.getAttribute('href'),
                visible: e.offsetParent !== null
            }))
        """)
        print(f"Total sidebar links detected: {len(sidebar_items)}")
        for idx, item in enumerate(sidebar_items):
            safe_text = item['text'].encode('ascii', 'ignore').decode('ascii').replace('\n', ' ')
            print(f"  [{idx+1}] Text: '{safe_text}' | Href: '{item['href']}' | Visible: {item['visible']}")

        print("\n=== STEP 4: Live Click Acceptance Test (Clicking through sidebar items) ===")
        # Test clicking 5 different items and check for HTTP reloads & sidebar stability
        target_links = [
            "Procurement Management",
            "Stock and Inventory",
            "Accounting and Finance",
            "Vehicle Fuel Hub",
            "My Business"
        ]

        start_docs = http_document_reloads
        for target in target_links:
            loc = page.locator(".body-sidebar .sidebar-item-container").filter(has_text=target).locator("a").first
            if loc.is_visible():
                loc_text = loc.inner_text().strip().encode('ascii', 'ignore').decode('ascii')
                print(f"\nClicking sidebar item: '{loc_text}'...")
                before_click_docs = http_document_reloads
                loc.click()
                page.wait_for_timeout(1500)
                click_diff = http_document_reloads - before_click_docs
                print(f"  Result URL: {page.url}")
                print(f"  HTTP Full Reloads during click: {click_diff}")
            else:
                print(f"\nItem '{target}' was not visible in sidebar!")

        total_clicks_reloads = http_document_reloads - start_docs
        print(f"\n=== ACCEPTANCE SUMMARY ===")
        print(f"Total Full HTTP Document Reloads during sidebar clicks: {total_clicks_reloads}")

        final_screenshot = os.path.join(ARTIFACT_DIR, "live_acceptance_final_state.png")
        page.screenshot(path=final_screenshot)
        print(f"Saved final screenshot to: {final_screenshot}")

        browser.close()

if __name__ == "__main__":
    main()
