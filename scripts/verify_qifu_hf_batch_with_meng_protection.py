import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

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

    print("Navigating to Employee Salary Workbench...")
    page.goto(f"{SITE_URL}/desk/employee-salary-workbench")
    page.wait_for_selector("#emp-data-table", state="visible", timeout=15000)
    time.sleep(2)

    # 1. 截图祺富视图工具栏（包含一键公积金按钮与孟祥山豁免保护）
    shot_qifu_bar = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_hf_actions_toolbar.png"
    page.screenshot(path=shot_qifu_bar)
    print("Saved Qifu Bar Shot:", shot_qifu_bar)

    # 2. 测试点击【⚡ 一键全员公积金 (最低基数)】
    print("Clicking 一键全员公积金 (最低基数)...")
    page.click("#btn-qifu-hf-min")
    time.sleep(1)
    
    # 截图确认对话框（显示孟祥山核心保护提示）
    shot_confirm_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_hf_confirm_modal.png"
    page.screenshot(path=shot_confirm_modal)
    print("Saved Confirm Modal Shot:", shot_confirm_modal)

    # 确认执行
    page.click(".modal-dialog .btn-primary")
    time.sleep(2)

    # 关闭提示弹窗（如果有）
    msg_box = page.locator(".modal-dialog.msgprint-dialog")
    if msg_box.is_visible():
        page.keyboard.press("Escape")
        time.sleep(1)

    # 截图一键全员最低基数后的结果
    shot_after_min = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_hf_after_min_base.png"
    page.screenshot(path=shot_after_min)
    print("Saved After Min Base Shot:", shot_after_min)

    # 3. 测试点击【🚫 一键取消公积金 (清零)】
    print("Clicking 一键取消公积金 (清零)...")
    page.click("#btn-qifu-hf-zero")
    time.sleep(1)
    page.click(".modal-dialog .btn-primary")
    time.sleep(2)

    if page.locator(".modal-dialog.msgprint-dialog").is_visible():
        page.keyboard.press("Escape")
        time.sleep(1)

    # 截图一键清零后的结果
    shot_after_zero = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_hf_after_zero_base.png"
    page.screenshot(path=shot_after_zero)
    print("Saved After Zero Base Shot:", shot_after_zero)

    browser.close()

print("\n[ALL QIFU HOUSING FUND BATCH ACCEPTANCE COMPLETED!]")
