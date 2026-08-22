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
        
        nav_count = 0
        def on_nav(frame):
            nonlocal nav_count
            if frame == page.main_frame:
                nav_count += 1
                print(f"[FULL PAGE RELOAD #{nav_count}] {frame.url}")

        page.on("framenavigated", on_nav)

        print("Logging in...")
        page.goto(f"{SITE_URL}/login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click(".btn-login")
        page.wait_for_timeout(3000)
        
        print("\n--- Clicking Sidebar Workspace Items ---")
        items = ["采购管理", "仓库与库存", "会计与财务", "车油能耗管理", "企业合规中心", "我的业务"]
        
        for item in items:
            initial_nav = nav_count
            print(f"\nSearching for sidebar item: '{item}'")
            
            # Match element containing text
            loc = page.locator(".sidebar-item-label, .body-sidebar a, .desk-sidebar a").filter(has_text=item).first
            if loc.is_visible():
                loc.click()
                page.wait_for_timeout(2000)
                print(f"Clicked '{item}' | Current URL: {page.url}")
                if nav_count > initial_nav:
                    print(f"  --> BUG DETECTED: Clicking '{item}' caused FULL PAGE RELOAD!")
                else:
                    print(f"  --> SPA Navigation Clean (No reload)")
            else:
                print(f"  --> Element '{item}' not visible")

        browser.close()

if __name__ == "__main__":
    main()
