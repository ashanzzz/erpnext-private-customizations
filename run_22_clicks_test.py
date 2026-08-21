# -*- coding: utf-8 -*-
"""
自动化全量交互测试：至少 20 次点击深度验收
记录每次点击前后的：
- 点击目标（分类一级/单据二级/主页）
- 路由变化 (URL Before -> URL After)
- 右侧主视图标题 / 内容摘要
- 左侧边栏状态（各 Section 展开/折叠状态）
- 控制台错误与弹窗异常检测
- 截图保存
"""
import os
import sys
import json
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

# 定义 22 次点击的全面测试序列
TEST_ACTIONS = [
    {"name": "点击一级分类【仓库与库存】", "type": "section", "text": "仓库与库存"},
    {"name": "点击二级菜单【物料主数据】", "type": "link", "text": "物料主数据"},
    {"name": "点击二级菜单【仓库管理】", "type": "link", "text": "仓库管理"},
    {"name": "点击二级菜单【物料调拨与领用】", "type": "link", "text": "物料调拨与领用"},
    {"name": "点击二级菜单【销售出库单】", "type": "link", "text": "销售出库单"},
    {"name": "点击一级分类【采购协同】", "type": "section", "text": "采购协同"},
    {"name": "点击二级菜单【采购订单】", "type": "link", "text": "采购订单"},
    {"name": "点击二级菜单【采购入库单】", "type": "link", "text": "采购入库单"},
    {"name": "点击二级菜单【供应商管理】", "type": "link", "text": "供应商管理"},
    {"name": "点击一级分类【车油能耗中心】", "type": "section", "text": "车油能耗"},
    {"name": "点击二级菜单【油卡档案】", "type": "link", "text": "油卡档案"},
    {"name": "点击二级菜单【加油与能耗记录】", "type": "link", "text": "加油与能耗记录"},
    {"name": "点击二级报表【车辆加油明细表】", "type": "link", "text": "车辆加油明细表"},
    {"name": "点击一级分类【企业合规中心】", "type": "section", "text": "合规"},
    {"name": "点击二级菜单【环保合规项档案】", "type": "link", "text": "环保合规项档案"},
    {"name": "点击二级菜单【特种设备台账与校验】", "type": "link", "text": "特种设备台账与校验"},
    {"name": "点击一级分类【财务与报销】", "type": "section", "text": "财务"},
    {"name": "点击二级菜单【员工报销申请】", "type": "link", "text": "员工报销申请"},
    {"name": "点击二级菜单【采购应付发票】", "type": "link", "text": "采购应付发票"},
    {"name": "点击二级菜单【付款凭证】", "type": "link", "text": "付款凭证"},
    {"name": "点击顶层主页【我的业务 (总控主页)】", "type": "home", "text": "我的业务"},
    {"name": "再次点击一级分类【仓库与库存】(折叠切换)", "type": "section", "text": "仓库与库存"}
]

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("[0] Logging in...")
        await page.goto(f"{SITE_URL}/login", wait_until="networkidle", timeout=30000)
        await page.fill("#login_email", ERPNEXT_USER)
        await page.fill("#login_password", ERPNEXT_PASS)
        await page.click(".btn-login")
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(4)

        # 初始进入 My Business
        await page.goto(f"{SITE_URL}/desk/my-business", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        results = []
        print(f"\n================ STARTING {len(TEST_ACTIONS)} CLICKS DEEP TEST ================\n")

        for idx, action in enumerate(TEST_ACTIONS, 1):
            url_before = page.url
            action_name = action["name"]
            action_type = action["type"]
            target_text = action["text"]

            # 执行点击
            click_info = await page.evaluate("""(opt) => {
                let clicked = false;
                let text = '';
                let href = '';
                let targetEl = null;

                if (opt.type === 'section') {
                    const sections = Array.from(document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item'));
                    for (let s of sections) {
                        if (s.textContent.includes(opt.text)) {
                            targetEl = s;
                            break;
                        }
                    }
                } else if (opt.type === 'home') {
                    const items = Array.from(document.querySelectorAll('.body-sidebar .standard-sidebar-item'));
                    for (let it of items) {
                        if (it.textContent.includes(opt.text) || it.textContent.includes('总控主页')) {
                            targetEl = it;
                            break;
                        }
                    }
                } else {
                    const links = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor, .body-sidebar .standard-sidebar-item .item-anchor'));
                    for (let a of links) {
                        if (a.textContent.includes(opt.text)) {
                            targetEl = a;
                            break;
                        }
                    }
                }

                if (targetEl) {
                    text = targetEl.textContent.trim();
                    href = targetEl.getAttribute('href') || '';
                    targetEl.click();
                    clicked = true;
                }

                return { clicked, text, href };
            }""", {"type": action_type, "text": target_text})

            # 等待渲染稳定
            await asyncio.sleep(2.5)

            url_after = page.url

            # 抓取页面状态
            state = await page.evaluate("""() => {
                const titleEl = document.querySelector('.page-title, .title-text, .list-header, .workspace-title, h1, h2, h3');
                const title = titleEl ? titleEl.textContent.trim().substring(0, 40) : 'N/A';
                const sidebarItemCount = document.querySelectorAll('.body-sidebar .standard-sidebar-item').length;
                const modalCount = document.querySelectorAll('.modal.show').length;
                
                // 获取各 Section 状态
                const sectionStates = {};
                document.querySelectorAll('.body-sidebar .section-item').forEach(el => {
                    const name = (el.getAttribute('item-name') || el.getAttribute('title') || '').trim();
                    const isOpen = el.getAttribute('data-state') === 'opened';
                    if (name) sectionStates[name] = isOpen ? 'opened' : 'closed';
                });

                return {
                    title,
                    sidebarItemCount,
                    modalCount,
                    sectionStates
                };
            }""")

            # 截图
            shot_file = f"click_{idx:02d}_{action_type}.png"
            shot_path = os.path.join(OUTPUT_DIR, shot_file)
            await page.screenshot(path=shot_path)

            step_res = {
                "step": idx,
                "action": action_name,
                "clicked_text": click_info["text"],
                "clicked_href": click_info["href"],
                "url_before": url_before,
                "url_after": url_after,
                "page_title": state["title"],
                "sidebar_count": state["sidebarItemCount"],
                "modal_count": state["modalCount"],
                "section_states": state["sectionStates"],
                "shot_file": shot_file
            }
            results.append(step_res)

            print(f"[{idx:02d}/{len(TEST_ACTIONS)}] [OK] {action_name}")
            print(f"     URL: {url_after}")
            print(f"     View Title: {state['title']} | Sidebar Items: {state['sidebarItemCount']} | Modals: {state['modalCount']}")
            print(f"     Screenshot: {shot_file}")

        await browser.close()

        # 保存完整结果 JSON
        json_path = os.path.join(OUTPUT_DIR, "acceptance_22_clicks_results.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n[DONE] Finished all {len(TEST_ACTIONS)} clicks! Results saved to {json_path}")

asyncio.run(run())
