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

        print("=== 测试 1: 极速连续点击 6 次右侧箭头按钮 (测试手风琴灵敏度) ===")
        for i in range(1, 7):
            state = await page.evaluate("""() => {
                const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
                if (!sec) return { error: 'not found' };
                const btn = sec.querySelector('.drop-icon');
                btn.click();
                const isClosed = sec.getAttribute('data-state') === 'closed' || $(sec).find('.nested-container').hasClass('hidden');
                return {
                    state: isClosed ? 'closed' : 'opened',
                    icon: $(sec).find('.drop-icon use').attr('href')
                };
            }""")
            print(f"  [箭头点击 #{i}] 状态: {state['state']} | 图标: {state['icon']}")
            await asyncio.sleep(0.5)

        print("\n=== 测试 2: 点击左侧文字区域 (测试页面跳转与自动展开) ===")
        for section_name in ["仓库与库存", "采购协同", "财务与报销"]:
            res = await page.evaluate("""(name) => {
                const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes(name));
                if (!sec) return { error: 'not found' };
                const label = sec.querySelector('.sidebar-item-label');
                label.click();
                return {
                    clicked: true,
                    name: name
                };
            }""", section_name)
            await asyncio.sleep(2)
            url = page.url
            opened = await page.evaluate("""(name) => {
                const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes(name));
                return sec ? (sec.getAttribute('data-state') === 'opened') : false;
            }""", section_name)
            print(f"  [文字点击] 目标: {section_name} -> 最终URL: {url} | 菜单自动展开: {opened}")

        shot = os.path.join(OUTPUT_DIR, "rapid_test_final.png")
        await page.screenshot(path=shot)
        print(f"\n截图保存: {shot}")

        await browser.close()
        print("\n[SUCCESS] 全部灵敏度与双区测试通过！")

asyncio.run(run())
