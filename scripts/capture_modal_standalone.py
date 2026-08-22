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

def capture_modal():
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

        # 2. 导航进入【房租与物业费工作台】
        page.evaluate("frappe.set_route('lease-settlement-workbench')")
        time.sleep(3)
        page.wait_for_selector("#sel-month", timeout=10000)

        # 3. 切换到 7 月并等待表格渲染
        page.select_option("#sel-month", "7")
        time.sleep(3)
        page.wait_for_selector(".btn-print-company", timeout=10000)

        # 4. 点击第一家公司（吉众或祺富）的“单证预览”
        page.click(".btn-print-company[data-company='天津祺富机械加工有限公司']")
        time.sleep(3)
        page.wait_for_selector(".bill-dialog-wrapper", timeout=10000)

        # 5. 截图弹窗
        ss_bill = os.path.join(ARTIFACT_DIR, "live_acceptance_lease_bill_preview_july.png")
        page.screenshot(path=ss_bill)
        print(f"Saved Modal: {ss_bill}")

        browser.close()
        print("Modal capture complete!")

if __name__ == "__main__":
    capture_modal()
