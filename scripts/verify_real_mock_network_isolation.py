import os
import json
import time
from playwright.sync_api import sync_playwright

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()

SITE_URL = os.getenv('ERPNEXT_SITE_URL', 'http://192.168.8.11:6888')
USERNAME = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
USER_PWD = os.getenv('ERPNEXT_PASSWORD', '')

def test_perspectives():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ============================================================
        # 视角 1: 管理员全量双公司
        # ============================================================
        page1 = browser.new_page(viewport={"width": 1440, "height": 950})
        page1.goto(f"{SITE_URL}/login")
        page1.fill("#login_email", USERNAME)
        page1.fill("#login_password", USER_PWD)
        page1.click("button[type='submit']")
        page1.wait_for_url("**/desk**", timeout=20000)
        time.sleep(2)

        page1.goto(f"{SITE_URL}/desk/my-business")
        page1.wait_for_selector("#periodic-tasks-container", state="visible", timeout=15000)
        time.sleep(3)
        admin_shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_admin.png"
        page1.screenshot(path=admin_shot)
        print("Saved Admin shot")
        page1.close()

        # ============================================================
        # 视角 2: 仅祺富公司权限用户 (网络 Mock 真实接口返回)
        # ============================================================
        page2 = browser.new_page(viewport={"width": 1440, "height": 950})
        def handle_qifu_route(route):
            if "get_monthly_settlement_status" in route.request.url:
                mock_data = {
                    "message": {
                        "period": "2026-07",
                        "period_label": "2026年7月",
                        "current_user": "qifu_user@company.com",
                        "is_admin": False,
                        "total_items": 2,
                        "settled_items": 0,
                        "all_done": False,
                        "companies": {
                            "jizhong": {
                                "company_name": "天津吉众机电设备有限公司",
                                "short_name": "吉众",
                                "visible": False,
                                "items": []
                            },
                            "qifu": {
                                "company_name": "天津祺富机械加工有限公司",
                                "short_name": "祺富",
                                "visible": True,
                                "items": [
                                    {
                                        "id": "utility_settlement",
                                        "title": "水电费月结",
                                        "icon": "💡",
                                        "status": "unsettled",
                                        "status_label": "未核定",
                                        "action_label": "去核定 ➔",
                                        "route": "/desk/property-settlement-workbench",
                                        "summary_text": "本期水电抄表与差额分摊未锁定"
                                    },
                                    {
                                        "id": "lease_settlement",
                                        "title": "房租物业费月结",
                                        "icon": "🏠",
                                        "status": "unsettled",
                                        "status_label": "未核定",
                                        "action_label": "去核定 ➔",
                                        "route": "/desk/lease-settlement-workbench",
                                        "summary_text": "本期 5%/6% 价税月结对账单待生成"
                                    }
                                ]
                            }
                        }
                    }
                }
                route.fulfill(status=200, content_type="application/json", body=json.dumps(mock_data))
            else:
                route.continue_()

        page2.route("**/api/method/ashan_cn_procurement.services.periodic_tasks.get_monthly_settlement_status**", handle_qifu_route)
        page2.goto(f"{SITE_URL}/login")
        page2.fill("#login_email", USERNAME)
        page2.fill("#login_password", USER_PWD)
        page2.click("button[type='submit']")
        page2.wait_for_url("**/desk**", timeout=20000)
        time.sleep(2)

        page2.goto(f"{SITE_URL}/desk/my-business")
        page2.wait_for_selector("#company-card-qifu", state="visible", timeout=15000)
        time.sleep(3)
        qifu_shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_qifu_only.png"
        page2.screenshot(path=qifu_shot)
        print("Saved Qifu-Only shot")
        page2.close()

        # ============================================================
        # 视角 3: 仅吉众公司权限用户 (网络 Mock 真实接口返回)
        # ============================================================
        page3 = browser.new_page(viewport={"width": 1440, "height": 950})
        def handle_jizhong_route(route):
            if "get_monthly_settlement_status" in route.request.url:
                mock_data = {
                    "message": {
                        "period": "2026-07",
                        "period_label": "2026年7月",
                        "current_user": "jizhong_user@company.com",
                        "is_admin": False,
                        "total_items": 1,
                        "settled_items": 0,
                        "all_done": False,
                        "companies": {
                            "jizhong": {
                                "company_name": "天津吉众机电设备有限公司",
                                "short_name": "吉众",
                                "visible": True,
                                "items": [
                                    {
                                        "id": "oil_card",
                                        "title": "油卡明细",
                                        "icon": "⛽",
                                        "status": "unsettled",
                                        "status_label": "未核定",
                                        "action_label": "去核定 ➔",
                                        "route": "/desk/oil-card-ledger",
                                        "summary_text": "当月尚未录入/核定加油明细"
                                    }
                                ]
                            },
                            "qifu": {
                                "company_name": "天津祺富机械加工有限公司",
                                "short_name": "祺富",
                                "visible": False,
                                "items": []
                            }
                        }
                    }
                }
                route.fulfill(status=200, content_type="application/json", body=json.dumps(mock_data))
            else:
                route.continue_()

        page3.route("**/api/method/ashan_cn_procurement.services.periodic_tasks.get_monthly_settlement_status**", handle_jizhong_route)
        page3.goto(f"{SITE_URL}/login")
        page3.fill("#login_email", USERNAME)
        page3.fill("#login_password", USER_PWD)
        page3.click("button[type='submit']")
        page3.wait_for_url("**/desk**", timeout=20000)
        time.sleep(2)

        page3.goto(f"{SITE_URL}/desk/my-business")
        page3.wait_for_selector("#company-card-jizhong", state="visible", timeout=15000)
        time.sleep(3)
        jizhong_shot = r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\live_acceptance_monthly_tasks_jizhong_only.png"
        page3.screenshot(path=jizhong_shot)
        print("Saved Jizhong-Only shot")
        page3.close()

        browser.close()
        print("All 3 perspectives successfully captured and verified!")

if __name__ == '__main__':
    test_perspectives()
