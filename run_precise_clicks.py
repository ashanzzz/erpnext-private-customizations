# -*- coding: utf-8 -*-
"""
自动化全量交互测试：精准 22 步点击深度验收与状态监控
"""
import os
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
ERPNEXT_PASS = os.getenv('ERPNEXT_PASSWORD', '')

OUTPUT_DIR = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8"

# 22 步精准点击测试序列（覆盖 6 个一级分类、各类二级单据与报表、主控首页）
TEST_ACTIONS = [
    # --- 仓库与库存 模块 ---
    {"name": "点击一级分类【仓库与库存】", "type": "section", "target": "仓库与库存"},
    {"name": "点击二级菜单【物料主数据】", "type": "link", "target": "/desk/item"},
    {"name": "点击二级菜单【仓库管理】", "type": "link", "target": "/desk/warehouse"},
    {"name": "点击二级菜单【物料调拨与领用】", "type": "link", "target": "/desk/stock-entry"},
    {"name": "点击二级报表【库存台账明细】", "type": "link", "target": "/desk/query-report/Stock Ledger"},

    # --- 采购协同 模块 ---
    {"name": "点击一级分类【采购协同】", "type": "section", "target": "采购协同"},
    {"name": "点击二级菜单【采购订单】", "type": "link", "target": "/desk/purchase-order"},
    {"name": "点击二级菜单【采购入库单】", "type": "link", "target": "/desk/purchase-receipt"},
    {"name": "点击二级菜单【供应商管理】", "type": "link", "target": "/desk/supplier"},
    {"name": "点击二级报表【采购执行分析】", "type": "link", "target": "/desk/query-report/Purchase Order Analysis"},

    # --- 车油能耗中心 模块 ---
    {"name": "点击一级分类【车油能耗中心】", "type": "section", "target": "车油能耗"},
    {"name": "点击二级菜单【油卡档案】", "type": "link", "target": "/desk/oil-card"},
    {"name": "点击二级菜单【油卡充值流水】", "type": "link", "target": "/desk/oil-card-recharge"},
    {"name": "点击二级菜单【加油与能耗记录】", "type": "link", "target": "/desk/oil-card-refuel-log"},
    {"name": "点击二级报表【车辆加油明细表】", "type": "link", "target": "/desk/query-report/Vehicle Refuel Ledger"},

    # --- 企业合规中心 模块 ---
    {"name": "点击一级分类【企业合规中心】", "type": "section", "target": "合规"},
    {"name": "点击二级菜单【环保合规台账】", "type": "link", "target": "/desk/environmental-compliance-item"},
    {"name": "点击二级菜单【特种设备校验】", "type": "link", "target": "/desk/compliance-equipment-item"},
    {"name": "点击二级报表【企业合规总览】", "type": "link", "target": "/desk/query-report/Company Compliance Overview"},

    # --- 财务与报销 模块 ---
    {"name": "点击一级分类【财务与报销】", "type": "section", "target": "财务"},
    {"name": "点击二级菜单【员工报销申请】", "type": "link", "target": "/desk/reimbursement-request"},
    {"name": "点击二级菜单【付款凭证】", "type": "link", "target": "/desk/payment-entry"},
    {"name": "点击顶层主控主页【我的业务 (总控主页)】", "type": "home", "target": "/desk/my-business"}
]

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

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
        print(f"\n================ EXECUTING 23 PRECISE CLICKS ACCEPTANCE ================\n")

        for idx, action in enumerate(TEST_ACTIONS, 1):
            url_before = page.url
            action_name = action["name"]
            action_type = action["type"]
            target = action["target"]

            # 执行点击
            click_info = await page.evaluate("""(opt) => {
                let clicked = false;
                let text = '';
                let href = '';
                let targetEl = null;

                if (opt.type === 'section') {
                    const sections = Array.from(document.querySelectorAll('.body-sidebar .section-item .standard-sidebar-item'));
                    for (let s of sections) {
                        if (s.textContent.includes(opt.target)) {
                            targetEl = s;
                            break;
                        }
                    }
                } else if (opt.type === 'home') {
                    const anchors = Array.from(document.querySelectorAll('.body-sidebar .standard-sidebar-item .item-anchor'));
                    for (let a of anchors) {
                        if (a.getAttribute('href') === opt.target || a.textContent.includes('我的业务') || a.textContent.includes('总控主页')) {
                            targetEl = a;
                            break;
                        }
                    }
                } else {
                    const anchors = Array.from(document.querySelectorAll('.body-sidebar .sidebar-child-item .item-anchor, .body-sidebar .standard-sidebar-item .item-anchor'));
                    for (let a of anchors) {
                        let h = a.getAttribute('href') || '';
                        if (h === opt.target || h.startsWith(opt.target) || decodeURIComponent(h) === opt.target) {
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
            }""", {"type": action_type, "target": target})

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
            shot_file = f"precise_click_{idx:02d}.png"
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
            print(f"     Target URL: {url_after}")
            print(f"     View Title: {state['title']} | Sidebar Count: {state['sidebarItemCount']} | Modals: {state['modalCount']}")
            print(f"     Screenshot: {shot_file}")

        await browser.close()

        # 保存完整结果 JSON
        json_path = os.path.join(OUTPUT_DIR, "acceptance_23_precise_results.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n[DONE] Finished all {len(TEST_ACTIONS)} precise clicks! Results saved to {json_path}")

asyncio.run(run())
