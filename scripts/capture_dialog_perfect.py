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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')
ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460"

def capture_dialog_perfect():
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
        time.sleep(4)

        # 3. 切换到 7 月
        page.select_option("#sel-month", "7")
        time.sleep(3)

        # 4. 点击第一行的预览单证（吉众）或第二行（祺富）
        btn_qifu = page.locator("button.btn-print-company[data-company='天津祺富机械加工有限公司']").first
        print("Clicking Qifu print button...")
        btn_qifu.click()
        time.sleep(3)

        # 5. 截图包含弹窗的页面
        ss_bill = os.path.join(ARTIFACT_DIR, "live_acceptance_lease_bill_preview_july.png")
        page.screenshot(path=ss_bill)
        print(f"Saved Dialog screenshot: {ss_bill}")

        browser.close()
        print("Success!")

if __name__ == "__main__":
    capture_dialog_perfect()
