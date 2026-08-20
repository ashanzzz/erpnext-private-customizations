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

    sidebar_info = page.evaluate("""() => {
        const sidebar = document.querySelector('.desk-sidebar, .layout-side-section');
        const items = Array.from(document.querySelectorAll('.standard-sidebar-item, .sidebar-item-container, .desk-sidebar .item-anchor')).map(el => el.innerText.trim());
        
        let bootPages = [];
        if (window.frappe && window.frappe.boot) {
            bootPages = window.frappe.boot.sidebar_pages || [];
        }
        
        return {
            domItems: items,
            bootSidebarPages: bootPages,
            workspaceList: window.frappe && window.frappe.workspaces ? Object.keys(window.frappe.workspaces) : []
        };
    }""")

    print("=== SIDEBAR DOM ITEMS ===")
    for item in sidebar_info.get('domItems', []):
        print(f" - {item}")

    print("\n=== BOOT SIDEBAR PAGES ===")
    print(json.dumps(sidebar_info.get('bootSidebarPages'), indent=2, ensure_ascii=False))

    browser.close()
