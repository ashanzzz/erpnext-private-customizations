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
SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        
        page.wait_for_timeout(3000)
        
        # Navigate to /desk/ashan-cn-procurement
        page.goto(f"{SITE_URL}/desk/ashan-cn-procurement")
        page.wait_for_timeout(4000)
        
        # Screenshot default state (menu at bottom)
        screenshot_default = "C:\\Users\\ashan\\.gemini\\antigravity\\brain\\3022ddc6-f669-4fd1-ae68-002d1e790491\\left_sidebar_bottom_toggle.png"
        page.screenshot(path=screenshot_default)
        print(f"Saved default screenshot to {screenshot_default}")
        
        # Click the toggle switch to hide original sidebar items
        checkbox = page.locator("#ashan-toggle-original")
        if checkbox.is_visible():
            checkbox.check()
            page.wait_for_timeout(1000)
            screenshot_hidden = "C:\\Users\\ashan\\.gemini\\antigravity\\brain\\3022ddc6-f669-4fd1-ae68-002d1e790491\\left_sidebar_original_hidden.png"
            page.screenshot(path=screenshot_hidden)
            print(f"Saved hidden screenshot to {screenshot_hidden}")
            
        browser.close()

if __name__ == "__main__":
    main()
