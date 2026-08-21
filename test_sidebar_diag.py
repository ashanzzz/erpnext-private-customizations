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

        # Login
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        # Clear localStorage & reload to fetch fresh bootinfo
        await page.evaluate("() => localStorage.clear()")
        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        diag = await page.evaluate("""() => {
            const sb = frappe.app?.sidebar;
            return {
                sidebar_title: sb?.sidebar_title,
                workspace_sidebar_items_len: sb?.workspace_sidebar_items?.length || 0,
                boot_my_business_len: frappe.boot?.workspace_sidebar_item?.['my business']?.items?.length || 0,
                body_sidebar_html: $('.body-sidebar').html()?.length,
                rendered_items: $('.body-sidebar .standard-sidebar-item').length
            };
        }""")
        print("DIAGNOSTIC DATA:", diag)

        shot1 = os.path.join(OUTPUT_DIR, "live_landing_diag.png")
        await page.screenshot(path=shot1)
        print(f"Screenshot saved: {shot1}")

        # If items not rendered, check what make_sidebar does
        if diag['rendered_items'] <= 1:
            res = await page.evaluate("""() => {
                const sb = frappe.app?.sidebar;
                sb.setup('My Business');
                return {
                    after_setup_items: $('.body-sidebar .standard-sidebar-item').length
                };
            }""")
            print("AFTER sb.setup('My Business'):", res)
            await asyncio.sleep(2)
            shot2 = os.path.join(OUTPUT_DIR, "after_sb_setup.png")
            await page.screenshot(path=shot2)
            print(f"Screenshot 2 saved: {shot2}")

        await browser.close()

asyncio.run(run())
