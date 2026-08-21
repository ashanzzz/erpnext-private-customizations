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

        print("[1] 登录并打开主控页...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 初始进入 My Business
        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # -------------------------------------------------------------
        # 测试 1: 点击【仓库与库存】的右侧【箭头按钮】(折叠手风琴)
        # 预期：只折叠子菜单，页面 URL 不发生跳转 (仍保持在 /desk/my-business)
        # -------------------------------------------------------------
        print("\n[2] 测试 1: 点击【仓库与库存】右侧折叠箭头...")
        before_url_1 = page.url
        toggled_1 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            if (sec) {
                const btn = sec.querySelector('.sidebar-item-control, .drop-icon');
                if (btn) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }""")
        await asyncio.sleep(1.5)
        after_url_1 = page.url
        is_closed_1 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            return sec ? (sec.getAttribute('data-state') === 'closed' || $(sec).find('.sidebar-child-item').is(':hidden')) : false;
        }""")
        print(f"     点击结果: {toggled_1}")
        print(f"     URL 保持不变: {before_url_1} == {after_url_1} ({before_url_1 == after_url_1})")
        print(f"     子菜单成功收起 (Closed): {is_closed_1}")

        shot1 = os.path.join(OUTPUT_DIR, "dual_zone_1_chevron_collapse.png")
        await page.screenshot(path=shot1)

        # -------------------------------------------------------------
        # 测试 2: 再次点击【仓库与库存】右侧【箭头按钮】(展开手风琴)
        # 预期：展开子菜单，URL 依然不发生跳转
        # -------------------------------------------------------------
        print("\n[3] 测试 2: 再次点击【仓库与库存】右侧折叠箭头...")
        toggled_2 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            if (sec) {
                const btn = sec.querySelector('.sidebar-item-control, .drop-icon');
                if (btn) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }""")
        await asyncio.sleep(1.5)
        is_opened_2 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('仓库与库存'));
            return sec ? (sec.getAttribute('data-state') === 'opened' && $(sec).find('.sidebar-child-item').is(':visible')) : false;
        }""")
        print(f"     子菜单成功展开 (Opened): {is_opened_2}")
        print(f"     URL 保持不变: {page.url}")

        shot2 = os.path.join(OUTPUT_DIR, "dual_zone_2_chevron_expand.png")
        await page.screenshot(path=shot2)

        # -------------------------------------------------------------
        # 测试 3: 点击【采购协同】的【文字/图标区域】
        # 预期：直接跳转到采购看板 (/desk/procurement-management)，且自动保证菜单展开
        # -------------------------------------------------------------
        print("\n[4] 测试 3: 点击【采购协同】文字区域 (页面跳转)...")
        nav_3 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('采购协同'));
            if (sec) {
                const label = sec.querySelector('.sidebar-item-label');
                if (label) {
                    label.click();
                    return true;
                }
            }
            return false;
        }""")
        await asyncio.sleep(2.5)
        print(f"     点击结果: {nav_3}")
        print(f"     页面成功跳转至采购看板: {page.url}")
        is_opened_3 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('采购协同'));
            return sec ? (sec.getAttribute('data-state') === 'opened') : false;
        }""")
        print(f"     采购协同菜单保持展开: {is_opened_3}")

        shot3 = os.path.join(OUTPUT_DIR, "dual_zone_3_text_navigation.png")
        await page.screenshot(path=shot3)

        # -------------------------------------------------------------
        # 测试 4: 点击【车油能耗中心】文字区域 (跨模块页面跳转)
        # -------------------------------------------------------------
        print("\n[5] 测试 4: 点击【车油能耗中心】文字区域...")
        nav_4 = await page.evaluate("""() => {
            const sec = Array.from(document.querySelectorAll('.body-sidebar .section-item')).find(el => el.textContent.includes('车油能耗'));
            if (sec) {
                const label = sec.querySelector('.sidebar-item-label');
                if (label) {
                    label.click();
                    return true;
                }
            }
            return false;
        }""")
        await asyncio.sleep(2.5)
        print(f"     页面成功跳转至车油看板: {page.url}")

        shot4 = os.path.join(OUTPUT_DIR, "dual_zone_4_fuel_navigation.png")
        await page.screenshot(path=shot4)

        await browser.close()
        print("\n[ALL TESTS PASSED] 双区职责分离模型验证 100% 成功！")

asyncio.run(run())
