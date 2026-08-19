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

        http_doc_reloads = 0
        def on_response(resp):
            nonlocal http_doc_reloads
            if resp.request.resource_type == "document" and resp.status == 200:
                http_doc_reloads += 1
                print(f"[PAGE RELOAD #{http_doc_reloads}] {resp.url}")

        page.on("response", on_response)

        print("1. Login and go to /desk/home...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        page.goto(f"{SITE_URL}/desk/home")
        page.wait_for_timeout(3000)

        initial_docs = http_doc_reloads
        print(f"Loaded /desk/home. Initial doc count: {initial_docs}")

        # Test clicking top custom items
        top_items = [
            "采购管理",
            "仓库与库存",
            "会计与财务",
            "车油能耗管理",
            "企业合规中心"
        ]

        for item_name in top_items:
            print(f"\nClicking top custom menu item: '{item_name}'...")
            start_reloads = http_doc_reloads
            loc = page.locator("#ashan-cn-sidebar-container .ashan-group-title-link").filter(has_text=item_name).first
            if loc.is_visible():
                loc.click()
                page.wait_for_timeout(2000)
                diff = http_doc_reloads - start_reloads
                print(f"  URL after click: {page.url} | Document reloads: {diff}")
            else:
                print(f"  Item '{item_name}' not visible!")

        total_diff = http_doc_reloads - initial_docs
        print(f"\n=== TOTAL HTTP RELOADS ON TOP CUSTOM MENU: {total_diff} ===")

        browser.close()

if __name__ == "__main__":
    main()
