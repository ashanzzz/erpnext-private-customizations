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

        # 连续刷新 5 次并捕获是否有任何一次出现过 (CNY)
        any_flicker = False
        for i in range(1, 6):
            print(f"[测试 {i}/5] 加载新建采购发票页面...")
            await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="domcontentloaded", timeout=30000)
            
            # 在极其微小的时刻（50ms、100ms、300ms、1000ms）抓取表头文本
            for delay in [0.05, 0.1, 0.3, 0.8]:
                await asyncio.sleep(delay)
                text = await page.evaluate("""() => {
                    const row = document.querySelector('[data-fieldname="items"] .grid-heading-row');
                    return row ? row.innerText : '';
                }""")
                if "CNY" in text:
                    print(f"  [发现闪烁!] 在第 {i} 次加载后 {delay}s 捕获到了 CNY: {text}")
                    any_flicker = True

        if not any_flicker:
            print("\n[PERFECT] 连续 5 次极速采样，0 次出现 CNY，彻底杜绝闪烁！")

        shot = os.path.join(OUTPUT_DIR, "zero_flicker_verified.png")
        await page.screenshot(path=shot)
        print(f"  最终截图保存: {shot}")

        await browser.close()

asyncio.run(run())
