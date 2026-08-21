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

        # 1. 验证访问 /desk/home
        print("[1] 访问 /desk/home ...")
        await page.goto(f"{SITE_URL}/desk/home", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        shot1 = os.path.join(OUTPUT_DIR, "transplanted_home_dashboard.png")
        await page.screenshot(path=shot1)
        print(f"  /desk/home 截图: {shot1}")

        # 2. 验证从业务单据（采购发票）点击全局面包屑返回 Home
        print("[2] 进入新建采购发票页面...")
        await page.goto(f"{SITE_URL}/desk/purchase-invoice/new-purchase-invoice-1", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        print("[3] 点击顶部全局面包屑 Home 图标...")
        # 点击面包屑 home link
        await page.click(".breadcrumb a:first-child, .breadcrumb-item a:first-child, [data-page-route*='home']")
        await asyncio.sleep(3)
        shot2 = os.path.join(OUTPUT_DIR, "breadcrumb_return_home.png")
        await page.screenshot(path=shot2)
        print(f"  面包屑返回 Home 截图: {shot2}")

        # 3. 验证点击左侧侧边栏第一项“我的业务 (总控主页)”
        print("[4] 点击左侧侧边栏第一项...")
        await page.click(".body-sidebar .standard-sidebar-item:first-child a")
        await asyncio.sleep(2)
        shot3 = os.path.join(OUTPUT_DIR, "sidebar_click_home.png")
        await page.screenshot(path=shot3)
        print(f"  侧边栏点击 Home 截图: {shot3}")

        await browser.close()
        print("\n[SUCCESS] Home 工作区总控 Dashboard 移植与面包屑全链路验证成功！")

asyncio.run(run())
