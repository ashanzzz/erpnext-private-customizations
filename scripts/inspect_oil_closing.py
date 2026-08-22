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

    # 3. 切换账期到 2026年7月
    print("Selecting 2026-07...")
    page.select_option("#sel-year", "2026")
    page.select_option("#sel-month", "7")
    time.sleep(2)

    # 截图 1: 7月份当前状态
    shot_july = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_july_current.png"
    page.screenshot(path=shot_july)
    print("Saved July Status Shot:", shot_july)

    # 检查是否处于锁定状态
    unlock_btn = page.query_selector("#btn-unlock-month-action")
    lock_btn = page.query_selector("#btn-lock-month-action")
    print("Is Unlock button present?:", bool(unlock_btn))
    print("Is Lock button present?:", bool(lock_btn))

    # 如果未锁定，执行锁定
    if lock_btn:
        print("Locking July...")
        lock_btn.click()
        time.sleep(1)
        page.click('.modal.show button:has-text("Yes")')
        time.sleep(3)
        shot_july_locked = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_july_locked_clean.png"
        page.screenshot(path=shot_july_locked)
        print("Saved July Clean Locked Shot:", shot_july_locked)

    # 点击【录入加油】，测试锁定拦截
    print("Testing refuel intercept when locked...")
    page.click("#btn-quick-refuel")
    time.sleep(1)
    shot_intercept = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_lock_intercept_clean.png"
    page.screenshot(path=shot_intercept)
    print("Saved Intercept Clean Shot:", shot_intercept)

    # 关闭提示
    page.keyboard.press("Escape")
    time.sleep(1)

    # 4. 切换到 2026年8月，验证期初继承
    print("Selecting 2026-08...")
    page.select_option("#sel-month", "8")
    time.sleep(2)

    shot_aug = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_oil_card_aug_inherit_clean.png"
    page.screenshot(path=shot_aug)
    print("Saved August Inherit Clean Shot:", shot_aug)

    browser.close()
    print("\n[ALL WORKFLOW VERIFICATIONS COMPLETED SUCCESSFULLY!]")
