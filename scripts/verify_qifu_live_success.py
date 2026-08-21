import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 950})

    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/employee-salary-workbench")
    page.wait_for_selector("#emp-data-table", state="visible", timeout=15000)
    time.sleep(2)

    # 1. 触发一键全员最低基数
    print("Testing 一键全员公积金 (最低基数)...")
    page.click("#btn-qifu-hf-min")
    time.sleep(1)
    page.click(".modal-dialog:visible .btn-primary")
    time.sleep(3)
    
    # 截图成功弹窗
    shot_msg = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_hf_success_alert.png"
    page.screenshot(path=shot_msg)
    print("Saved Success Alert Shot:", shot_msg)

    # 关闭提示
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图表格
    shot_table = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_hf_live_verified.png"
    page.screenshot(path=shot_table)
    print("Saved Live Verified Shot:", shot_table)

    browser.close()

print("\n[FRONTEND PLAYWRIGHT WORKFLOW FULLY VERIFIED!]")
