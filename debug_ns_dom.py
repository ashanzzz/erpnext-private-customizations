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

        await page.goto(f"{SITE_URL}/desk/purchase-invoice/ACC-PINV-2026-00001", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        info = await page.evaluate("""() => {
            const frm = cur_frm;
            const ns_ctrl = frm.fields_dict.naming_series;
            return {
                doc_name: frm.doc.name,
                naming_series_val: frm.doc.naming_series,
                has_ctrl: !!ns_ctrl,
                disp_status: ns_ctrl ? ns_ctrl.disp_status : null,
                df_hidden: ns_ctrl ? ns_ctrl.df.hidden : null,
                wrapper_visible: ns_ctrl ? ns_ctrl.$wrapper.is(':visible') : null,
                wrapper_classes: ns_ctrl ? ns_ctrl.$wrapper.attr('class') : null,
                wrapper_parent: ns_ctrl ? ns_ctrl.$wrapper.parent().attr('class') : null
            };
        }""")
        print("naming_series DOM Info:", info)

        # Now let's try to unhide it via JS in browser
        await page.evaluate("""() => {
            cur_frm.toggle_display('naming_series', true);
            cur_frm.set_df_property('naming_series', 'hidden', 0);
            cur_frm.set_df_property('naming_series', 'read_only', 1);
            cur_frm.fields_dict.naming_series.$wrapper.show().removeClass('hide-control hide');
        }""")
        await asyncio.sleep(1)

        info2 = await page.evaluate("""() => {
            const ns_ctrl = cur_frm.fields_dict.naming_series;
            return {
                disp_status: ns_ctrl.disp_status,
                wrapper_visible: ns_ctrl.$wrapper.is(':visible'),
                wrapper_classes: ns_ctrl.$wrapper.attr('class')
            };
        }""")
        print("After unhide naming_series DOM Info:", info2)

        shot = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\debug_unhide_series.png"
        await page.screenshot(path=shot)
        print("Screenshot saved to:", shot)

        await browser.close()

asyncio.run(run())
