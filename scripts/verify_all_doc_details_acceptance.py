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
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def verify_all_lists():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 950})
        page = context.new_page()

        # 1. 登录
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", state="visible")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(3)

        targets = [
            ("Purchase Order", "purchase-order", "live_acceptance_purchase_order_list.png"),
            ("Material Request", "material-request", "live_acceptance_material_request_list.png"),
            ("Purchase Receipt", "purchase-receipt", "live_acceptance_purchase_receipt_list.png"),
            ("Purchase Invoice", "purchase-invoice", "live_acceptance_purchase_invoice_list.png"),
            ("Reimbursement Request", "reimbursement-request", "live_acceptance_reimbursement_request_list.png"),
        ]

        for dt_label, route, filename in targets:
            print(f"Navigating to {dt_label} list ({route})...")
            page.goto(f"{SITE_URL}/desk/{route}")
            time.sleep(3)
            page.wait_for_selector(".frappe-list", timeout=10000)
            time.sleep(2)
            ss_path = os.path.join(ARTIFACT_DIR, filename)
            page.screenshot(path=ss_path)
            print(f"Saved: {ss_path}")

        browser.close()
        print("All list screenshots captured successfully!")

if __name__ == "__main__":
    verify_all_lists()
