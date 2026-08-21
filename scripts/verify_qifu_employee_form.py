import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 950})
    page.goto(os.getenv('ERPNEXT_SITE_URL') + '/login')
    page.fill('#login_email', os.getenv('ERPNEXT_USERNAME'))
    page.fill('#login_password', os.getenv('ERPNEXT_PASSWORD'))
    page.click("button[type='submit']")
    page.wait_for_url('**/desk**')
    
    # 访问余莉影详情页
    doc_url = f"{os.getenv('ERPNEXT_SITE_URL')}/desk/ashan-employee-salary-profile/天津祺富机械加工有限公司-A0001-余莉影"
    page.goto(doc_url)
    page.wait_for_selector(".form-layout", timeout=15000)
    time.sleep(2)
    
    shot_path = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_employee_form_single.png"
    page.screenshot(path=shot_path)
    print("Saved form view shot:", shot_path)
    browser.close()
