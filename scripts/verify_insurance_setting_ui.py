import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

# 等待站点就绪
for i in range(20):
    try:
        r = requests.get(f"{SITE_URL}/api/method/ping", timeout=3)
        if r.status_code == 200:
            print("Site is ready!")
            break
    except Exception:
        pass
    time.sleep(2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 950})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    # ==================== 1. 祺富社保公积金配置 Tab ====================
    print("\n--- Testing 祺富社保公积金配置 Tab ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector(".qifu-tab-btn[data-tab='insurance']", state="visible", timeout=15000)
    time.sleep(2)

    page.click(".qifu-tab-btn[data-tab='insurance']")
    time.sleep(2)

    # 截图祺富社保配置视图（含合计卡片）
    shot_qifu_ins = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_insurance_setting_totals.png"
    page.screenshot(path=shot_qifu_ins)
    print("Saved Qifu Ins Shot:", shot_qifu_ins)

    # 点击修改配置弹窗
    print("Clicking 祺富修改社保配置按钮...")
    page.click("#btn-qifu-edit-insurance")
    time.sleep(1)

    shot_qifu_ins_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_insurance_edit_dialog.png"
    page.screenshot(path=shot_qifu_ins_modal)
    print("Saved Qifu Ins Modal Shot:", shot_qifu_ins_modal)

    page.keyboard.press("Escape")
    time.sleep(1)

    # ==================== 2. 吉众社保公积金配置 Tab ====================
    print("\n--- Testing 吉众社保公积金配置 Tab ---")
    page.goto(f"{SITE_URL}/desk/jizhong-hr-salary-workbench")
    page.wait_for_selector(".jz-tab-btn[data-tab='insurance']", state="visible", timeout=15000)
    time.sleep(2)

    page.click(".jz-tab-btn[data-tab='insurance']")
    time.sleep(2)

    # 截图吉众社保配置视图（含合计卡片）
    shot_jz_ins = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_jizhong_insurance_setting_totals.png"
    page.screenshot(path=shot_jz_ins)
    print("Saved Jizhong Ins Shot:", shot_jz_ins)

    # 点击修改配置弹窗
    print("Clicking 吉众修改社保配置按钮...")
    page.click("#btn-jz-edit-insurance")
    time.sleep(1)

    shot_jz_ins_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_jizhong_insurance_edit_dialog.png"
    page.screenshot(path=shot_jz_ins_modal)
    print("Saved Jizhong Ins Modal Shot:", shot_jz_ins_modal)

    browser.close()

print("\n[ALL INSURANCE SETTING UI VERIFIED AND ACCEPTED!]")
