# -*- coding: utf-8 -*-
"""
浏览器验收脚本 - 使用 Playwright + Chromium 本地验收
验收目标：侧边栏折叠状态修复（section 互不影响）
"""
import os
import sys
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

SITE_URL = "http://192.168.8.11:6888"  # 直接用已验证的 6888
ERPNEXT_USER = os.getenv('ERPNEXT_USER', 'Administrator')
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', '')

OUTPUT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # ---- 1. 登录 ----
        print("[1] 登录...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)

        # ---- 2. 进入 my-business workspace ----
        print("[2] 导航到 my-business...")
        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # 清除旧 localStorage 状态，模拟全新用户
        await page.evaluate("""() => {
            localStorage.removeItem('ashan-cn-sidebar-state');
            localStorage.removeItem('section-breaks-state');
        }""")
        await page.reload(wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # ---- 3. 截图：初始状态 ----
        shot1 = os.path.join(OUTPUT_DIR, "acceptance_1_fresh.png")
        await page.screenshot(path=shot1)
        print(f"[3] 截图 1 保存：{shot1}")

        # 列出所有 section 标题
        sections = await page.eval_on_selector_all(
            ".body-sidebar .section-item .standard-sidebar-item",
            "els => els.map(e => e.textContent.trim().substring(0, 40))"
        )
        print(f"[3] 发现 {len(sections)} 个一级菜单：{sections}")

        # ---- 4. 点击"财务与报销" ----
        print("[4] 点击 财务与报销...")
        clicked_caiwu = await page.evaluate("""() => {
            const items = document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item');
            for (const item of items) {
                const t = item.textContent.trim();
                if (t.includes('财务') || t.includes('报销')) {
                    item.click();
                    return t;
                }
            }
            return null;
        }""")
        print(f"[4] 点击了：{clicked_caiwu}")
        await asyncio.sleep(1.5)

        shot2 = os.path.join(OUTPUT_DIR, "acceptance_2_after_caiwu.png")
        await page.screenshot(path=shot2)
        print(f"[4] 截图 2 保存：{shot2}")

        # 检查 section 状态
        states_after_caiwu = await page.evaluate("""() => {
            const children = document.querySelectorAll('.body-sidebar .sidebar-item-children');
            let opened = [], closed = [];
            children.forEach((c, i) => {
                const state = c.getAttribute('data-state');
                const title = c.closest('.sidebar-item-container')?.getAttribute('item-name') || 
                              c.closest('.sidebar-item-container')?.getAttribute('title') || i;
                if (state === 'opened') opened.push(title);
                else if (state === 'closed') closed.push(title);
            });
            return {opened, closed, total: children.length};
        }""")
        print(f"[4] 点击财务后 - 展开: {states_after_caiwu['opened']}, 收起: {states_after_caiwu['closed']}")

        # 读取我们自己的 localStorage
        ashan_state = await page.evaluate("() => localStorage.getItem('ashan-cn-sidebar-state')")
        native_state = await page.evaluate("() => localStorage.getItem('section-breaks-state')")
        print(f"[4] ashan-cn-sidebar-state: {ashan_state}")
        print(f"[4] section-breaks-state (原生): {native_state}")

        # ---- 5. 点击"仓库与库存" ----
        print("[5] 点击 仓库与库存...")
        await page.evaluate("""() => {
            const items = document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item');
            for (const item of items) {
                const t = item.textContent.trim();
                if (t.includes('库存') || t.includes('仓库')) { item.click(); return; }
            }
        }""")
        await asyncio.sleep(1.5)

        shot3 = os.path.join(OUTPUT_DIR, "acceptance_3_after_kucun.png")
        await page.screenshot(path=shot3)
        print(f"[5] 截图 3 保存：{shot3}")

        states_after_kucun = await page.evaluate("""() => {
            const children = document.querySelectorAll('.body-sidebar .sidebar-item-children');
            let opened = [], closed = [];
            children.forEach((c, i) => {
                const state = c.getAttribute('data-state');
                const title = c.closest('.sidebar-item-container')?.getAttribute('item-name') || 
                              c.closest('.sidebar-item-container')?.getAttribute('title') || i;
                if (state === 'opened') opened.push(title);
                else if (state === 'closed') closed.push(title);
            });
            return {opened, closed};
        }""")
        print(f"[5] 点击库存后 - 展开: {states_after_kucun['opened']}, 收起: {states_after_kucun['closed']}")

        ashan_state2 = await page.evaluate("() => localStorage.getItem('ashan-cn-sidebar-state')")
        print(f"[5] ashan-cn-sidebar-state: {ashan_state2}")

        # ---- 6. 再点击"采购协同" ----
        print("[6] 点击 采购协同...")
        await page.evaluate("""() => {
            const items = document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item');
            for (const item of items) {
                const t = item.textContent.trim();
                if (t.includes('采购')) { item.click(); return; }
            }
        }""")
        await asyncio.sleep(1.5)

        shot4 = os.path.join(OUTPUT_DIR, "acceptance_4_after_caigou.png")
        await page.screenshot(path=shot4)
        print(f"[6] 截图 4 保存：{shot4}")

        states_final = await page.evaluate("""() => {
            const children = document.querySelectorAll('.body-sidebar .sidebar-item-children');
            let info = [];
            children.forEach((c, i) => {
                const state = c.getAttribute('data-state');
                const title = c.closest('.sidebar-item-container')?.getAttribute('item-name') || 
                              c.closest('.sidebar-item-container')?.getAttribute('title') || String(i);
                info.push({title, state});
            });
            return info;
        }""")
        print("[6] 最终各 section 状态:")
        for s in states_final:
            icon = "⬇ 展开" if s['state'] == 'opened' else "⬆ 收起"
            print(f"    [{s['state']}] {s['title'][:25]}")

        # 判断是否存在状态泄漏
        final_ashan = await page.evaluate("() => localStorage.getItem('ashan-cn-sidebar-state')")
        print(f"\n[最终] ashan-cn-sidebar-state: {final_ashan}")

        await browser.close()
        print("\n[DONE] 浏览器验收完成！")

asyncio.run(run())
