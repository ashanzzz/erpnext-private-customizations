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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

ARTIFACT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})

    # 1. Login
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click(".btn-login")
    page.wait_for_timeout(3500)

    # 2. Capture /desk/my-business
    page.goto(f"{SITE_URL}/desk/my-business")
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "option_b_my_business.png"))

    # 3. Capture /desk/vehicle-fuel-hub
    page.goto(f"{SITE_URL}/desk/vehicle-fuel-hub")
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "option_b_fuel_hub.png"))

    # 4. Capture /desk/stock-and-inventory
    page.goto(f"{SITE_URL}/desk/stock-and-inventory")
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "option_b_stock_inventory.png"))

    # 5. Capture /desk/company-compliance-center
    page.goto(f"{SITE_URL}/desk/company-compliance-center")
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(ARTIFACT_DIR, "option_b_compliance_center.png"))

    print("Screenshots captured successfully for Option B!")
    browser.close()
