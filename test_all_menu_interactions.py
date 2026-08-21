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
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', '')

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

        # 2. Initial Landing on My Business
        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        shot0 = os.path.join(OUTPUT_DIR, "menu_test_0_initial.png")
        await page.screenshot(path=shot0)
        print(f"[2] Initial landing screenshot: {shot0}")

        # ---- Test 1: Click Level 1 Category Header [仓库与库存] ----
        print("\n[3] Test 1: Click Level 1 Category Header [仓库与库存]...")
        click_res_1 = await page.evaluate("""() => {
            const sections = Array.from(document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item'));
            for (let s of sections) {
                if (s.textContent.includes('仓库') || s.textContent.includes('库存')) {
                    s.click();
                    return { found: true, text: s.textContent.trim() };
                }
            }
            return { found: false };
        }""")
        print(f"[3] Click result: {click_res_1}")
        await asyncio.sleep(3)

        print(f"[3] Current URL: {page.url}")
        sidebar_count_1 = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.length")
        print(f"[3] Total sidebar items count: {sidebar_count_1}")

        shot1 = os.path.join(OUTPUT_DIR, "menu_test_1_click_l1_stock.png")
        await page.screenshot(path=shot1)
        print(f"[3] Screenshot 1 saved: {shot1}")

        # ---- Test 2: Click Level 2 Submenu Item [物料主数据] ----
        print("\n[4] Test 2: Click Level 2 Submenu Item [物料主数据]...")
        click_res_2 = await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor'));
            for (let it of items) {
                if (it.textContent.includes('物料主数据') || it.textContent.includes('物料')) {
                    it.click();
                    return { found: true, text: it.textContent.trim(), href: it.getAttribute('href') };
                }
            }
            return { found: false };
        }""")
        print(f"[4] Click result: {click_res_2}")
        await asyncio.sleep(3)

        print(f"[4] Current URL: {page.url}")
        sidebar_count_2 = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.length")
        print(f"[4] Total sidebar items count: {sidebar_count_2}")

        shot2 = os.path.join(OUTPUT_DIR, "menu_test_2_click_l2_item.png")
        await page.screenshot(path=shot2)
        print(f"[4] Screenshot 2 saved: {shot2}")

        # ---- Test 3: Click another Level 2 Submenu Item [采购订单] ----
        print("\n[5] Test 3: Click another Level 2 Submenu Item [采购订单]...")
        click_res_3 = await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor'));
            for (let it of items) {
                if (it.textContent.includes('采购订单')) {
                    it.click();
                    return { found: true, text: it.textContent.trim(), href: it.getAttribute('href') };
                }
            }
            return { found: false };
        }""")
        print(f"[5] Click result: {click_res_3}")
        await asyncio.sleep(3)

        print(f"[5] Current URL: {page.url}")
        sidebar_count_3 = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.length")
        print(f"[5] Total sidebar items count: {sidebar_count_3}")

        shot3 = os.path.join(OUTPUT_DIR, "menu_test_3_click_l2_purchase_order.png")
        await page.screenshot(path=shot3)
        print(f"[5] Screenshot 3 saved: {shot3}")

        # ---- Test 4: Click Level 1 Header [企业合规中心] ----
        print("\n[6] Test 4: Click Level 1 Header [企业合规中心]...")
        click_res_4 = await page.evaluate("""() => {
            const sections = Array.from(document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item'));
            for (let s of sections) {
                if (s.textContent.includes('合规') || s.textContent.includes('企业合规')) {
                    s.click();
                    return { found: true, text: s.textContent.trim() };
                }
            }
            return { found: false };
        }""")
        print(f"[6] Click result: {click_res_4}")
        await asyncio.sleep(3)

        print(f"[6] Current URL: {page.url}")
        sidebar_count_4 = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.length")
        print(f"[6] Total sidebar items count: {sidebar_count_4}")

        shot4 = os.path.join(OUTPUT_DIR, "menu_test_4_click_l1_compliance.png")
        await page.screenshot(path=shot4)
        print(f"[6] Screenshot 4 saved: {shot4}")

        await browser.close()
        print("\n[ALL SUCCESS] Finished all 4 interactive menu tests cleanly!")

asyncio.run(run())
