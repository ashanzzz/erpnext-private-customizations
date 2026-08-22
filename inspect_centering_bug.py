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
        # Use 1920x1080 to clearly see wide screen centering
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 访问 ACC-PINV-2026-00001 在 1920 宽屏下的布局
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/ACC-PINV-2026-00001", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        shot1 = os.path.join(OUTPUT_DIR, "invoice_1920_left_bug.png")
        await page.screenshot(path=shot1)
        print(f"1920宽屏下截图: {shot1}")

        # 分析各层 DOM 宽度与 margin
        dom_analysis = await page.evaluate("""() => {
            function getInfo(sel) {
                const el = document.querySelector(sel);
                if (!el) return null;
                const cs = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return {
                    sel: sel,
                    width: cs.width,
                    maxWidth: cs.maxWidth,
                    marginLeft: cs.marginLeft,
                    marginRight: cs.marginRight,
                    left: rect.left,
                    right: rect.right,
                    rectWidth: rect.width
                };
            }
            return [
                getInfo('.page-container'),
                getInfo('.page-body'),
                getInfo('.layout-main'),
                getInfo('.layout-main-section-wrapper'),
                getInfo('.layout-main-section'),
                getInfo('.std-form-layout'),
                getInfo('.form-section'),
                getInfo('.section-body'),
                getInfo('.form-footer-section')
            ];
        }""")
        print("DOM ANALYSIS:")
        for d in dom_analysis:
            print(" ", d)

        await browser.close()

asyncio.run(run())
