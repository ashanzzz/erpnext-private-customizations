import os
import sys
import time
import requests
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

    # ==================== 祺富人事薪酬工作台 - 2026-07 外部实发导入与倒推 ====================
    print("\n--- Testing 祺富上传/导入实发工资表 Excel ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-qifu-import-excel", state="visible", timeout=15000)
    time.sleep(2)

    # 1. 打开导入弹窗
    print("Opening Import Dialog...")
    page.click("#btn-qifu-import-excel")
    time.sleep(1)

    # 截图导入弹窗
    shot_import_modal = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_import_excel_dialog.png"
    page.screenshot(path=shot_import_modal)
    print("Saved Import Dialog Shot:", shot_import_modal)

    # 选择快速文件 祺富工资2026.7.xlsx
    print("Selecting 祺富工资2026.7.xlsx...")
    page.select_option(".modal-dialog:visible select[data-fieldname='quick_file']", "祺富工资2026.7.xlsx")
    time.sleep(1)

    # 点击开始导入与倒推
    print("Executing Import & Reverse Tax Calculation...")
    page.click(".modal-dialog:visible .btn-primary")
    time.sleep(4)

    # 关闭提示弹窗 (如有)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 切换月份选择器到 2026-07 并刷新
    page.fill("#qifu-month-select", "2026-07")
    page.dispatch_event("#qifu-month-select", "change")
    time.sleep(3)

    # 截图导入后倒推税前的完整工作台视图
    shot_after_import = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_2026_07_reverse_tax_calculated.png"
    page.screenshot(path=shot_after_import)
    print("Saved After Import Shot:", shot_after_import)

    # 锁定核定
    print("Clicking 祺富确认核定锁定 2026-07...")
    page.click("#btn-qifu-lock-payroll")
    time.sleep(1)
    page.locator(".modal-dialog:visible .btn-primary").click()
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图核定锁定后的只读状态
    shot_locked = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_2026_07_locked.png"
    page.screenshot(path=shot_locked)
    print("Saved Locked Shot:", shot_locked)

    browser.close()

print("\n[EXCEL IMPORT & REVERSE TAX DERIVATION COMPLETED!]")
