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
        
        page.wait_for_timeout(4000)
        
        # Take a screenshot of Desk
        screenshot_path = "C:\\Users\\ashan\\.gemini\\antigravity\\brain\\3022ddc6-f669-4fd1-ae68-002d1e790491\\sidebar_result.png"
        page.screenshot(path=screenshot_path)
        print(f"Saved screenshot to {screenshot_path}")
        
        # Get sidebar text
        items = page.locator(".standard-sidebar-item, .sidebar-item-label, .item-anchor").all_inner_texts()
        print("Sidebar items found:", items)
        
        browser.close()

if __name__ == "__main__":
    main()
