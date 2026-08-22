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

def capture_acceptance():
    print("Launching Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. 登录
        print("1. Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.wait_for_selector("#login_email", state="visible")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", USER_PWD)
        page.click("button[type='submit']")
        page.wait_for_url("**/desk**", timeout=20000)
        time.sleep(3)

        # 2. 访问 Property Lease 列表
        print("2. Navigating to Property Lease List...")
        page.evaluate("frappe.set_route('List', 'Property Lease')")
        time.sleep(4)
        ss1 = os.path.join(ARTIFACT_DIR, "live_acceptance_property_lease_list.png")
        page.screenshot(path=ss1)
        print(f"Saved: {ss1}")

        # 3. 点击进入 930平米 仓库 Form 详情
        print("3. Navigating to 930sqm Warehouse Form...")
        page.evaluate("frappe.set_route('Form', 'Property Lease', '天津祺富机械加工有限公司-仓库-930平米')")
        time.sleep(4)
        ss2 = os.path.join(ARTIFACT_DIR, "live_acceptance_property_lease_form.png")
        page.screenshot(path=ss2, full_page=True)
        print(f"Saved: {ss2}")

        # 4. 访问房租与物业费工作台
        print("4. Navigating to Lease Settlement Workbench...")
        page.evaluate("frappe.set_route('lease-settlement-workbench')")
        time.sleep(4)
        page.wait_for_selector("#table-comp-summary", state="visible", timeout=15000)
        ss3 = os.path.join(ARTIFACT_DIR, "live_acceptance_lease_workbench_5pct.png")
        page.screenshot(path=ss3, full_page=True)
        print(f"Saved: {ss3}")

        # 5. 打开单证预览弹窗（天津祺富机械加工有限公司）
        print("5. Opening Bill Preview Dialog...")
        btn_print = page.locator(".btn-print-company[data-company='天津祺富机械加工有限公司']").first
        if btn_print.count() > 0:
            btn_print.click()
            time.sleep(3)
            ss4 = os.path.join(ARTIFACT_DIR, "live_acceptance_lease_bill_preview_5pct.png")
            page.screenshot(path=ss4)
            print(f"Saved: {ss4}")

        browser.close()
        print("All acceptance verification completed!")

if __name__ == "__main__":
    capture_acceptance()
