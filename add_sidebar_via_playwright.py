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
USERNAME = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PASSWORD = os.getenv('ERPNEXT_PASSWORD', '')

def main():
    print("Starting Playwright to click Add Sidebar Item...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        
        page.wait_for_timeout(4000)
        
        # Click "Add Sidebar Item"
        print("Clicking Add Sidebar Item button...")
        add_btn = page.locator("button:has-text('Add Sidebar Item'), div:has-text('Add Sidebar Item')").last
        if add_btn.is_visible():
            add_btn.click()
            page.wait_for_timeout(1000)
            
            # Modal opens. Select type or title
            print("Modal opened, searching for My Business / 业务扩展...")
            # Look for inputs in dialog
            page.screenshot(path="C:\\Users\\ashan\\.gemini\\antigravity\\brain\\3022ddc6-f669-4fd1-ae68-002d1e790491\\modal_opened.png")
            
        else:
            print("Add Sidebar Item button not found!")
            
        browser.close()

if __name__ == "__main__":
    main()
