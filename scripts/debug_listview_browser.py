import os
import time
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

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})

    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(3)

    page.goto(f"{SITE_URL}/desk/purchase-order")
    time.sleep(3)

    # 打印浏览器控制台中关于 listview_settings 的信息
    res = page.evaluate("""() => {
        return {
            has_ashan: typeof ashan !== 'undefined',
            has_doc_details: typeof ashan !== 'undefined' && !!ashan.doc_details,
            po_settings: frappe.listview_settings['Purchase Order'],
            rendered_html: document.querySelector('.frappe-list') ? document.querySelector('.frappe-list').innerHTML.substring(0, 1000) : 'none'
        };
    }""")
    print("Evaluate Result:", res)

    browser.close()
