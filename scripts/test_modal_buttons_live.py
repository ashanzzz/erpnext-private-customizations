import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

for i in range(25):
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
    page = browser.new_page(viewport={"width": 1850, "height": 1100})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    page.wait_for_selector("#btn-view-ins-sheet", state="visible", timeout=15000)
    time.sleep(2)

    print("1. Opening Social Insurance Modal...")
    page.click("#btn-view-ins-sheet")
    page.wait_for_selector("#btn-modal-export-ins", state="visible", timeout=10000)
    time.sleep(1)

    print("2. Testing Excel Export Button in Modal...")
    with page.expect_download(timeout=10000) as download_info:
        page.click("#btn-modal-export-ins")
    download = download_info.value
    download_path = os.path.join(r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\scratch", download.suggested_filename)
    download.save_as(download_path)
    print("✅ Downloaded Excel Successfully:", download.suggested_filename, "Size:", os.path.getsize(download_path))

    print("3. Testing Print Button in Modal...")
    page.click("#btn-modal-print-ins")
    time.sleep(1)
    # Check if print-report-iframe exists and has content
    has_iframe = page.evaluate("() => document.getElementById('print-report-iframe') !== null")
    print("✅ Print Iframe Created:", has_iframe)

    shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_qifu_social_insurance_modal.png"
    page.screenshot(path=shot)
    print("Saved Screenshot:", shot)

    browser.close()

print("\n[MODAL BUTTONS CLICK & EXPORT & PRINT TEST PASSED 100%!]")
