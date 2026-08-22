import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.click(".app-switcher-menu, .navbar-brand, .sidebar-header, .app-switcher, .dropdown-item")
    time.sleep(0.5)

    # 悬停 Display
    page.hover(".menu-item-title:has-text('Display')")
    time.sleep(0.5)

    # 悬停 Help
    page.hover(".menu-item-title:has-text('Help')")
    time.sleep(0.5)

    submenus = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('.context-menu, .frappe-menu, .popover, .dropdown-menu'));
        return els.map(e => e.innerText);
    }""")
    print("--- ALL MENUS ---")
    for s in submenus:
        print(s)
        print("="*40)

    browser.close()
