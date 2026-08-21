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
    page.goto(os.getenv('ERPNEXT_SITE_URL') + '/desk/tax-invoice-center')
    page.wait_for_selector('.tax-inv-wrapper')
    time.sleep(2)
    
    # 搜索发票号 26122000000099990001
    page.fill('#filter-search', '26122000000099990001')
    page.press('#filter-search', 'Enter')
    time.sleep(1.5)
    
    shot_path = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_tax_invoice_exact_mismatch_single_view.png"
    page.screenshot(path=shot_path)
    print("Saved single view shot:", shot_path)
    browser.close()
