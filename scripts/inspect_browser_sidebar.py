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

def inspect_sidebar_in_browser():
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

        # 2. 检查当前 URL 与左侧栏文本
        print(f"Current URL after login: {page.url}")
        sidebar_items = page.eval_on_selector_all(".desk-sidebar .sidebar-item-container, .layout-side-section .sidebar-item-container, .standard-sidebar-item", "elements => elements.map(e => e.innerText.trim())")
        print("\n--- Detected Sidebar Items ---")
        for it in sidebar_items:
            print("  -", it.replace('\n', ' | '))

        ss_path = os.path.join(ARTIFACT_DIR, "live_acceptance_current_sidebar.png")
        page.screenshot(path=ss_path)
        print(f"\nSaved screenshot: {ss_path}")

        # 3. 检查【My Business】Workspace 的侧边栏
        page.evaluate("frappe.set_route('workspace', 'my-business')")
        time.sleep(3)
        ss_my_biz = os.path.join(ARTIFACT_DIR, "live_acceptance_my_biz_sidebar.png")
        page.screenshot(path=ss_my_biz)
        print(f"Saved My Business screenshot: {ss_my_biz}")

        browser.close()
        print("Inspection complete!")

if __name__ == "__main__":
    inspect_sidebar_in_browser()
