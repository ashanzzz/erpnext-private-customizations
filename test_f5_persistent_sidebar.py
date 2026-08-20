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

        print("[1] 直接访问新建采购发票页面...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        print("[2] 在单据页面执行浏览器 F5 强刷...")
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(4)

        shot = os.path.join(OUTPUT_DIR, "persistent_sidebar_after_f5.png")
        await page.screenshot(path=shot)
        print(f"  截图保存: {shot}")

        check = await page.evaluate("""() => {
            const sidebar = frappe.workspace?.sidebar || frappe.app?.sidebar;
            const labels = Array.from(document.querySelectorAll('.standard-sidebar-section .sidebar-item-label, .desk-sidebar .sidebar-item-label')).map(el => el.textContent.trim());
            return {
                sidebar_title: sidebar?.sidebar_title,
                header_subtitle: sidebar?.header_subtitle,
                has_warehouse: labels.some(l => l.includes('仓库') || l.includes('库存')),
                has_procurement: labels.some(l => l.includes('采购协同') || l.includes('采购')),
                has_finance: labels.some(l => l.includes('财务') || l.includes('报销')),
                labels: labels
            };
        }""")
        print("F5 刷新后侧边栏检查结果:", check)

        await browser.close()
        print("\n[SUCCESS] F5 刷新侧边栏持久化验证完成！")

asyncio.run(run())
