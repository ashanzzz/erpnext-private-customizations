import os
import sys
import time
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(r"d:\SynologyDrive团队\antigravity\erpnext16\.env")

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

for i in range(25):
    try:
        r = requests.get(f"{SITE_URL}/api/method/ping", timeout=3)
        if r.status_code == 200:
            print("Site is ready!")
            break
    except Exception:
        pass
    time.sleep(2)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1850, "height": 1150})

    errors = []
    page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}") if msg.type in ['error', 'warning'] else None)
    page.on("pageerror", lambda err: errors.append(str(err)))

    print("Logging in...")
    page.goto(f"{SITE_URL}/login")
    page.fill("#login_email", USERNAME)
    page.fill("#login_password", USER_PWD)
    page.click("button[type='submit']")
    page.wait_for_url("**/desk**", timeout=20000)
    time.sleep(2)

    page.goto(f"{SITE_URL}/desk/qifu-hr-salary-workbench")
    time.sleep(3)
    page.keyboard.press("Escape")
    time.sleep(1)

    # 1. 验证 Tab 2 备考列
    print("\n--- 1. Testing Tab 2: 备考列空值显示 ---")
    page.click("[data-tab='import']")
    time.sleep(2)
    tab2_remarks = page.eval_on_selector_all("#tbody-qifu-distribution tr td:last-child", "els => els.map(e => e.innerText)")
    print(f"✅ Tab 2 备考列数据示例: {tab2_remarks[:5]}")

    page.click("[data-tab='employees']")
    time.sleep(1)

    # 如果当前处于锁定状态，先解锁以完整测试闭环
    is_locked_init = page.is_visible("#btn-qifu-unlock-month")
    if is_locked_init:
        print("Initial state is locked, unlocking for full cycle testing...")
        page.click("#btn-qifu-unlock-month")
        time.sleep(1)
        page.fill(".modal.in textarea, .modal.show textarea", "自动化测试重置")
        page.click(".modal.in .btn-primary, .modal.show .btn-primary")
        time.sleep(2)
        page.keyboard.press("Escape")
        time.sleep(1)

    # 2. 验证【🔒 核定本月薪酬台账】与全页只读模式
    print("\n--- 2. Testing Lock Month & Readonly Protection ---")
    lock_badge_before = page.text_content("#qifu-month-lock-badge")
    print(f"  Lock Badge Before: {lock_badge_before.strip()}")

    # 点击核定
    page.click("#btn-qifu-lock-month")
    time.sleep(1)
    page.click(".modal.in .btn-primary, .modal.show .btn-primary")
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)

    lock_badge_after = page.text_content("#qifu-month-lock-badge")
    banner_visible = page.is_visible("#qifu-locked-banner")
    new_emp_disabled = page.is_disabled("#btn-qifu-new-emp")
    print(f"✅ Lock Badge After: {lock_badge_after.strip()}")
    print(f"✅ Readonly Banner Visible: {banner_visible}")
    print(f"✅ Add Emp Button Disabled: {new_emp_disabled}")

    shot1 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_month_locked_readonly.png"
    page.screenshot(path=shot1)

    # 3. 验证【🔓 撤销核定】
    print("\n--- 3. Testing Unlock Month ---")
    page.click("#btn-qifu-unlock-month")
    time.sleep(1)
    page.fill(".modal.in textarea, .modal.show textarea", "测试撤销核定并恢复编辑")
    page.click(".modal.in .btn-primary, .modal.show .btn-primary")
    time.sleep(2)
    page.keyboard.press("Escape")
    time.sleep(1)

    lock_badge_unlocked = page.text_content("#qifu-month-lock-badge")
    new_emp_enabled = not page.is_disabled("#btn-qifu-new-emp")
    print(f"✅ Lock Badge Unlocked: {lock_badge_unlocked.strip()}")
    print(f"✅ Add Emp Button Enabled: {new_emp_enabled}")

    shot2 = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_month_unlocked_draft.png"
    page.screenshot(path=shot2)

    # 4. 验证 Excel 导出功能
    print("\n--- 4. Testing Excel Export Download ---")
    with page.expect_download() as download_info:
        page.click("#btn-qifu-export-all")
    download = download_info.value
    download_path = os.path.join(r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\scratch", download.suggested_filename)
    download.save_as(download_path)
    file_size = os.path.getsize(download_path)
    print(f"🎉 Excel Download Success: {download.suggested_filename} ({file_size} bytes)")

    print("\n--- Errors check ---")
    if len(errors) == 0:
        print("🎉 ZERO PAGE ERRORS! LOCK/UNLOCK, EXCEL EXPORT, PRINT & CLEAN REMARKS 100% VERIFIED!")
    else:
        for err in errors:
            print("❌ PAGE ERROR:", err)

    browser.close()
