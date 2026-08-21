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

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        logs = []
        page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))

        await page.add_init_script("""
            const checkHook = setInterval(() => {
                if (window.frappe && frappe.views && frappe.views.pageview && !frappe.views.pageview._hooked) {
                    frappe.views.pageview._hooked = true;
                    const origShow = frappe.views.pageview.show;
                    frappe.views.pageview.show = function(name) {
                        const err = new Error('pageview.show called for: ' + name);
                        console.warn('[DEBUG_PAGEVIEW_SHOW] ' + name + ' -> STACK: ' + err.stack);
                        return origShow.apply(this, arguments);
                    };
                }
                if (window.frappe && frappe.show_not_found && !frappe.show_not_found._hooked) {
                    frappe.show_not_found._hooked = true;
                    const origNotFound = frappe.show_not_found;
                    frappe.show_not_found = function(name) {
                        const err = new Error('show_not_found called for: ' + name);
                        console.error('[DEBUG_SHOW_NOT_FOUND] ' + name + ' -> STACK: ' + err.stack);
                        return origNotFound.apply(this, arguments);
                    };
                }
            }, 10);
        """)

        # 1. Login
        print("Step 1: Login")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 2. Now open http://192.168.8.11:6888 in a new tab or navigation
        print("Step 2: Navigate to root URL http://192.168.8.11:6888")
        logs.clear()
        await page.goto(f"{SITE_URL}/", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        print("\n=== DEBUG CALL LOGS (Step 2) ===")
        for l in logs:
            if "DEBUG" in l:
                print(l)

        # Check if modal is present
        modals = await page.locator(".modal.show").count()
        print(f"Modals count on root URL: {modals}")

        await browser.close()

asyncio.run(run())
