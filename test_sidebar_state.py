import os
import time
import paramiko
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
USERNAME  = os.getenv('ERPNEXT_USER', 'Administrator')
PASSWORD  = os.getenv('ERPNEXT_PASSWORD', 'admin')

opts = webdriver.ChromeOptions()
opts.add_argument('--headless=new')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--window-size=1400,900')

driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 20)

try:
    # Login
    driver.get(f"{SITE_URL}/login")
    time.sleep(2)
    driver.find_element(By.ID, "login_email").send_keys(USERNAME)
    driver.find_element(By.ID, "login_password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, ".btn-login").click()
    time.sleep(4)

    # Navigate to my-business
    driver.get(f"{SITE_URL}/desk/my-business")
    time.sleep(4)

    # Clear localStorage to start fresh (simulate fresh state)
    driver.execute_script("localStorage.removeItem('ashan-cn-sidebar-state'); localStorage.removeItem('section-breaks-state');")
    driver.refresh()
    time.sleep(4)

    # Screenshot: initial state (all sections default)
    driver.save_screenshot("test_initial_state.png")
    print("[1] Initial state screenshot saved")

    # Click on a section header - 财务与报销
    sidebar_items = driver.find_elements(By.CSS_SELECTOR, ".body-sidebar .section-item .standard-sidebar-item")
    print(f"Found {len(sidebar_items)} section items")
    for item in sidebar_items:
        print("  Section:", item.text.strip()[:30])

    # Find 财务与报销 section
    target_section = None
    for item in sidebar_items:
        if "财务" in item.text or "报销" in item.text:
            target_section = item
            break

    if target_section:
        target_section.click()
        time.sleep(1)
        driver.save_screenshot("test_after_click_caiwu.png")
        print("[2] After clicking 财务 section - screenshot saved")

        # Check if other sections are incorrectly opened
        all_children = driver.find_elements(By.CSS_SELECTOR, ".body-sidebar .sidebar-item-children")
        opened = [c for c in all_children if c.get_attribute("data-state") == "opened"]
        closed = [c for c in all_children if c.get_attribute("data-state") == "closed"]
        print(f"Opened sections: {len(opened)}, Closed sections: {len(closed)}")

        # Check localStorage state
        ashan_state = driver.execute_script("return localStorage.getItem('ashan-cn-sidebar-state')")
        native_state = driver.execute_script("return localStorage.getItem('section-breaks-state')")
        print(f"ashan-cn-sidebar-state: {ashan_state}")
        print(f"section-breaks-state: {native_state}")
    else:
        print("[WARN] 财务与报销 section not found")

    # Now click another section and verify states don't cross
    sidebar_items2 = driver.find_elements(By.CSS_SELECTOR, ".body-sidebar .section-item .standard-sidebar-item")
    for item in sidebar_items2:
        if "库存" in item.text or "仓库" in item.text:
            item.click()
            time.sleep(1)
            driver.save_screenshot("test_after_click_kucun.png")
            print("[3] After clicking 库存 section - screenshot saved")

            ashan_state2 = driver.execute_script("return localStorage.getItem('ashan-cn-sidebar-state')")
            print(f"State after 2 clicks: {ashan_state2}")
            break

finally:
    driver.quit()
    print("[DONE] Browser test complete")
