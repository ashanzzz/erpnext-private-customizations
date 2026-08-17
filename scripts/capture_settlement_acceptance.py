import os, sys, time
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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def capture_settlement_workbench():
    print("Launching Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Login
        print("Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", state="visible")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=15000)
        time.sleep(3)

        # Go to Property Settlement Workbench via SPA route
        print("Navigating to Property Settlement Workbench via frappe.set_route...")
        page.evaluate("frappe.set_route('property-settlement-workbench')")
        time.sleep(4)

        # Wait for table to render
        page.wait_for_selector("#table-comp-summary", state="visible", timeout=15000)
        time.sleep(2)

        # Screenshot 1: Overview
        ss1 = os.path.join(ARTIFACT_DIR, "live_acceptance_property_settlement_workbench.png")
        page.screenshot(path=ss1, full_page=True)
        print(f"Saved: {ss1}")

        # Click Bill Preview for 吉众
        print("Opening bill preview dialog...")
        btn_print = page.locator(".btn-print-company[data-company='天津吉众机电设备有限公司']").first
        if btn_print.count() > 0:
            btn_print.click()
            time.sleep(2)
            ss2 = os.path.join(ARTIFACT_DIR, "live_acceptance_bill_preview_dialog.png")
            page.screenshot(path=ss2)
            print(f"Saved: {ss2}")

        browser.close()
        print("Playwright capture finished successfully!")

if __name__ == "__main__":
    capture_settlement_workbench()
