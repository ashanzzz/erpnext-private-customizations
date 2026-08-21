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
    page = browser.new_page(viewport={"width": 1600, "height": 1200})

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(3)

    # 通过 jQuery 一键展开全部侧边栏 Section
    page.evaluate("""() => {
        $('.body-sidebar .section-item').each(function() {
            const $sec = $(this);
            $sec.attr('data-state', 'opened');
            $sec.find('.drop-icon').attr('data-state', 'opened').show().find('use').attr('href', '#icon-chevron-down');
            $sec.find('.sidebar-child-item').show().removeClass('hidden');
            $sec.find('.sidebar-child-item .standard-sidebar-item').show().removeClass('hidden');
        });
    }""")

    time.sleep(2)
    shot_expanded = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_sidebar_sections_opened.png"
    page.screenshot(path=shot_expanded)
    print("Saved Opened Sections Shot:", shot_expanded)

    browser.close()

print("\n[ALL EXPANDED SIDEBAR SCREENSHOTS CAPTURED!]")
