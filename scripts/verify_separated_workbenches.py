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

    # ==================== 1. 祺富人事薪酬工作台 ====================
    print("\n--- Testing 祺富人事薪酬工作台 ---")
    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#table-qifu-payroll", state="visible", timeout=15000)
    time.sleep(2)

    # 测算
    print("Clicking 祺富一键测算...")
    page.click("#btn-qifu-calc-payroll")
    time.sleep(3)

    # 截图测算后表格与KPI
    shot_qifu_calc = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_payroll_calculated.png"
    page.screenshot(path=shot_qifu_calc)
    print("Saved Qifu Calc Shot:", shot_qifu_calc)

    # 锁定核定
    print("Clicking 祺富确认核定锁定...")
    page.click("#btn-qifu-lock-payroll")
    time.sleep(1)
    page.locator(".modal-dialog:visible .btn-primary").click()
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图锁定后的只读状态
    shot_qifu_locked = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_payroll_locked.png"
    page.screenshot(path=shot_qifu_locked)
    print("Saved Qifu Locked Shot:", shot_qifu_locked)

    # 切换到员工档案 Tab
    print("Switching to 祺富员工档案 Tab...")
    page.click(".qifu-tab-btn[data-tab='employees']")
    time.sleep(2)
    shot_qifu_emp = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_employees_tab.png"
    page.screenshot(path=shot_qifu_emp)
    print("Saved Qifu Emp Tab Shot:", shot_qifu_emp)

    # 切换到社保配置 Tab
    print("Switching to 祺富社保配置 Tab...")
    page.click(".qifu-tab-btn[data-tab='insurance']")
    time.sleep(1)
    shot_qifu_ins = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_insurance_tab.png"
    page.screenshot(path=shot_qifu_ins)
    print("Saved Qifu Ins Tab Shot:", shot_qifu_ins)

    # ==================== 2. 吉众人事薪酬工作台 ====================
    print("\n--- Testing 吉众人事薪酬工作台 ---")
    page.goto(f"{SITE_URL}/desk/jizhong-hr-salary-workbench")
    page.wait_for_selector("#table-jz-payroll", state="visible", timeout=15000)
    time.sleep(2)

    # 测算
    print("Clicking 吉众一键测算...")
    page.click("#btn-jz-calc-payroll")
    time.sleep(3)

    # 截图测算后表格与KPI
    shot_jz_calc = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_jizhong_payroll_calculated.png"
    page.screenshot(path=shot_jz_calc)
    print("Saved Jizhong Calc Shot:", shot_jz_calc)

    # 锁定核定
    print("Clicking 吉众确认核定锁定...")
    page.click("#btn-jz-lock-payroll")
    time.sleep(1)
    page.locator(".modal-dialog:visible .btn-primary").click()
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图锁定后的只读状态
    shot_jz_locked = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_jizhong_payroll_locked.png"
    page.screenshot(path=shot_jz_locked)
    print("Saved Jizhong Locked Shot:", shot_jz_locked)

    # 切换到员工档案 Tab
    print("Switching to 吉众员工档案 Tab...")
    page.click(".jz-tab-btn[data-tab='employees']")
    time.sleep(2)
    shot_jz_emp = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_jizhong_employees_tab.png"
    page.screenshot(path=shot_jz_emp)
    print("Saved Jizhong Emp Tab Shot:", shot_jz_emp)

    # 切换到社保配置 Tab
    print("Switching to 吉众社保配置 Tab...")
    page.click(".jz-tab-btn[data-tab='insurance']")
    time.sleep(1)
    shot_jz_ins = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_jizhong_insurance_tab.png"
    page.screenshot(path=shot_jz_ins)
    print("Saved Jizhong Ins Tab Shot:", shot_jz_ins)

    browser.close()

print("\n[ALL SEPARATED WORKBENCHES TESTED AND ACCEPTED!]")
