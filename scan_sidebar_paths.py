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

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        info = await page.evaluate("""() => {
            let container_page = frappe.container?.page;
            let standard_ws = frappe.standard_pages?.Workspaces;
            let pageview_pages = Object.keys(frappe.views?.pageview?.pages || {});
            
            // Search all properties on window and frappe for an instance of Sidebar
            let sidebar_paths = [];
            function scan(obj, path, depth) {
                if (!obj || depth > 3) return;
                try {
                    for (let k in obj) {
                        if (k === 'sidebar' && obj[k]) {
                            sidebar_paths.push(`${path}.${k}`);
                        }
                    }
                } catch(e){}
            }
            scan(window, 'window', 1);
            scan(frappe, 'frappe', 1);
            scan(frappe.container, 'frappe.container', 1);
            scan(frappe.views, 'frappe.views', 1);
            scan(frappe.desk, 'frappe.desk', 1);
            scan(standard_ws, 'standard_ws', 1);

            return {
                sidebar_paths,
                pageview_pages,
                container_page_name: container_page?.page_name
            };
        }""")

        import pprint
        print("EXACT SIDEBAR PATHS:")
        pprint.pprint(info)

        await browser.close()

asyncio.run(run())
