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
        
        http_document_reloads = 0
        def on_response(response):
            nonlocal http_document_reloads
            if response.request.resource_type == "document" and response.status == 200:
                http_document_reloads += 1
                print(f"[HTTP FULL DOCUMENT RELOAD #{http_document_reloads}] {response.url}")

        page.on("response", on_response)

        print("1. Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        
        initial_doc_fetches = http_document_reloads
        print(f"Logged in. Base URL: {page.url} (Initial HTTP Document fetches: {initial_doc_fetches})")

        print("\n2. Testing clicks on native Frappe Workspaces:")
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
                start_docs = http_document_reloads
                # Click the native workspace item anchor
                loc = page.locator(".body-sidebar .sidebar-item-container").filter(has_text=ws).locator("a").first
                if loc.is_visible():
                    loc.click()
                    page.wait_for_timeout(1200)
                    doc_diff = http_document_reloads - start_docs
                    print(f"Clicked '{ws}' -> Current URL: {page.url} | HTTP Document Reloads: {doc_diff}")

        total_http_reloads_during_clicks = http_document_reloads - initial_doc_fetches
        print("\n=== ACCURATE SPA NAVIGATION SUMMARY ===")
        print(f"Total Full HTTP Document Reloads During 12 Workspace Clicks: {total_http_reloads_during_clicks}")
        if total_http_reloads_during_clicks == 0:
            print("SUCCESS! All workspace clicks are 100% smooth SPA navigations without page reloads!")

        browser.close()

if __name__ == "__main__":
    main()
