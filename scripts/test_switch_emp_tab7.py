import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1150})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 切换至 Tab 7
    page.click(".qifu-tab-btn[data-tab='history_timeline']")
    time.sleep(3)

    # 通过环境变量指定一个测试员工，避免在公开仓库硬编码真实人员。
    employee_no = os.getenv("ERPNEXT_TEST_EMPLOYEE_NO", "")
    if not employee_no:
        options = page.locator("#select-history-emp option").all_attribute_values("value")
        employee_no = next((value for value in options if value), "")
    if not employee_no:
        raise RuntimeError("历史数据页没有可供测试的员工。")
    print(f"Switching history employee to {employee_no}...")
    page.select_option("#select-history-emp", employee_no)
    time.sleep(3)
    shot_meng = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tab7_employee.png"
    page.screenshot(path=shot_meng)
    print(f"Captured Employee Timeline: {shot_meng}")

    browser.close()
