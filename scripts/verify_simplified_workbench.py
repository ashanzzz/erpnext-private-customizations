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
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

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

    # ==================== 祺富人事薪酬工作台 - 极简高能版实机验证 ====================
    print("\n--- Testing 祺富极简高能版工作台 ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-qifu-import-excel", state="visible", timeout=15000)
    time.sleep(2)

    # 1. 打开导入弹窗
    print("Opening Unified Upload Dialog...")
    page.click("#btn-qifu-import-excel")
    time.sleep(1)

    # 2. 选择快速文件 祺富工资2026.7.xlsx 触发智能月份探测
    print("Selecting 祺富工资2026.7.xlsx to trigger smart month detection...")
    page.select_option(".modal-dialog:visible select[data-fieldname='quick_file']", "祺富工资2026.7.xlsx")
    time.sleep(1.5)

    # 截图统一中文拖拽与智能核定月份弹窗
    shot_dialog = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_unified_upload_and_month_detect_dialog.png"
    page.screenshot(path=shot_dialog)
    print("Saved Dialog Shot:", shot_dialog)

    # 3. 点击开始导入与倒推
    print("Clicking Start Import & Reverse Tax...")
    page.click(".modal-dialog:visible .btn-primary")
    time.sleep(3)

    # 关闭提示框 (如有)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图导入后倒推税前的完整工作台视图 (岗位仅显示操作工)
    shot_table = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_simplified_workbench_2026_07.png"
    page.screenshot(path=shot_table)
    print("Saved Workbench Shot:", shot_table)

    # 4. 测试 2026-05 月份智能导入
    print("\nTesting 2026-05 import...")
    page.click("#btn-qifu-import-excel")
    time.sleep(1)
    page.select_option(".modal-dialog:visible select[data-fieldname='quick_file']", "祺富工资2026.5.xlsx")
    time.sleep(1.5)
    page.click(".modal-dialog:visible .btn-primary")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    shot_2026_05 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_simplified_workbench_2026_05.png"
    page.screenshot(path=shot_2026_05)
    print("Saved 2026-05 Shot:", shot_2026_05)

    browser.close()

print("\n[ALL TESTS COMPLETED SUCCESSFULLY!]")
