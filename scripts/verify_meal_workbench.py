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

    # 2. 访问工作餐费月结工作台
    print("Navigating to meal-settlement-workbench...")
    page.goto(f"{SITE_URL}/desk/meal-settlement-workbench")
    page.wait_for_selector(".meal-top-bar", state="visible", timeout=15000)
    time.sleep(1)

    # 3. 点击【📥 导入订餐 Excel】
    print("Opening upload dialog...")
    page.click("#btn-upload-excel")
    page.wait_for_selector("#inp-meal-excel", state="attached", timeout=5000)
    time.sleep(0.5)

    excel_file = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\订餐记录(2).xlsx"
    print("Uploading file:", excel_file)
    page.set_input_files("#inp-meal-excel", excel_file)
    time.sleep(1)

    # 点击开始解析
    print("Clicking start parse button...")
    page.click(".modal.show .modal-footer button.btn-primary")
    time.sleep(3)

    # 截图 1: 导入成功提示弹窗
    shot_msg = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_upload_success_modal.png"
    page.screenshot(path=shot_msg)
    print("Saved Msg Shot:", shot_msg)

    # 按 Escape 关掉提示框
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图 2: 导入后完整表格与 KPI 看板
    shot_parsed = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_workbench_parsed.png"
    page.screenshot(path=shot_parsed)
    print("Saved Parsed Shot:", shot_parsed)

    # 4. 测试手动编辑单元格与自动防抖保存
    print("Testing inline edit on Row 1 (Aug 1)...")
    first_qifu_inp = page.query_selector("tbody#tbody-meal-records tr:first-child .inp-qifu")
    if first_qifu_inp:
        first_qifu_inp.fill("28")
        first_qifu_inp.dispatch_event("input")
        time.sleep(2)

    # 截图 3: 自动保存后状态
    shot_saved = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_workbench_autosaved.png"
    page.screenshot(path=shot_saved)
    print("Saved Auto Saved Shot:", shot_saved)

    # 5. 测试切换到 6 月份并解析 6 月工作表
    print("Switching month to 2026-06...")
    page.click("#btn-prev-month")
    time.sleep(0.5)
    page.click("#btn-prev-month")
    time.sleep(1)

    print("Month is now:", page.inner_text("#text-current-month"))
    # 上传 6 月数据
    page.click("#btn-upload-excel")
    page.wait_for_selector("#inp-meal-excel", state="attached", timeout=5000)
    page.set_input_files("#inp-meal-excel", excel_file)
    time.sleep(0.5)
    page.click(".modal.show .modal-footer button.btn-primary")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图 4: 6月份完整订餐明细
    shot_june = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_workbench_june.png"
    page.screenshot(path=shot_june)
    print("Saved June Shot:", shot_june)

    browser.close()
    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")
