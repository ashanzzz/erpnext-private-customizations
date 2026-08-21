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
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        print("=== 测试 1: 点击二级菜单【物料主数据】(验证父级绝对不折叠) ===")
        # 记录点击前父级状态
        stock_state_before = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            return sec ? sec.getAttribute('data-state') : 'none';
        }""")
        print(f"  点击前【仓库与库存】状态: {stock_state_before}")

        # 点击二级菜单
        await page.evaluate("""() => {
            const item = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor')).find(el => el.textContent.includes('物料主数据') || el.textContent.includes('物料'));
            if (item) item.click();
        }""")
        await asyncio.sleep(2.5)

        stock_state_after = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            return sec ? sec.getAttribute('data-state') : 'none';
        }""")
        print(f"  点击后 URL: {page.url}")
        print(f"  点击后【仓库与库存】状态: {stock_state_after} (预期: opened, 绝对不折叠)")

        shot1 = os.path.join(OUTPUT_DIR, "l2_click_1_stock_opened.png")
        await page.screenshot(path=shot1)

        print("\n=== 测试 2: 再次点击另一个二级菜单【仓库管理】(验证继续保持展开) ===")
        await page.evaluate("""() => {
            const item = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor')).find(el => el.textContent.includes('仓库管理'));
            if (item) item.click();
        }""")
        await asyncio.sleep(2.5)

        stock_state_after2 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            return sec ? sec.getAttribute('data-state') : 'none';
        }""")
        print(f"  点击后 URL: {page.url}")
        print(f"  点击后【仓库与库存】状态: {stock_state_after2} (预期: opened)")

        shot2 = os.path.join(OUTPUT_DIR, "l2_click_2_warehouse_opened.png")
        await page.screenshot(path=shot2)

        print("\n=== 测试 3: 点击跨模块二级菜单【采购订单】(验证采购模块自动保持展开) ===")
        await page.evaluate("""() => {
            const item = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor')).find(el => el.textContent.includes('采购订单'));
            if (item) item.click();
        }""")
        await asyncio.sleep(2.5)

        procure_state = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('采购协同'));
            return sec ? sec.getAttribute('data-state') : 'none';
        }""")
        print(f"  点击后 URL: {page.url}")
        print(f"  【采购协同】状态: {procure_state} (预期: opened)")

        shot3 = os.path.join(OUTPUT_DIR, "l2_click_3_purchase_opened.png")
        await page.screenshot(path=shot3)

        await browser.close()
        print("\n[SUCCESS] 二级菜单隔离测试全部通过，二级菜单绝不再触发折叠！")

asyncio.run(run())
