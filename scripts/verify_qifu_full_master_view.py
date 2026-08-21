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
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1750, "height": 1100})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#table-qifu-payroll", state="visible", timeout=15000)
    time.sleep(2)

    # 截图工作台顶部与车间出勤及补贴人员
    shot_top = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_master_fusion_2026_07_workshop.png"
    page.screenshot(path=shot_top)
    print("Saved Workshop Shot:", shot_top)

    # 滚动到底部查看非车间出勤(母表在册人员)与管理补贴人员
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    shot_bottom = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_master_fusion_2026_07_non_workshop.png"
    page.screenshot(path=shot_bottom)
    print("Saved Non Workshop Shot:", shot_bottom)

    browser.close()

print("\n[ALL SCREENSHOTS CAPTURED!]")
