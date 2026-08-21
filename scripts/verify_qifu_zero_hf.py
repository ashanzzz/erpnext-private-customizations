import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

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

    # 1. 确认孟祥山当前基数
    # 点击清零
    page.click("#btn-qifu-hf-zero")
    time.sleep(1)
    
    # 确认
    page.locator(".modal-dialog:visible .btn-primary").click()
    time.sleep(3)

    # 关闭提示
    page.keyboard.press("Escape")
    time.sleep(1)

    # 截图清零结果
    shot_zero = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_hf_after_zero_base.png"
    page.screenshot(path=shot_zero)
    print("Saved Zero Shot:", shot_zero)

    browser.close()
