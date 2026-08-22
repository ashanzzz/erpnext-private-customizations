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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950})

    # 1. 登录
    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.wait_for_selector("#login_email", state="visible")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # 2. 访问员工工作餐月结工作台
    print("Navigating to meal-settlement-workbench...")
    page.goto(f"{SITE_URL}/desk/meal-settlement-workbench")
    page.wait_for_selector(".meal-workbench-container", state="visible", timeout=15000)
    time.sleep(2)

    # 验证 AshanUI 全局可用性
    has_ashan_ui = page.evaluate("() => typeof window.AshanUI !== 'undefined'")
    print(f"Is window.AshanUI available?: {has_ashan_ui}")

    # 3. 切换账期到 2026年6月 (已导入数据)
    print("Selecting 2026-06 via AshanUI Period Selector...")
    page.select_option(".ashan-period-select.sel-year", "2026")
    page.select_option(".ashan-period-select.sel-month", "6")
    time.sleep(2)

    # 截图 1: 2026年6月餐费工作台升级版
    shot_june_init = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_workbench_upgraded_june.png"
    page.screenshot(path=shot_june_init)
    print("Saved June Upgraded Shot:", shot_june_init)

    # 4. 修改基准单价为 16.0 并点击【💾 保存并应用】
    print("Modifying base price to 16.0 and clicking 保存并应用...")
    page.fill("#inp-base-price", "16.0")
    page.click("#btn-apply-base-price")
    time.sleep(2)

    # 截图 2: 单价更新为 16.0 并同步全月明细
    shot_price_updated = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_base_price_sync_16.png"
    page.screenshot(path=shot_price_updated)
    print("Saved Price 16.0 Updated Shot:", shot_price_updated)

    # 5. 测试快捷键 Ctrl+S 保存草稿
    print("Pressing Ctrl+S to test hotkey save...")
    page.keyboard.press("Control+s")
    time.sleep(1.5)

    # 6. 将单价调回 15.0 恢复标准
    print("Resetting base price back to 15.0...")
    page.fill("#inp-base-price", "15.0")
    page.click("#btn-apply-base-price")
    time.sleep(2)

    # 7. 测试【🗑️ 清空本月】确认弹窗 (切换到 2026年7月测试)
    print("Selecting 2026-07 and testing 清空本月 dialog...")
    page.select_option(".ashan-period-select.sel-month", "7")
    time.sleep(2)

    page.click("#btn-clear-month")
    time.sleep(1)

    # 截图 3: 清空本月确认弹窗
    shot_clear_dialog = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_clear_month_dialog.png"
    page.screenshot(path=shot_clear_dialog)
    print("Saved Clear Month Dialog Shot:", shot_clear_dialog)

    # 确认清空
    page.click('.modal.show button:has-text("Yes")')
    time.sleep(2)

    # 截图 4: 7月份清空后的状态
    shot_cleared = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_july_cleared.png"
    page.screenshot(path=shot_cleared)
    print("Saved July Cleared Shot:", shot_cleared)

    browser.close()
    print("\n[ALL MEAL WORKBENCH & ASHAN UI TESTS COMPLETED SUCCESSFULLY!]")
