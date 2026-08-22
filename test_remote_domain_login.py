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
REMOTE_URL = 'https://erpnext.335356119.xyz'
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        page.on("console", lambda msg: print(f"[REMOTE CONSOLE {msg.type.upper()}] {msg.text}"))
        page.on("framenavigated", lambda frame: print(f"[REMOTE NAVIGATED] {frame.url}") if frame == page.main_frame else None)

        print("1. Going to remote /login...")
        page.goto(f"{REMOTE_URL}/login")
        page.wait_for_timeout(1000)
        
        print("2. Filling credentials and clicking login...")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        
        for t in range(1, 8):
            page.wait_for_timeout(1000)
            print(f"[{t}s] Remote URL: {page.url} | Title: {page.title()}")
            
        screenshot_path = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\remote_domain_login_test.png"
        page.screenshot(path=screenshot_path)
        print(f"Saved remote test screenshot to {screenshot_path}")
        browser.close()

if __name__ == "__main__":
    main()
