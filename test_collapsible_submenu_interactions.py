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

ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # 1. Login
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click(".btn-login")
    page.wait_for_timeout(3500)

    # 2. Go to /desk/my-business
    page.goto(f"{SITE_URL}/desk/my-business")
    page.wait_for_timeout(3000)

    # Capture initial sidebar state
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "submenu_initial_state.png"))

    # 3. Inspect Section Breaks and Nested Items in DOM
    section_items = page.locator(".section-item, .standard-sidebar-item.section-break, .sidebar-child-item").all_text_contents()
    print("DOM Sidebar Sections & Children:", section_items)

    # 4. Click a Section Break if collapsed to test toggle
    headers = page.locator(".section-break, .sidebar-item-container[data-id='仓储与库存'], .sidebar-item-container[data-id='车油能耗中心']").all()
    print(f"Found {len(headers)} interactive section headers.")
    
    # 5. Capture close-up of sidebar
    sidebar_elem = page.locator(".body-sidebar")
    if sidebar_elem.count() > 0:
        sidebar_elem.first.screenshot(path=os.path.join(ARTIFACT_DIR, "submenu_sidebar_closeup.png"))

    # 6. Click on a secondary menu item: 物料主数据
    item_link = page.locator(".body-sidebar a:has-text('物料主数据')")
    if item_link.count() > 0:
        print("Clicking secondary menu link: 物料主数据...")
        item_link.first.click()
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "submenu_clicked_item_list.png"))

    print("Submenu testing completed!")
    browser.close()
