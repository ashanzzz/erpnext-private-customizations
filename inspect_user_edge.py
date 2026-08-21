# -*- coding: utf-8 -*-
"""
直连用户正在操作的 Edge 浏览器 (CDP 9222 端口)
功能：
1. 抓取当前 Edge 标签页 URL 和标题
2. 抓取当前页面截图
3. 读取控制台报错 (Console Logs)
4. 读取当前 DOM 状态与侧边栏渲染
"""
import os
import sys
import asyncio
from playwright.async_api import async_playwright

CDP_URL = "http://127.0.0.1:9222"
OUTPUT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

async def inspect():
    async with async_playwright() as p:
        try:
            print(f"正在尝试连接 Edge 调试端口 {CDP_URL}...")
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            contexts = browser.contexts
            if not contexts:
                print("[错误] 未找到任何浏览器上下文，请确认 Edge 已打开。")
                return

            context = contexts[0]
            pages = context.pages
            print(f"[连接成功] 共找到 {len(pages)} 个已打开的 Edge 标签页：")

            target_page = None
            for idx, pg in enumerate(pages):
                title = await pg.title()
                url = pg.url
                print(f"  [{idx+1}] {title} -> {url}")
                if "192.168.8.11" in url or "my-business" in url or "desk" in url:
                    target_page = pg

            if not target_page and pages:
                target_page = pages[0]

            if target_page:
                print(f"\n正在分析当前操作页面: {target_page.url}")
                
                # 截图
                shot_path = os.path.join(OUTPUT_DIR, "user_live_edge_screenshot.png")
                await target_page.screenshot(path=shot_path)
                print(f"已抓取当前 Edge 实时屏幕画面：{shot_path}")

                # 获取控制台与 DOM 信息
                dom_info = await target_page.evaluate("""() => {
                    return {
                        title: document.title,
                        url: window.location.href,
                        has_sidebar: $('.body-sidebar').length > 0,
                        sidebar_items_count: $('.body-sidebar .standard-sidebar-item').length,
                        sidebar_items: Array.from(document.querySelectorAll('.body-sidebar .standard-sidebar-item')).map(e => e.textContent.trim().substring(0, 30)),
                        modals_count: $('.modal.show').length,
                        route: window.frappe ? frappe.get_route_str() : 'NO_FRAPPE'
                    };
                }""")

                print("\n页面实时状态数据:")
                print(f"  - 页面标题: {dom_info['title']}")
                print(f"  - 当前路由: {dom_info['route']}")
                print(f"  - 侧边栏项数: {dom_info['sidebar_items_count']}")
                print(f"  - 侧边栏前 10 项: {dom_info['sidebar_items'][:10]}")
                print(f"  - 弹窗数量: {dom_info['modals_count']}")

        except Exception as e:
            print(f"[连接失败] 无法连接到 Edge 调试端口: {e}")
            print("提示：请确认您已通过【启动Edge调试模式.bat】启动 Edge，且未被防火墙阻拦。")

if __name__ == '__main__':
    asyncio.run(inspect())
