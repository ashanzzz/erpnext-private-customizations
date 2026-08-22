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

    # 2. 导航到人事与薪资月结工作台
    page.goto(f"{SITE_URL}/desk/payroll-settlement-workbench")
    page.wait_for_selector(".payroll-unified-header-bar", state="visible", timeout=15000)
    time.sleep(2)

    # 截图 1: 工资核定总表视图 (全员数据与 KPI 汇总看板)
    shot_summary = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_workbench_summary.png"
    page.screenshot(path=shot_summary)
    print("Saved Payroll Summary Shot:", shot_summary)

    # 截图 2: 切换到 [ 🛡️ 五险一金核算 ]
    page.click(".payroll-view-tab[data-view='insurance']")
    time.sleep(0.5)
    shot_ins = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_workbench_insurance.png"
    page.screenshot(path=shot_ins)
    print("Saved Payroll Insurance Shot:", shot_ins)

    # 截图 3: 切换到 [ 🏛️ 个人所得税累计 ]
    page.click(".payroll-view-tab[data-view='tax']")
    time.sleep(0.5)
    shot_tax = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_workbench_tax.png"
    page.screenshot(path=shot_tax)
    print("Saved Payroll Tax Shot:", shot_tax)

    # 截图 4: 切换到 [ 💵 现金零钞配钞表 ]
    page.click(".payroll-view-tab[data-view='cash']")
    time.sleep(0.5)
    shot_cash = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_workbench_cash.png"
    page.screenshot(path=shot_cash)
    print("Saved Payroll Cash Shot:", shot_cash)

    # 截图 5: 打开 A4 签收单打印预览
    page.click("#btn-print-a4")
    page.wait_for_selector(".payroll-print-modal-body", state="visible", timeout=5000)
    time.sleep(1)
    shot_print = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_a4_print_preview.png"
    page.screenshot(path=shot_print)
    print("Saved A4 Print Preview Shot:", shot_print)

    browser.close()
