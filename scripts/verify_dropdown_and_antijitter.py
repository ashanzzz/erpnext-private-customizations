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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1150})

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 导航到水电费月结
    page.goto(f"{SITE_URL}/desk/property-settlement-workbench")
    page.wait_for_selector(".prop-unified-header-bar", state="visible", timeout=15000)
    time.sleep(2)

    # 截图 1: 点击【📥 导出 Excel ▼】展开下拉菜单 (验证无内部滚动条，完整跳出并悬浮在最上层)
    page.click("#btn-export-dropdown")
    page.wait_for_selector("#menu-export-excel", state="visible")
    time.sleep(0.5)

    shot_dropdown = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_export_dropdown_fixed.png"
    page.screenshot(path=shot_dropdown)
    print("Saved Export Dropdown Shot:", shot_dropdown)

    # 截图 2: 点击保存草稿触发状态变化 (验证宽度恒定锁死，周边文字绝不抖动位移)
    page.click("#btn-save-draft")
    time.sleep(1)

    shot_saved = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_save_capsule_antijitter.png"
    page.screenshot(path=shot_saved)
    print("Saved Save Capsule Anti-Jitter Shot:", shot_saved)

    browser.close()
