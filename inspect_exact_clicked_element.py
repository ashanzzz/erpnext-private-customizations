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
        
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        
        item_info = page.eval_on_selector_all(".desk-sidebar .sidebar-item-container", """
            els => els.map(e => ({
                outerHTML: e.outerHTML,
                anchor_href: e.querySelector('a') ? e.querySelector('a').href : null,
                anchor_html: e.querySelector('a') ? e.querySelector('a').outerHTML : null
            }))
        """)
        
        print("=== EXACT SIDEBAR ITEM CONTAINER HTML ===")
        for idx, info in enumerate(item_info):
            print(f"Item #{idx}:")
            print("  Anchor HTML:", info['anchor_html'])
            print("  Anchor Href:", info['anchor_href'])

        browser.close()

if __name__ == "__main__":
    main()
