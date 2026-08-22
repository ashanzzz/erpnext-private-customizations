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
        
        # Go to login page
        page.goto(f"{SITE_URL}/login")
        
        # Fill credentials
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        
        # Wait for Desk to load (wait for the workspace title or sidebar)
        page.wait_for_selector(".standard-sidebar-item", timeout=30000)
        
        # Wait a bit for everything to settle
        page.wait_for_timeout(3000)
        
        # Expand "我的业务" if it's there
        try:
            # Click the dropdown toggle for "My Business"
            my_business_item = page.locator(".standard-sidebar-item:has-text('我的业务')")
            if my_business_item.count() > 0:
                # Find the expand icon (usually a chevron) inside the item
                chevron = my_business_item.locator(".sidebar-item-control .icon-use")
                if chevron.count() > 0:
                    chevron.click()
                    page.wait_for_timeout(1000)
        except Exception as e:
            print("Could not expand: ", e)
        
        # Screenshot the whole page
        screenshot_path = os.path.join(os.path.dirname(__file__), "sidebar_verification.png")
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        browser.close()

if __name__ == "__main__":
    main()
