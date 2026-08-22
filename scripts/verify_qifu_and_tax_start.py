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

    # 截图 1: 吉众机电 (带有自定义个税计税起始月份胶囊)
    shot_jizhong = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_jizhong_with_tax_start.png"
    page.screenshot(path=shot_jizhong)
    print("Saved Jizhong Shot:", shot_jizhong)

    # 3. 切换到【🏢 祺富机械】
    page.click(".payroll-comp-tab-btn[data-comp='天津祺富机械加工有限公司']")
    time.sleep(1.5)

    # 截图 2: 祺富机械全员薪资总表 (展示天工资、全勤、达标、职位/房车补贴及导入老板娘工资表按钮)
    shot_qifu = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_qifu_summary.png"
    page.screenshot(path=shot_qifu)
    print("Saved Qifu Summary Shot:", shot_qifu)

    # 4. 点击【📥 导入老板娘工资表】按钮，唤起上传模态框
    page.click("#btn-import-boss-sheet")
    page.wait_for_selector(".modal-dialog", state="visible", timeout=5000)
    time.sleep(1)

    # 截图 3: 导入老板娘工资表上传模态框
    shot_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_boss_sheet_modal.png"
    page.screenshot(path=shot_modal)
    print("Saved Boss Sheet Modal Shot:", shot_modal)

    # 5. 关闭模态框并测试切换【个税计税起始月份】为 2025-12
    page.click(".modal-header .btn-modal-close, .modal-header .close")
    time.sleep(0.5)
    page.select_option("#sel-tax-start-month", "2025-12")
    time.sleep(1.5)

    # 截图 4: 切换个税起始月份为 2025-12 后的累计个税视图
    page.click(".payroll-view-tab[data-view='tax']")
    time.sleep(0.5)
    shot_tax = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_payroll_custom_tax_cycle.png"
    page.screenshot(path=shot_tax)
    print("Saved Custom Tax Cycle Shot:", shot_tax)

    browser.close()
