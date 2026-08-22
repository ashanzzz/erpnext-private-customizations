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
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click(".btn-login")
    page.wait_for_timeout(3500)

    page.goto(f"{SITE_URL}/desk/stock-and-inventory")
    page.wait_for_timeout(2500)

    res = page.evaluate("""() => {
        return {
            route: frappe.get_route(),
            route_str: frappe.get_route_str(),
            sidebar_title: frappe.app.sidebar.sidebar_title,
            boot_sidebar_keys: Object.keys(frappe.boot.workspace_sidebar_item),
            module_app: frappe.boot.module_app
        };
    }""")
    print("ROUTE INFO ON /desk/stock-and-inventory:\n", res)
    browser.close()
