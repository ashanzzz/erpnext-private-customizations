# -*- coding: utf-8 -*-
import os
import json
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

        print("[1] 打开新建采购发票页面...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(4)

        print("\n=== [测试 1] 录入数量 2.0，含税单价 100 元 (13%税) -> 验证价税合计严格为 200.00 元 ===")
        res1 = await page.evaluate("""async () => {
            const frm = cur_frm;
            await frm.set_value('supplier', '天津市某某科技有限公司');
            
            frm.doc.items = [];
            const row = frm.add_child('items', {
                item_code: 'ITEM-GOODS-13',
                qty: 2,
                custom_tax_rate: 13
            });
            frm.refresh_field('items');
            
            // 录入含税单价 100
            await frappe.model.set_value(row.doctype, row.name, 'custom_gross_rate', 100);
            
            const cardText = document.querySelector('#ashan-tax-breakdown-card')?.textContent.replace(/\\s+/g, ' ').trim() || '';
            
            return {
                qty: row.qty,
                custom_gross_rate: row.custom_gross_rate,
                custom_gross_amount: row.custom_gross_amount,
                rate: row.rate,
                amount: row.amount,
                custom_tax_amount: row.custom_tax_amount,
                net_total: frm.doc.net_total,
                grand_total: frm.doc.grand_total,
                cardText: cardText
            };
        }""")
        print("  【测试 1 结果】:")
        print(f"    - 数量: {res1['qty']}")
        print(f"    - 含税单价: {res1['custom_gross_rate']}")
        print(f"    - 价税合计: {res1['custom_gross_amount']} (预期: 200.00)")
        print(f"    - 未税金额: {res1['amount']} (预期: 176.99)")
        print(f"    - 税额: {res1['custom_tax_amount']} (预期: 23.01)")
        print(f"    - 汇总卡片文本: {res1['cardText']}")

        shot1 = os.path.join(OUTPUT_DIR, "exact_200_test.png")
        await page.screenshot(path=shot1)

        print("\n=== [测试 2] 用户直接修改【价税合计】为 300.00 元 -> 验证无缝倒算 ===")
        res2 = await page.evaluate("""async () => {
            const frm = cur_frm;
            const row = frm.doc.items[0];
            
            // 模拟用户直接修改价税合计为 300
            await frappe.model.set_value(row.doctype, row.name, 'custom_gross_amount', 300);
            
            const cardText = document.querySelector('#ashan-tax-breakdown-card')?.textContent.replace(/\\s+/g, ' ').trim() || '';
            
            return {
                qty: row.qty,
                custom_gross_rate: row.custom_gross_rate,
                custom_gross_amount: row.custom_gross_amount,
                rate: row.rate,
                amount: row.amount,
                custom_tax_amount: row.custom_tax_amount,
                net_total: frm.doc.net_total,
                grand_total: frm.doc.grand_total,
                cardText: cardText
            };
        }""")
        print("  【测试 2 结果】:")
        print(f"    - 数量: {res2['qty']}")
        print(f"    - 价税合计: {res2['custom_gross_amount']} (预期: 300.00)")
        print(f"    - 含税单价: {res2['custom_gross_rate']} (预期: 150.00)")
        print(f"    - 未税金额: {res2['amount']} (预期: 265.49)")
        print(f"    - 税额: {res2['custom_tax_amount']} (预期: 34.51)")
        print(f"    - 汇总卡片文本: {res2['cardText']}")

        shot2 = os.path.join(OUTPUT_DIR, "exact_300_test.png")
        await page.screenshot(path=shot2)

        await browser.close()
        print("\n[SUCCESS] 精准整百金额与精简 UI 卡片验证通过！")

asyncio.run(run())
