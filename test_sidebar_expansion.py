import os
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
SITE_URL = 'http://192.168.8.11:6888'
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        
        page.wait_for_timeout(4000)
        page.goto(f"{SITE_URL}/app/home")
        page.wait_for_timeout(3000)
        
        # Click on "采购管理" or triangle icon in sidebar
        procurement_item = page.locator("text='采购管理'").first
        if procurement_item.is_visible():
            print("Found 采购管理 item, clicking...")
            procurement_item.click()
            page.wait_for_timeout(2000)
            
            screenshot_path = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\procurement_expanded.png"
            page.screenshot(path=screenshot_path)
            print(f"Saved expanded procurement screenshot to {screenshot_path}")

        # Click on "车油能耗管理"
        vehicle_item = page.locator("text='车油能耗管理'").first
        if vehicle_item.is_visible():
            print("Found 车油能耗管理 item, clicking...")
            vehicle_item.click()
            page.wait_for_timeout(2000)
            
            screenshot_path2 = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\vehicle_expanded.png"
            page.screenshot(path=screenshot_path2)
            print(f"Saved expanded vehicle screenshot to {screenshot_path2}")
        
        browser.close()

if __name__ == "__main__":
    main()
