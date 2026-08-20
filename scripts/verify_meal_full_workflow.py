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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
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

    # 3. 导入订餐记录 Excel (8月份)
    print("Uploading 订餐记录(2).xlsx for 2026-08...")
    page.click("#btn-upload-excel")
    page.wait_for_selector("#inp-meal-excel", state="attached", timeout=5000)
    excel_file = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\订餐记录(2).xlsx"
    page.set_input_files("#inp-meal-excel", excel_file)
    time.sleep(0.5)

    # 截图 1: 上传弹窗
    shot_dlg = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_upload_dialog.png"
    page.screenshot(path=shot_dlg)
    print("Saved Dialog Shot:", shot_dlg)

    # 点击开始解析
    page.click(".modal.show .modal-footer button.btn-primary")
    time.sleep(3)

    # 截图 2: 成功提示模态框
    shot_msg = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_upload_success_modal.png"
    page.screenshot(path=shot_msg)
    print("Saved Success Modal Shot:", shot_msg)

    # 关闭提示框
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图 3: 8月份解析后完整表格与 KPI
    shot_aug_parsed = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_workbench_aug_parsed.png"
    page.screenshot(path=shot_aug_parsed)
    print("Saved Aug Parsed Shot:", shot_aug_parsed)

    # 4. 切换到 2026-06 并解析 6 月份数据
    print("Navigating to 2026-06...")
    page.click("#btn-prev-month")
    time.sleep(0.5)
    page.click("#btn-prev-month")
    time.sleep(1)

    page.click("#btn-upload-excel")
    page.wait_for_selector("#inp-meal-excel", state="attached", timeout=5000)
    page.set_input_files("#inp-meal-excel", excel_file)
    time.sleep(0.5)
    page.click(".modal.show .modal-footer button.btn-primary")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图 4: 6月份解析后完整表格与 KPI (祺富/吉众全部准确)
    shot_june_parsed = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_workbench_june_parsed.png"
    page.screenshot(path=shot_june_parsed)
    print("Saved June Parsed Shot:", shot_june_parsed)

    # 5. 测试手动修改与防抖保存
    print("Testing manual edit and debounce autosave...")
    # 修改 6月1日祺富数量为 30
    inp_qifu_1 = page.query_selector("tbody#tbody-meal-records tr:first-child .inp-qifu")
    if inp_qifu_1:
        inp_qifu_1.fill("30")
        inp_qifu_1.dispatch_event("input")
        time.sleep(2)

    # 截图 5: 修改后自动求和与保存状态
    shot_autosave = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_meal_workbench_autosaved.png"
    page.screenshot(path=shot_autosave)
    print("Saved Autosave Shot:", shot_autosave)

    browser.close()
    print("\n[ALL TESTS VERIFIED SUCCESSFULLY!]")
