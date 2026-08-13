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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        
        page.wait_for_timeout(4000)
        
        # Try navigating directly to /desk/my-business or /desk/ashan-cn-procurement
        print("Navigating to /desk/my-business...")
        page.goto(f"{SITE_URL}/desk/my-business")
        page.wait_for_timeout(3000)
        print("URL after my-business:", page.url)
        page.screenshot(path="C:\\Users\\ashan\\.gemini\\antigravity\\brain\\3022ddc6-f669-4fd1-ae68-002d1e790491\\my_business_page.png")
        
        print("Navigating to /desk/ashan-cn-procurement...")
        page.goto(f"{SITE_URL}/desk/ashan-cn-procurement")
        page.wait_for_timeout(3000)
        print("URL after ashan-cn-procurement:", page.url)
        page.screenshot(path="C:\\Users\\ashan\\.gemini\\antigravity\\brain\\3022ddc6-f669-4fd1-ae68-002d1e790491\\ashan_procurement_page.png")
        
        browser.close()

if __name__ == "__main__":
    main()
