import os
import json
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
    page = browser.new_page(viewport={"width": 1440, "height": 1050})

    # 1. 登录
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")

    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 前往房租物业月结工作台
    page.goto(f"{SITE_URL}/desk/lease-settlement-workbench")
    page.wait_for_selector("#dim-switch-group", state="visible", timeout=15000)
    time.sleep(2)

    # 滚动到租赁明细表格区域
    page.evaluate("window.scrollBy(0, 380)")
    time.sleep(1)

    # 3. 截取 默认【按年展示 (基准)】
    shot_annual = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_lease_bench_annual.png"
    page.screenshot(path=shot_annual)
    print("Saved Annual View:", shot_annual)

    # 4. 点击【📆 按月展示】
    page.click("button[data-dim='monthly']")
    time.sleep(1)
    shot_monthly = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_lease_bench_monthly.png"
    page.screenshot(path=shot_monthly)
    print("Saved Monthly View:", shot_monthly)

    # 5. 点击【📅 按日展示】
    page.click("button[data-dim='daily']")
    time.sleep(1)
    shot_daily = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_lease_bench_daily.png"
    page.screenshot(path=shot_daily)
    print("Saved Daily View:", shot_daily)

    # 6. 回到顶部点击【🖨️ 单证预览/打印】
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)
    page.click("#btn-preview-bills")
    page.wait_for_selector(".modal.show, .modal-dialog", state="visible", timeout=5000)
    time.sleep(1.5)

    shot_bill = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_lease_bench_bill_modal.png"
    page.screenshot(path=shot_bill)
    print("Saved Bill Modal View:", shot_bill)

    browser.close()
