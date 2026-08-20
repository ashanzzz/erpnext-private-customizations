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

    res = page.evaluate("""() => {
        const sidebar = document.querySelector('.desk-sidebar');
        return {
            sidebar_html: sidebar ? sidebar.outerHTML : 'No .desk-sidebar found',
            boot_allowed_workspaces: window.frappe && window.frappe.boot ? window.frappe.boot.allowed_workspaces : null,
            boot_desk_pages: window.frappe && window.frappe.boot ? window.frappe.boot.desk_pages : null,
            frappe_workspace_pages: window.frappe && window.frappe.workspace && window.frappe.workspace.pages ? Object.keys(window.frappe.workspace.pages) : null
        };
    }""")

    print("Allowed Workspaces in Boot:", len(res.get('boot_allowed_workspaces') or []))
    for w in (res.get('boot_allowed_workspaces') or []):
        print(f"  - {w.get('name')} (title: {w.get('title')}, parent: {w.get('parent_page')}, module: {w.get('module')})")

    browser.close()
