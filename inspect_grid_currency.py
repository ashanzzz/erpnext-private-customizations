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
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        grid_info = await page.evaluate("""() => {
            const grid = cur_frm.fields_dict['items'].grid;
            const headers = Array.from(document.querySelectorAll('.form-page[data-doctype="Purchase Invoice"] .grid-heading-row .col'))
                .map(el => el.innerText.trim());
            const row_cells = Array.from(document.querySelectorAll('.form-page[data-doctype="Purchase Invoice"] .grid-row:not(.grid-heading-row) .col'))
                .map(el => el.innerText.trim());
            
            return {
                headers: headers,
                row_cells: row_cells,
                docfields: grid.docfields.filter(df => df.in_list_view).map(df => ({
                    fieldname: df.fieldname,
                    label: df.label,
                    fieldtype: df.fieldtype,
                    options: df.options
                }))
            };
        }""")
        print("Grid Info:")
        import pprint
        pprint.pprint(grid_info)

        await browser.close()

asyncio.run(run())
