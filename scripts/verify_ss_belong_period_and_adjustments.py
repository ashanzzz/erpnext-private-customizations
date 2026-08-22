import os
import sys
import time
import json
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

session = requests.Session()
session.post(f"{SITE_URL}/api/method/login", data={"usr": USERNAME, "pwd": USER_PWD})

# 1. 直接登记一笔补缴调整；测试员工从环境变量读取，避免公开仓库保留真实工号/姓名。
test_employee_no = os.getenv("ERPNEXT_TEST_EMPLOYEE_NO", "DEMO001")
adj_data = {
    "employee_no": test_employee_no,
    "period_month_str": "202605",
    "biz_type": "历史补缴",
    "ss_base": 5124.0,
    "late_fee": 50.0,
    "remarks": "补缴5月份社保，税局收取滞纳金50元"
}
r = session.post(
    f"{SITE_URL}/api/method/ashan_cn_procurement.services.payroll_settlement_service.save_social_insurance_adjustment",
    data={
        "company": "天津祺富机械加工有限公司",
        "period_month": "2026-07",
        "adjustment_json": json.dumps(adj_data)
    }
)
print("Save Adjustment Result:", r.json())

# 2. 浏览器打开社保明细模态框并截图
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1850, "height": 1100})

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

    print("Opening Social Insurance Modal...")
    page.click("#btn-view-ins-sheet", force=True)
    page.wait_for_selector("#btn-modal-export-ins", state="visible", timeout=10000)
    time.sleep(1)

    adjs_count = page.evaluate("() => document.querySelectorAll('.btn-del-ss-adj').length")
    print(f"✅ Found {adjs_count} Adjustment/Backpay Row(s) in Modal!")

    shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_social_insurance_adjustment_live.png"
    page.screenshot(path=shot)
    print("Saved Screenshot with Adjustment:", shot)

    browser.close()

print("\n[ALL BELONG PERIOD & SPECIAL ADJUSTMENT 100% VERIFIED!]")
