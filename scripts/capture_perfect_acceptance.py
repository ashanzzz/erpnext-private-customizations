import os
import sys
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

def run_capture():
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

        # 2. 导航进入 930平米 仓库 Form
        print("Navigating to 930sqm Warehouse Form...")
        page.evaluate("frappe.set_route('Form', 'Property Lease', '天津祺富机械加工有限公司-仓库-930平米 (空港中环南路106号)')")
        time.sleep(4)
        ss_form = os.path.join(ARTIFACT_DIR, "live_acceptance_property_lease_form.png")
        page.screenshot(path=ss_form, full_page=True)
        print(f"Saved Form: {ss_form}")

        # 3. 导航进入【房租与物业费工作台】
        print("Navigating to Lease Settlement Workbench...")
        page.evaluate("frappe.set_route('lease-settlement-workbench')")
        time.sleep(4)
        ss_wb = os.path.join(ARTIFACT_DIR, "live_acceptance_lease_workbench_5pct.png")
        page.screenshot(path=ss_wb, full_page=True)
        print(f"Saved Workbench: {ss_wb}")

        # 4. 点击打开祺富单证预览弹窗
        print("Opening bill preview dialog for 祺富...")
        btn_print = page.locator(".btn-print-company[data-company='天津祺富机械加工有限公司']").first
        if btn_print.count() > 0:
            btn_print.click()
            time.sleep(3)
            ss_bill = os.path.join(ARTIFACT_DIR, "live_acceptance_lease_bill_preview_5pct.png")
            page.screenshot(path=ss_bill)
            print(f"Saved Bill Dialog: {ss_bill}")

        browser.close()
        print("All Done!")

if __name__ == "__main__":
    run_capture()
