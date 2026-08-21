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
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click(".btn-login")
    page.wait_for_timeout(3500)

    page.goto(f"{SITE_URL}/desk/my-business")
    page.wait_for_timeout(3000)

    debug = page.evaluate("""() => {
        return {
            sidebar_items: window.frappe && window.frappe.workspace && window.frappe.workspace.sidebar_items ? window.frappe.workspace.sidebar_items : null,
            boot_sidebar_items: window.frappe && window.frappe.boot ? window.frappe.boot.sidebar_pages : null,
            module_page_map: window.frappe && window.frappe.boot ? window.frappe.boot.module_page_map : null,
            sidebar_categories: Array.from(document.querySelectorAll('.desk-sidebar .standard-sidebar-section')).map(s => {
                return {
                    header: s.querySelector('.sidebar-section-header, .standard-sidebar-label')?.innerText,
                    items: Array.from(s.querySelectorAll('.sidebar-item-container, .item-anchor')).map(a => a.innerText.trim())
                };
            })
        };
    }""")

    print(json.dumps(debug, indent=2, ensure_ascii=False))
    browser.close()
