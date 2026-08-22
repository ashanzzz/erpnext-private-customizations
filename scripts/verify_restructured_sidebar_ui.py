import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 1050})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(3)

    # 展开所有 Section
    sections = page.locator(".body-sidebar .section-item")
    count = sections.count()
    print(f"Found {count} sidebar sections. Expanding all...")
    for i in range(count):
        sec = sections.nth(i)
        drop_icon = sec.locator(".drop-icon")
        state = sec.get_attribute("data-state")
        if state != "opened" and drop_icon.is_visible():
            try:
                drop_icon.click()
                time.sleep(0.2)
            except Exception:
                pass

    time.sleep(2)
    shot_full_sidebar = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_restructured_sidebar_full_view.png"
    page.screenshot(path=shot_full_sidebar)
    print("Saved Restructured Sidebar Shot:", shot_full_sidebar)

    browser.close()

print("\n[ALL SIDEBAR RESTRUCTURING SCREENSHOTS COMPLETED!]")
