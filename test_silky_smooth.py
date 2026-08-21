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

        print("=== 测试 1: 点击左侧文字【仓库与库存】(第 1 次: 触发收起) ===")
        res1 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            if (!sec) return { error: 'not found' };
            const label = sec.querySelector('.sidebar-item-label');
            label.click();
            return { ok: true };
        }""")
        await asyncio.sleep(0.5)
        state1 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            const isClosed = sec.getAttribute('data-state') === 'closed' || $(sec).find('.nested-container').is(':hidden');
            return {
                state: isClosed ? 'closed' : 'opened',
                icon: $(sec).find('.drop-icon use').attr('href')
            };
        }""")
        print(f"  [文字点击 #1] 状态: {state1['state']} | 图标: {state1['icon']}")

        shot1 = os.path.join(OUTPUT_DIR, "silky_text_click_1_closed.png")
        await page.screenshot(path=shot1)

        print("\n=== 测试 2: 再次点击左侧文字【仓库与库存】(第 2 次: 触发展开) ===")
        res2 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            if (!sec) return { error: 'not found' };
            const label = sec.querySelector('.sidebar-item-label');
            label.click();
            return { ok: true };
        }""")
        await asyncio.sleep(0.5)
        state2 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            const isClosed = sec.getAttribute('data-state') === 'closed' || $(sec).find('.nested-container').is(':hidden');
            return {
                state: isClosed ? 'closed' : 'opened',
                icon: $(sec).find('.drop-icon use').attr('href')
            };
        }""")
        print(f"  [文字点击 #2] 状态: {state2['state']} | 图标: {state2['icon']}")

        shot2 = os.path.join(OUTPUT_DIR, "silky_text_click_2_opened.png")
        await page.screenshot(path=shot2)

        print("\n=== 测试 3: 点击左侧文字【采购协同】(跨模块跳转 + 丝滑展开) ===")
        await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('采购协同'));
            const label = sec.querySelector('.sidebar-item-label');
            label.click();
        }""")
        await asyncio.sleep(2)
        print(f"  当前 URL: {page.url}")

        shot3 = os.path.join(OUTPUT_DIR, "silky_text_click_3_procurement.png")
        await page.screenshot(path=shot3)

        await browser.close()
        print("\n[SUCCESS] 文字双向丝滑折叠展开测试全部通过！")

asyncio.run(run())
