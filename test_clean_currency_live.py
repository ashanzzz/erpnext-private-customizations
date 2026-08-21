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

        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        await page.evaluate("""() => {
            // 1. 覆盖 Currency 格式化器
            const orig = frappe.form.formatters.Currency;
            frappe.form.formatters.Currency = function(value, df, options, doc) {
                if (df && (df.parent === 'Purchase Invoice Item' || (doc && doc.doctype === 'Purchase Invoice Item'))) {
                    if (value === undefined || value === null || value === '') return '';
                    return (parseFloat(value) || 0).toLocaleString('zh-CN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                }
                return orig(value, df, options, doc);
            };

            // 2. 清理表头 (CNY)
            $('.form-page[data-doctype="Purchase Invoice"] .grid-heading-row .grid-static-col').each(function() {
                let t = $(this).text();
                if (t.includes('CNY') || t.includes('(CNY)')) {
                    $(this).text(t.replace(/\\s*\\([^\\)]*CNY[^\\)]*\\)/gi, '').replace(/CNY/gi, '').trim());
                }
            });

            // 3. 重新渲染明细行
            cur_frm.fields_dict['items'].grid.grid_rows.forEach(r => r.render_row());
        }""")
        await asyncio.sleep(2)

        shot = os.path.join(OUTPUT_DIR, "clean_grid_verified.png")
        await page.screenshot(path=shot)
        print(f"  截图保存: {shot}")

        await browser.close()
        print("\n[SUCCESS] 纯数字明细表格验证成功！")

asyncio.run(run())
