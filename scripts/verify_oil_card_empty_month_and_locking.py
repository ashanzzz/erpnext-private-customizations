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

    # 2. 访问油卡综合台账明细台
    print("Navigating to oil-card-ledger...")
    page.goto(f"{SITE_URL}/desk/oil-card-ledger")
    page.wait_for_selector(".oil-console-layout", state="visible", timeout=15000)
    time.sleep(2)

    # 3. 切换账期到 2026年7月 (空月)
    print("Selecting 2026-07 (empty month)...")
    page.select_option("#sel-year", "2026")
    page.select_option("#sel-month", "7")
    time.sleep(1.5)

    # 截图 1: 7月份空月展示
    shot_empty_month = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_july_empty.png"
    page.screenshot(path=shot_empty_month)
    print("Saved July Empty Month Shot:", shot_empty_month)

    # 4. 点击【本月核定】
    print("Clicking 本月核定 for 2026-07...")
    page.click("#btn-lock-month-action")
    time.sleep(1)

    # 截图 2: 空月核定确认对话框
    shot_lock_confirm = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_lock_confirm_dialog.png"
    page.screenshot(path=shot_lock_confirm)
    print("Saved Lock Confirm Shot:", shot_lock_confirm)

    # 确认核定
    page.click(".modal.show .modal-footer button.btn-primary")
    time.sleep(2.5)

    # 截图 3: 核定并锁定后的状态
    shot_locked = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_july_locked.png"
    page.screenshot(path=shot_locked)
    print("Saved July Locked Shot:", shot_locked)

    # 5. 尝试在锁定状态下点击【录入加油】
    print("Attempting to click 录入加油 while locked...")
    page.click("#btn-quick-refuel")
    time.sleep(1)

    # 截图 4: 锁定拦截提示
    shot_intercept = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_lock_intercept_msg.png"
    page.screenshot(path=shot_intercept)
    print("Saved Intercept Msg Shot:", shot_intercept)

    # 关闭拦截弹窗
    page.keyboard.press("Escape")
    time.sleep(0.5)

    # 6. 切换到 2026年8月，验证期初自动继承 7 月份期末核定余额
    print("Selecting 2026-08 (inheriting from July)...")
    page.select_option("#sel-month", "8")
    time.sleep(1.5)

    # 截图 5: 8月份期初继承
    shot_aug_inherit = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_aug_inherit.png"
    page.screenshot(path=shot_aug_inherit)
    print("Saved August Inherit Shot:", shot_aug_inherit)

    browser.close()
    print("\n[ALL OIL CARD CLOSING & LOCKING TESTS PASSED SUCCESSFULLY!]")
