import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

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
    page = browser.new_page(viewport={"width": 1440, "height": 1050})

    # 1. 登录
    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 访问水电费月结工作台
    print("Navigating to property-settlement-workbench...")
    page.goto(f"{SITE_URL}/desk/property-settlement-workbench")
    page.wait_for_selector("#table-elec-meters", state="visible", timeout=15000)
    time.sleep(2)

    # 截图 1: 顶部录入区域优先视图 (电表/水表抄表置顶，表头有 * 号与加粗输入框)
    shot_top = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_prop_workbench_input_top.png"
    page.screenshot(path=shot_top)
    print("Saved Top Input Shot:", shot_top)

    # 聚焦第一个电表输入框，触发 focus 高亮
    first_inp = page.query_selector("#table-elec-meters .cell-reading-input")
    if first_inp:
        first_inp.focus()
        time.sleep(0.5)

    # 滚动到下方，查看全公司总开支汇总看板
    page.evaluate("window.scrollTo(0, 800)")
    time.sleep(1)

    # 截图 2: 底部财务总开支与分公司汇总看板
    shot_bottom = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_prop_workbench_summary_bottom.png"
    page.screenshot(path=shot_bottom)
    print("Saved Bottom Summary Shot:", shot_bottom)

    browser.close()
    print("\n[VERIFICATION COMPLETED]")
