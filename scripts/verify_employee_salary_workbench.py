import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
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
    time.sleep(3)

    # 1. 祺富视图截图
    shot_qifu = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_employee_workbench.png"
    page.screenshot(path=shot_qifu)
    print("Saved Qifu View Shot:", shot_qifu)

    # 2. 切换至吉众视图
    print("Switching to Jizhong tab...")
    page.click(".emp-company-tab[data-company='天津吉众机电设备有限公司']")
    time.sleep(2)
    shot_jizhong = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_jizhong_employee_workbench.png"
    page.screenshot(path=shot_jizhong)
    print("Saved Jizhong View Shot:", shot_jizhong)

    # 3. 测试点击单人【修改参数】弹窗
    print("Opening single edit modal...")
    page.click(".btn-emp-edit:visible")
    time.sleep(1)
    page.wait_for_selector(".modal-dialog", state="visible")
    shot_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_employee_edit_dialog.png"
    page.screenshot(path=shot_modal)
    print("Saved Single Edit Dialog Shot:", shot_modal)

    # 关闭弹窗
    page.keyboard.press("Escape")
    time.sleep(1)

    # 4. 测试勾选多位员工并展示批量修改栏
    print("Testing multi-select for batch update...")
    checks = page.locator(".emp-row-check")
    if checks.count() >= 3:
        checks.nth(0).check()
        checks.nth(1).check()
        checks.nth(2).check()
        time.sleep(1)
        shot_batch = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_employee_batch_bar.png"
        page.screenshot(path=shot_batch)
        print("Saved Batch Bar Shot:", shot_batch)

    browser.close()

print("\n[ALL WORKBENCH SCREENSHOTS AND ACCEPTANCE COMPLETED!]")
