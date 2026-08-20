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

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # 1. Login
        print("[1] 登录...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 2. 初始着陆页
        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        shot0 = os.path.join(OUTPUT_DIR, "menu_test_0_initial.png")
        await page.screenshot(path=shot0)
        print(f"[2] 初始主控页截图: {shot0}")

        # ---- 测试 1: 点击一级分类菜单【仓库与库存】----
        print("\n[3] 测试 1: 点击一级分类菜单【仓库与库存】...")
        # 记录点击前的 URL
        before_url_1 = page.url

        # 点击【仓库与库存】分类标题
        click_res_1 = await page.evaluate("""() => {
            const sections = Array.from(document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item'));
            for (let s of sections) {
                if (s.textContent.includes('仓库') || s.textContent.includes('库存')) {
                    s.click();
                    return { found: true, text: s.textContent.trim() };
                }
            }
            return { found: false };
        }""")
        print(f"[3] 点击结果: {click_res_1}")
        await asyncio.sleep(3)

        after_url_1 = page.url
        print(f"[3] 点击后 URL: {after_url_1}")

        # 检查右侧主内容标题与侧边栏项目数
        ws_title_1 = await page.eval_on_selector(".layout-main-section", "el => el.textContent.substring(0, 150).replace(/\\s+/g, ' ')")
        sidebar_count_1 = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.length")
        print(f"[3] 右侧区域文字摘要: {ws_title_1[:80]}")
        print(f"[3] 侧边栏菜单项总数: {sidebar_count_1}")

        shot1 = os.path.join(OUTPUT_DIR, "menu_test_1_click_l1_stock.png")
        await page.screenshot(path=shot1)
        print(f"[3] 测试 1 截图: {shot1}")

        # ---- 测试 2: 点击二级子菜单【物料主数据】(纯文字无图标) ----
        print("\n[4] 测试 2: 点击二级子菜单【物料主数据】...")
        before_url_2 = page.url

        click_res_2 = await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor'));
            for (let it of items) {
                if (it.textContent.includes('物料主数据') || it.textContent.includes('物料')) {
                    it.click();
                    return { found: true, text: it.textContent.trim(), href: it.getAttribute('href') };
                }
            }
            return { found: false };
        }""")
        print(f"[4] 点击结果: {click_res_2}")
        await asyncio.sleep(3)

        after_url_2 = page.url
        print(f"[4] 点击后 URL: {after_url_2}")

        page_title_2 = await page.eval_on_selector(".page-title, .title-text, .list-header", "el => el.textContent.trim()").catch(lambda e: "N/A")
        print(f"[4] 当前页面主标题: {page_title_2}")

        sidebar_count_2 = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.length")
        print(f"[4] 侧边栏菜单项总数: {sidebar_count_2}")

        shot2 = os.path.join(OUTPUT_DIR, "menu_test_2_click_l2_item.png")
        await page.screenshot(path=shot2)
        print(f"[4] 测试 2 截图: {shot2}")

        # ---- 测试 3: 点击另一个二级子菜单【采购订单】----
        print("\n[5] 测试 3: 点击另一个二级子菜单【采购订单】...")
        click_res_3 = await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor'));
            for (let it of items) {
                if (it.textContent.includes('采购订单')) {
                    it.click();
                    return { found: true, text: it.textContent.trim(), href: it.getAttribute('href') };
                }
            }
            return { found: false };
        }""")
        print(f"[5] 点击结果: {click_res_3}")
        await asyncio.sleep(3)

        after_url_3 = page.url
        print(f"[5] 点击后 URL: {after_url_3}")

        page_title_3 = await page.eval_on_selector(".page-title, .title-text, .list-header", "el => el.textContent.trim()").catch(lambda e: "N/A")
        print(f"[5] 当前页面主标题: {page_title_3}")

        sidebar_count_3 = await page.eval_on_selector_all(".body-sidebar .standard-sidebar-item", "els => els.length")
        print(f"[5] 侧边栏菜单项总数: {sidebar_count_3}")

        shot3 = os.path.join(OUTPUT_DIR, "menu_test_3_click_l2_purchase_order.png")
        await page.screenshot(path=shot3)
        print(f"[5] 测试 3 截图: {shot3}")

        await browser.close()
        print("\n[SUCCESS] 全部菜单点击测试执行完毕！")

asyncio.run(run())
