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

        find_res = await page.evaluate("""() => {
            // Find sidebar object anywhere
            const results = [];
            for (let k in frappe) {
                try {
                    if (frappe[k] && typeof frappe[k] === 'object') {
                        if (frappe[k].sidebar || frappe[k].workspace_sidebar_items || frappe[k].make_sidebar) {
                            results.push(`frappe.${k}`);
                        }
                    }
                } catch(e){}
            }
            if (frappe.workspace) {
                for (let k in frappe.workspace) {
                    if (k.toLowerCase().includes('side')) results.push(`frappe.workspace.${k}`);
                }
            }
            // Check jquery data on .body-sidebar
            const dom_data = $('.body-sidebar').data();
            return {
                frappe_results: results,
                dom_data_keys: Object.keys(dom_data || {}),
                body_sidebar_wrapper_id: $('.body-sidebar').parent().attr('id') || $('.body-sidebar').parent().attr('class')
            };
        }""")

        import pprint
        print("FIND RESULTS:")
        pprint.pprint(find_res)

        await browser.close()

asyncio.run(run())
