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

        # 监听控制台日志
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        print("[1] 访问新建采购发票页面...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 检查 purchase_invoice_tax_calculator.js 是否加载到前端
        check_js = await page.evaluate("""() => {
            return {
                has_ashan_tax: !!window.ashan?.tax,
                has_custom_gross_rate_handler: !!frappe.ui.form.events?.['Purchase Invoice Item']?.custom_gross_rate,
                all_pi_item_handlers: Object.keys(frappe.ui.form.events?.['Purchase Invoice Item'] || {})
            };
        }""")
        print("JS 加载状态检查:", check_js)

        # 模拟在表格中选择物品、输入含税单价和数量
        print("\n[2] 模拟在前端录入物料、数量与含税单价...")
        sim_res = await page.evaluate("""() => {
            const cur_frm = cur_frm;
            if (!cur_frm) return { error: 'no cur_frm' };
            
            // 选供应商
            cur_frm.set_value('supplier', '天津市某某科技有限公司');
            
            // 添加一行物料
            const row = cur_frm.add_child('items', {
                item_code: 'ITEM-GOODS-13',
                qty: 5,
                custom_tax_rate: 13,
                custom_gross_rate: 113
            });
            
            // 触发 field change
            frappe.model.set_value(row.doctype, row.name, 'custom_gross_rate', 113);
            
            return {
                qty: row.qty,
                custom_gross_rate: row.custom_gross_rate,
                custom_tax_rate: row.custom_tax_rate,
                rate: row.rate,
                amount: row.amount,
                custom_tax_amount: row.custom_tax_amount,
                custom_gross_amount: row.custom_gross_amount,
                net_total: cur_frm.doc.net_total,
                grand_total: cur_frm.doc.grand_total
            };
        }""")
        print("录入含税单价模拟结果:", sim_res)

        shot1 = os.path.join(OUTPUT_DIR, "diag_enter_gross_rate.png")
        await page.screenshot(path=shot1)

        # 模拟在前端修改价税合计
        print("\n[3] 模拟在前端直接修改【价税合计】为 1130 元...")
        sim_gross_amount_res = await page.evaluate("""() => {
            const cur_frm = cur_frm;
            const row = cur_frm.doc.items[0];
            
            // 修改价税合计
            frappe.model.set_value(row.doctype, row.name, 'custom_gross_amount', 1130);
            
            return {
                qty: row.qty,
                custom_gross_rate: row.custom_gross_rate,
                custom_tax_rate: row.custom_tax_rate,
                rate: row.rate,
                amount: row.amount,
                custom_tax_amount: row.custom_tax_amount,
                custom_gross_amount: row.custom_gross_amount,
                net_total: cur_frm.doc.net_total,
                grand_total: cur_frm.doc.grand_total
            };
        }""")
        print("修改价税合计模拟结果:", sim_gross_amount_res)

        shot2 = os.path.join(OUTPUT_DIR, "diag_enter_gross_amount.png")
        await page.screenshot(path=shot2)

        print("\nConsole Logs (最近 15 条):")
        for log in console_logs[-15:]:
            print(" ", log)

        await browser.close()

asyncio.run(run())
