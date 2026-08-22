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

        loaded_scripts = []
        page.on("request", lambda req: loaded_scripts.append(req.url) if req.resource_type == "script" else None)

        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        page.goto(f"{SITE_URL}/desk/home")
        page.wait_for_timeout(3000)

        print("=== ALL SCRIPT URLS LOADED ON /desk/home ===")
        for s in loaded_scripts:
            print("-", s)

        # Check stack trace / origin of init_ashan_cn_sidebar
        fn_info = page.evaluate("""
            () => {
                return {
                    init_ashan_cn_sidebar: window.init_ashan_cn_sidebar ? window.init_ashan_cn_sidebar.toString().slice(0, 300) : null,
                    custom_container_html: document.querySelector('#ashan-cn-sidebar-container') ? document.querySelector('#ashan-cn-sidebar-container').outerHTML.slice(0, 300) : null
                };
            }
        """)

        print("\n=== FUNCTION & CONTAINER INFO ===")
        print("window.init_ashan_cn_sidebar string:", repr(fn_info['init_ashan_cn_sidebar']))

        browser.close()

if __name__ == "__main__":
    main()
