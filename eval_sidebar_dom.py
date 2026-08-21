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

        eval_data = await page.evaluate("""() => {
            // Trigger sync
            let sb = frappe.app?.sidebar;
            let current_ws = frappe.workspace;
            return {
                workspace_current_page_name: current_ws?.current_page_name,
                workspace_public_items: Object.keys(current_ws?.sidebar_items?.public || {}),
                sidebar_wrapper_html_length: $('.body-sidebar').html()?.length,
                all_standard_items_in_dom: $('.body-sidebar .standard-sidebar-item').length,
                all_dom_text: $('.body-sidebar').text()?.substring(0, 200)
            };
        }""")

        import pprint
        print("EVAL DATA:")
        pprint.pprint(eval_data)

        # Force re-render sidebar in browser
        await page.evaluate("""() => {
            let masterSidebar = null;
            for (let k in frappe.boot.workspace_sidebar_item) {
                let s = frappe.boot.workspace_sidebar_item[k];
                if (s && s.items && s.items.length >= 25) { masterSidebar = s; break; }
            }
            if (masterSidebar && frappe.app?.sidebar) {
                frappe.app.sidebar.sidebar_data = masterSidebar;
                frappe.app.sidebar.workspace_sidebar_items = masterSidebar.items;
                frappe.app.sidebar.find_nested_items();
                frappe.app.sidebar.make_sidebar();
            }
        }""")
        await asyncio.sleep(1)

        shot = os.path.join(OUTPUT_DIR, "forced_sidebar_render.png")
        await page.screenshot(path=shot)
        print(f"Forced render screenshot: {shot}")

        dom_items = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.map(e => e.textContent.trim().substring(0, 30))")
        print(f"After forced render: {len(dom_items)} items:", dom_items[:8])

        await browser.close()

asyncio.run(run())
