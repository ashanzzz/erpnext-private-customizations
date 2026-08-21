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
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        print("[1] 打开新建采购发票页面...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 1. 切换为【无发票】
        print("[2] 切换发票类型为【无发票】...")
        await page.evaluate("""async () => {
            const frm = cur_frm;
            await frm.set_value('custom_invoice_type', '无发票');
        }""")
        await asyncio.sleep(2)
        shot1 = os.path.join(OUTPUT_DIR, "inv_type_no_invoice.png")
        await page.screenshot(path=shot1)
        print(f"  截图保存: {shot1}")

        # 2. 切换为【专用发票】并输入已存在发票号 FP-2026-88888888
        print("[3] 切换发票类型为【专用发票】并测试重复发票号...")
        await page.evaluate("""async () => {
            const frm = cur_frm;
            await frm.set_value('custom_invoice_type', '专用发票');
            await frm.set_value('bill_no', 'FP-2026-88888888');
            ashan.tax.check_bill_no_duplicate(frm);
        }""")
        await asyncio.sleep(2)
        shot2 = os.path.join(OUTPUT_DIR, "inv_type_duplicate_warning.png")
        await page.screenshot(path=shot2)
        print(f"  截图保存: {shot2}")

        # 3. 输入合法唯一发票号 FP-2026-99999999
        print("[4] 输入合法唯一发票号...")
        await page.evaluate("""async () => {
            const frm = cur_frm;
            if (frappe.msgprint_dialog) {
                frappe.msgprint_dialog.hide();
            }
            await frm.set_value('bill_no', 'FP-2026-99999999');
            ashan.tax.check_bill_no_duplicate(frm);
        }""")
        await asyncio.sleep(2)
        shot3 = os.path.join(OUTPUT_DIR, "inv_type_valid_success.png")
        await page.screenshot(path=shot3)
        print(f"  截图保存: {shot3}")

        await browser.close()
        print("\n[SUCCESS] 浏览器全流程发票类型与防重联动验收完成！")

asyncio.run(run())
