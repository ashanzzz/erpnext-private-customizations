# -*- coding: utf-8 -*-
import os
import asyncio
from playwright.async_api import async_playwright

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = "http://192.168.8.11:6888"
ERPNEXT_USER = os.getenv('ERPNEXT_USER', 'Administrator')
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', 'admin')

OUTPUT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # 1. Login
        print("[1] Logging in...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 2. Open root URL directly: http://192.168.8.11:6888
        print("[2] Visiting root URL: http://192.168.8.11:6888 ...")
        await page.goto(f"{SITE_URL}/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        shot1 = os.path.join(OUTPUT_DIR, "live_acceptance_root_6888.png")
        await page.screenshot(path=shot1)
        print(f"[2] Screenshot saved: {shot1}")

        # Check modals and URL
        modals = await page.locator(".modal.show").count()
        curr_url = page.url
        print(f"[2] Current URL: {curr_url}")
        print(f"[2] Modal count: {modals} (0 is expected)")

        # 3. Test clicking a Category in sidebar: 仓库与库存
        print("[3] Clicking 仓库与库存...")
        clicked = await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.body-sidebar .standard-sidebar-item'));
            for (let item of items) {
                if (item.textContent.includes('仓库') || item.textContent.includes('库存')) {
                    item.click();
                    return item.textContent.trim();
                }
            }
            return null;
        }""")
        print(f"[3] Clicked: {clicked}")
        await asyncio.sleep(3)

        shot2 = os.path.join(OUTPUT_DIR, "live_acceptance_click_stock.png")
        await page.screenshot(path=shot2)
        print(f"[3] Screenshot saved: {shot2}")
        print(f"[3] Current URL: {page.url}")

        # 4. Test clicking 采购协同
        print("[4] Clicking 采购协同...")
        clicked2 = await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.body-sidebar .standard-sidebar-item'));
            for (let item of items) {
                if (item.textContent.includes('采购')) {
                    item.click();
                    return item.textContent.trim();
                }
            }
            return null;
        }""")
        print(f"[4] Clicked: {clicked2}")
        await asyncio.sleep(3)

        shot3 = os.path.join(OUTPUT_DIR, "live_acceptance_click_procurement.png")
        await page.screenshot(path=shot3)
        print(f"[4] Screenshot saved: {shot3}")
        print(f"[4] Current URL: {page.url}")

        await browser.close()
        print("\n[SUCCESS] All steps executed cleanly!")

asyncio.run(run())
