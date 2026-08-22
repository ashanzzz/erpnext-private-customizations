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

# 等待站点就绪
for i in range(25):
    try:
        r = requests.get(f"{SITE_URL}/api/method/ping", timeout=3)
        if r.status_code == 200:
            print("Site is ready!")
            break
    except Exception:
        pass
    time.sleep(2)

local_excel_path = r"d:\SynologyDrive团队\antigravity\erpnext16\祺富工资2026.7.xlsx"

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

    # ==================== 1. 纯本地文件上传与智能月度连续性核定 ====================
    print("\n--- Testing 纯本地上传与智能月度核定 ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-qifu-import-excel", state="visible", timeout=15000)
    time.sleep(2)

    # 打开导入弹窗
    print("Opening Local Upload Dialog...")
    page.click("#btn-qifu-import-excel")
    time.sleep(1)

    # 直接将本地真正的 Excel 投递到 input[type='file']
    print(f"Setting input file: {local_excel_path}...")
    page.set_input_files("#inp-qifu-salary-file", local_excel_path)
    time.sleep(2)

    # 截图本地上传识别与月份连续性看板弹窗
    shot_dialog = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_pure_local_upload_dialog.png"
    page.screenshot(path=shot_dialog)
    print("Saved Pure Local Dialog Shot:", shot_dialog)

    # 点击开始解析与倒推
    print("Clicking Start Parse & Reverse Tax...")
    page.click(".modal-dialog:visible .btn-primary")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图 2026-07 成功导入后的工作台
    shot_table_07 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_workbench_local_2026_07.png"
    page.screenshot(path=shot_table_07)
    print("Saved 2026-07 Workbench Shot:", shot_table_07)

    # ==================== 2. 测试一键核定空白零工资账期 (如 2026-08) ====================
    print("\n--- Testing 一键核定空白零工资账期 (2026-08) ---")
    page.click("#btn-qifu-create-blank")
    time.sleep(1)

    # 输入 2026-08 并生成
    page.fill(".modal-dialog:visible input[data-fieldname='period_month']", "2026-08")
    time.sleep(0.5)
    page.click(".modal-dialog:visible .btn-primary")
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图 2026-08 空白核定账期
    shot_blank_08 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_blank_period_2026_08.png"
    page.screenshot(path=shot_blank_08)
    print("Saved 2026-08 Blank Period Shot:", shot_blank_08)

    browser.close()

print("\n[ALL LOCAL UPLOAD & BLANK PERIOD TESTS COMPLETED!]")
