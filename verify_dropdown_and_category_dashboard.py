import os
import json
from playwright.sync_api import sync_playwright

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # 1. Login
    print("Step 1: Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click(".btn-login")
    page.wait_for_timeout(3500)

    # 2. Go to My Business
    print("Step 2: Visiting /desk/my-business...")
    page.goto(f"{SITE_URL}/desk/my-business")
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "step1_my_business_landing.png"))

    # 3. Click '仓库与库存' Section Break Header
    print("Step 3: Clicking '仓库与库存' Level 1 Header...")
    stock_header = page.locator(".body-sidebar .section-item:has-text('仓库与库存') .standard-sidebar-item")
    if stock_header.count() > 0:
        stock_header.first.click()
        page.wait_for_timeout(2500)
        current_url = page.url
        print("URL after clicking 仓库与库存:", current_url)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "click_stock_section_result.png"))

    # 4. Click '车油能耗中心' Section Break Header
    print("Step 4: Clicking '车油能耗中心' Level 1 Header...")
    fuel_header = page.locator(".body-sidebar .section-item:has-text('车油能耗中心') .standard-sidebar-item")
    if fuel_header.count() > 0:
        fuel_header.first.click()
        page.wait_for_timeout(2500)
        current_url = page.url
        print("URL after clicking 车油能耗中心:", current_url)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "click_fuel_section_result.png"))

    # 5. Click '企业合规中心' Section Break Header
    print("Step 5: Clicking '企业合规中心' Level 1 Header...")
    comp_header = page.locator(".body-sidebar .section-item:has-text('企业合规中心') .standard-sidebar-item")
    if comp_header.count() > 0:
        comp_header.first.click()
        page.wait_for_timeout(2500)
        current_url = page.url
        print("URL after clicking 企业合规中心:", current_url)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "click_compliance_section_result.png"))

    # 6. Click '我的业务 (总控主页)' Link
    print("Step 6: Clicking '我的业务 (总控主页)'...")
    home_link = page.locator(".body-sidebar a:has-text('我的业务 (总控主页)')")
    if home_link.count() > 0:
        home_link.first.click()
        page.wait_for_timeout(2500)
        current_url = page.url
        print("URL after clicking 我的业务:", current_url)
        page.screenshot(path=os.path.join(ARTIFACT_DIR, "click_home_section_result.png"))

    print("All interaction verifications completed!")
    browser.close()
