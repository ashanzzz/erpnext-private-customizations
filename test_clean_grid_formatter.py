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

        res = await page.evaluate("""() => {
            // 测试设置 docfield_map formatter
            const num_fields = ["custom_gross_rate", "rate", "amount", "custom_tax_amount", "custom_gross_amount"];
            num_fields.forEach(fn => {
                if (frappe.meta.docfield_map["Purchase Invoice Item"] && frappe.meta.docfield_map["Purchase Invoice Item"][fn]) {
                    frappe.meta.docfield_map["Purchase Invoice Item"][fn].formatter = function(val) {
                        if (val === undefined || val === null || val === "") return "";
                        return (parseFloat(val) || 0).toLocaleString('zh-CN', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });
                    };
                }
            });

            // 清理表头标题
            document.querySelectorAll('.form-page[data-doctype="Purchase Invoice"] .grid-heading-row .col').forEach(el => {
                el.innerText = el.innerText.replace(/\\(CNY\\)/g, '').trim();
            });

            cur_frm.fields_dict['items'].grid.refresh();

            // 再次抓取当前单元格内容
            const cells = Array.from(document.querySelectorAll('.form-page[data-doctype="Purchase Invoice"] .grid-row:not(.grid-heading-row) .col'))
                .map(el => el.innerText.trim());
            const headers = Array.from(document.querySelectorAll('.form-page[data-doctype="Purchase Invoice"] .grid-heading-row .col'))
                .map(el => el.innerText.trim());

            return { headers: headers, cells: cells };
        }""")

        print("Formatter Test Result:", res)
        await asyncio.sleep(2)

        shot = os.path.join(OUTPUT_DIR, "clean_grid_no_cny.png")
        await page.screenshot(path=shot)
        print(f"  截图保存: {shot}")

        await browser.close()

asyncio.run(run())
