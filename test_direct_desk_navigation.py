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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        # Log in first
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        
        # Now explicitly navigate to /desk
        print("Explicitly navigating to /desk...")
        page.goto(f"{SITE_URL}/desk")
        page.wait_for_timeout(3000)
        
        final_url = page.url
        print("FINAL URL AFTER NAVIGATING TO /desk:", final_url)
        
        screenshot_path = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\desk_navigation_test.png"
        page.screenshot(path=screenshot_path)
        print(f"Saved screenshot to {screenshot_path}")
        browser.close()

if __name__ == "__main__":
    main()
