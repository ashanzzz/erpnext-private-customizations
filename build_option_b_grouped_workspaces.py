import os
import json
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
SITE_URL = os.getenv('ERPNEXT_SITE_URL_LOCAL', 'http://192.168.8.11:6888')
USER = os.getenv('ERPNEXT_USERNAME', 'ashanzzz1213@gmail.com')
PWD = os.getenv('ERPNEXT_PASSWORD', 'Woo@@@204317')

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_req = urllib.request.Request(
    f"{SITE_URL}/api/method/login",
    data=json.dumps({'usr': USER, 'pwd': PWD}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
opener.open(login_req)

def call_api(endpoint, method='GET', data=None):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with opener.open(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"Error {e.code} on {method} {endpoint}: {err_body}")
        return None

def save_workspace(name, title, parent_page="", seq=1.0, icon="home", shortcuts=None, sections=None):
    content_blocks = [
        {"id": f"hdr_main_{name.lower().replace(' ', '_')}", "type": "header", "data": {"text": f"<span class=\"h3\"><b>{title}</b></span>", "col": 12}}
    ]

    formatted_shortcuts = []
    if shortcuts:
        content_blocks.append({
            "id": f"hdr_sc_{name.lower().replace(' ', '_')}",
            "type": "header",
            "data": {"text": "<span class=\"text-muted small\"><b>快捷业务入口</b></span>", "col": 12}
        })
        for i, sc in enumerate(shortcuts):
            sc_id = f"sc_{i}_{sc['link_to'].lower().replace(' ', '_')}"
            content_blocks.append({
                "id": sc_id,
                "type": "shortcut",
                "data": {"shortcut_name": sc['name'], "col": sc.get('col', 3)}
            })
            sc_dict = {
                "type": sc['type'],
                "label": sc['name'],
                "link_to": sc['link_to']
            }
            if sc['type'] == 'DocType':
                sc_dict['doc_view'] = sc.get('doc_view', 'List')
            elif sc['type'] == 'Report':
                sc_dict['is_query_report'] = sc.get('is_query_report', 1)
            formatted_shortcuts.append(sc_dict)

    formatted_links = []
    if sections:
        for s_idx, sec in enumerate(sections):
            content_blocks.append({
                "id": f"card_block_{s_idx}_{sec['title'].lower().replace(' ', '_')}",
                "type": "card",
                "data": {"card_name": sec['title'], "col": sec.get('col', 6)}
            })
            formatted_links.append({
                "label": sec['title'],
                "type": "Card Break",
                "link_type": "DocType",
                "link_to": ""
            })
            for item in sec['items']:
                formatted_links.append({
                    "label": item['name'],
                    "type": "Link",
                    "link_type": item['type'],
                    "link_to": item['link_to'],
                    "is_query_report": item.get('is_query_report', 0)
                })

    payload = {
        "doctype": "Workspace",
        "name": name,
        "label": name,
        "title": title,
        "public": 1,
        "module": "Ashan CN Procurement",
        "parent_page": parent_page,
        "sequence_id": seq,
        "icon": icon,
        "hide_custom": 1,
        "is_hidden": 0,
        "type": "Workspace",
        "content": json.dumps(content_blocks, ensure_ascii=False),
        "shortcuts": formatted_shortcuts,
        "links": formatted_links
    }

    enc = urllib.parse.quote(name)
    existing = call_api(f'/api/resource/Workspace/{enc}')
    if existing and 'data' in existing:
        res = call_api(f'/api/resource/Workspace/{enc}', method='PUT', data=payload)
    else:
        res = call_api('/api/resource/Workspace', method='POST', data=payload)
    print(f"Saved Workspace '{name}' (Title: '{title}', Parent: '{parent_page}', hide_custom: 1):", res is not None)

def export_all():
    workspaces = [
        ("My Business", "my_business"),
        ("Procurement Management", "procurement_management"),
        ("Stock and Inventory", "stock_and_inventory"),
        ("Accounting and Finance", "accounting_and_finance"),
        ("Vehicle Fuel Hub", "vehicle_fuel_hub"),
        ("Company Compliance Center", "company_compliance_center")
    ]
    for ws_name, dir_name in workspaces:
        enc_name = urllib.parse.quote(ws_name)
        data = call_api(f'/api/resource/Workspace/{enc_name}')
        if not data or 'data' not in data:
            continue
        ws_doc = data['data']
        for k in ['modified', 'creation', 'owner', 'modified_by', 'docstatus', 'idx', '__last_sync_on']:
            ws_doc.pop(k, None)
        for table in ['shortcuts', 'links', 'number_cards', 'charts', 'quick_lists', 'custom_blocks', 'roles']:
            if table in ws_doc and isinstance(ws_doc[table], list):
                for row in ws_doc[table]:
                    if isinstance(row, dict):
                        for rk in ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'parent', 'parentfield', 'parenttype', 'idx']:
                            row.pop(rk, None)
        target_dir = os.path.join(r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\workspace", dir_name)
        os.makedirs(target_dir, exist_ok=True)
        json_path = os.path.join(target_dir, f"{dir_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ws_doc, f, indent=1, ensure_ascii=False)
        print(f"Exported clean JSON to {json_path}")

def main():
    print("=== CONFIGURING OPTION B (GROUPED COLLAPSIBLE WORKSPACES WITH HIDE_CUSTOM=1) ===")
    
    # 1. Root Workspace: My Business (总控主页)
    save_workspace(
        name="My Business",
        title="我的业务 (总控主页)",
        parent_page="",
        seq=1.0,
        icon="home",
        shortcuts=[
            {"type": "DocType", "link_to": "Item", "name": "物料主数据", "col": 3},
            {"type": "DocType", "link_to": "Warehouse", "name": "仓库管理", "col": 3},
            {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单", "col": 3},
            {"type": "DocType", "link_to": "Oil Card", "name": "油卡档案", "col": 3},
            {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "加油与能耗记录", "col": 3},
            {"type": "DocType", "link_to": "Reimbursement Request", "name": "员工报销申请", "col": 3},
            {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "企业合规台账", "col": 3},
            {"type": "DocType", "link_to": "Stock Entry", "name": "物料调拨与领用", "col": 3}
        ],
        sections=[
            {
                "title": "常用业务快速通道",
                "items": [
                    {"type": "DocType", "link_to": "Item", "name": "物料主数据"},
                    {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单"},
                    {"type": "DocType", "link_to": "Oil Card", "name": "油卡档案"},
                    {"type": "DocType", "link_to": "Reimbursement Request", "name": "报销申请"}
                ]
            },
            {
                "title": "常用经营报表",
                "items": [
                    {"type": "Report", "link_to": "Stock Ledger", "name": "库存台账明细", "is_query_report": 1},
                    {"type": "Report", "link_to": "Vehicle Fuel Cost Summary", "name": "车油能耗月度汇总", "is_query_report": 1},
                    {"type": "Report", "link_to": "Company Compliance Overview", "name": "企业合规总览", "is_query_report": 1}
                ]
            }
        ]
    )

    # 2. 仓储与库存 (Stock and Inventory)
    save_workspace(
        name="Stock and Inventory",
        title="仓库与库存",
        parent_page="My Business",
        seq=1.1,
        icon="package",
        shortcuts=[
            {"type": "DocType", "link_to": "Item", "name": "物料主数据", "col": 3},
            {"type": "DocType", "link_to": "Warehouse", "name": "仓库管理", "col": 3},
            {"type": "DocType", "link_to": "Stock Entry", "name": "物料调拨与领用", "col": 3},
            {"type": "DocType", "link_to": "Delivery Note", "name": "销售出库单", "col": 3}
        ],
        sections=[
            {
                "title": "仓储核心单据",
                "items": [
                    {"type": "DocType", "link_to": "Item", "name": "物料主数据 (Item)"},
                    {"type": "DocType", "link_to": "Warehouse", "name": "仓库档案 (Warehouse)"},
                    {"type": "DocType", "link_to": "Stock Entry", "name": "物料调拨/领用 (Stock Entry)"},
                    {"type": "DocType", "link_to": "Delivery Note", "name": "销售出库单 (Delivery Note)"}
                ]
            },
            {
                "title": "仓储报表分析",
                "items": [
                    {"type": "Report", "link_to": "Stock Ledger", "name": "库存台账明细报表", "is_query_report": 1},
                    {"type": "Report", "link_to": "Stock Balance", "name": "库存余额报表", "is_query_report": 1}
                ]
            }
        ]
    )

    # 3. 采购管理 (Procurement Management)
    save_workspace(
        name="Procurement Management",
        title="采购管理",
        parent_page="My Business",
        seq=1.2,
        icon="shopping-cart",
        shortcuts=[
            {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单", "col": 3},
            {"type": "DocType", "link_to": "Purchase Receipt", "name": "采购入库单", "col": 3},
            {"type": "DocType", "link_to": "Supplier", "name": "供应商档案", "col": 3},
            {"type": "DocType", "link_to": "Material Request", "name": "采购申请单", "col": 3}
        ],
        sections=[
            {
                "title": "采购业务单据",
                "items": [
                    {"type": "DocType", "link_to": "Material Request", "name": "物料采购申请 (Material Request)"},
                    {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单 (Purchase Order)"},
                    {"type": "DocType", "link_to": "Purchase Receipt", "name": "采购入库单 (Purchase Receipt)"},
                    {"type": "DocType", "link_to": "Supplier", "name": "供应商管理 (Supplier)"}
                ]
            },
            {
                "title": "采购报表",
                "items": [
                    {"type": "Report", "link_to": "Purchase Order Analysis", "name": "采购订单执行分析", "is_query_report": 1}
                ]
            }
        ]
    )

    # 4. 车油能耗管理 (Vehicle Fuel Hub)
    save_workspace(
        name="Vehicle Fuel Hub",
        title="车油能耗管理",
        parent_page="My Business",
        seq=1.3,
        icon="truck",
        shortcuts=[
            {"type": "DocType", "link_to": "Oil Card", "name": "油卡档案", "col": 3},
            {"type": "DocType", "link_to": "Oil Card Recharge", "name": "油卡充值流水", "col": 3},
            {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "加油明细与能耗", "col": 3},
            {"type": "DocType", "link_to": "Oil Card Invoice Batch", "name": "油票批量录入", "col": 3}
        ],
        sections=[
            {
                "title": "车油台账与流水",
                "items": [
                    {"type": "DocType", "link_to": "Oil Card", "name": "油卡档案"},
                    {"type": "DocType", "link_to": "Oil Card Recharge", "name": "油卡充值流水"},
                    {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "加油明细与能耗记录"},
                    {"type": "DocType", "link_to": "Oil Card Invoice Batch", "name": "油票发票批量录入"}
                ]
            },
            {
                "title": "车油能耗统计报表",
                "items": [
                    {"type": "Report", "link_to": "Vehicle Refuel Ledger", "name": "车辆加油流水明细表", "is_query_report": 1},
                    {"type": "Report", "link_to": "Oil Card Recharge Ledger", "name": "油卡充值台账", "is_query_report": 1},
                    {"type": "Report", "link_to": "Vehicle Fuel Cost Summary", "name": "车油能耗月度汇总", "is_query_report": 1},
                    {"type": "Report", "link_to": "Oil Card Card Summary", "name": "油卡卡片汇总表", "is_query_report": 1},
                    {"type": "Report", "link_to": "Oil Card Monthly Ledger", "name": "油卡月度台账", "is_query_report": 1},
                    {"type": "Report", "link_to": "Oil Card Operating Summary", "name": "油卡运营总览", "is_query_report": 1},
                    {"type": "Report", "link_to": "Oil Supplier Invoice Summary", "name": "油品供应商发票汇总", "is_query_report": 1}
                ]
            }
        ]
    )

    # 5. 企业合规中心 (Company Compliance Center)
    save_workspace(
        name="Company Compliance Center",
        title="企业合规中心",
        parent_page="My Business",
        seq=1.4,
        icon="shield",
        shortcuts=[
            {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "环保合规台账", "col": 4},
            {"type": "DocType", "link_to": "Compliance Equipment Item", "name": "特种设备校验", "col": 4},
            {"type": "DocType", "link_to": "Employee Certificate Item", "name": "员工证书资质", "col": 4}
        ],
        sections=[
            {
                "title": "合规业务台账",
                "items": [
                    {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "环保合规项档案"},
                    {"type": "DocType", "link_to": "Compliance Equipment Item", "name": "特种设备台账与校验"},
                    {"type": "DocType", "link_to": "Employee Certificate Item", "name": "员工证书与特种资质"}
                ]
            },
            {
                "title": "合规监控与趋势报表",
                "items": [
                    {"type": "Report", "link_to": "Company Compliance Overview", "name": "企业合规总览报表", "is_query_report": 1},
                    {"type": "Report", "link_to": "Company Compliance Pending Purchase", "name": "合规待采办清单", "is_query_report": 1},
                    {"type": "Report", "link_to": "Compliance Expiry Trend", "name": "合规资质到期趋势预警", "is_query_report": 1}
                ]
            }
        ]
    )

    # 6. 会计与财务 (Accounting and Finance)
    save_workspace(
        name="Accounting and Finance",
        title="会计与财务",
        parent_page="My Business",
        seq=1.5,
        icon="credit-card",
        shortcuts=[
            {"type": "DocType", "link_to": "Purchase Invoice", "name": "应付发票", "col": 3},
            {"type": "DocType", "link_to": "Sales Invoice", "name": "应收发票", "col": 3},
            {"type": "DocType", "link_to": "Payment Entry", "name": "付款凭证", "col": 3},
            {"type": "DocType", "link_to": "Reimbursement Request", "name": "员工报销申请", "col": 3}
        ],
        sections=[
            {
                "title": "财务与报销单据",
                "items": [
                    {"type": "DocType", "link_to": "Reimbursement Request", "name": "员工报销申请单"},
                    {"type": "DocType", "link_to": "Purchase Invoice", "name": "采购应付发票"},
                    {"type": "DocType", "link_to": "Sales Invoice", "name": "销售应收发票"},
                    {"type": "DocType", "link_to": "Payment Entry", "name": "付款与核销凭证"}
                ]
            },
            {
                "title": "报销与财务报表",
                "items": [
                    {"type": "Report", "link_to": "Unpaid Reimbursement List", "name": "待支付报销明细表", "is_query_report": 1},
                    {"type": "Report", "link_to": "Reimbursement Payment Status", "name": "报销支付状态统计", "is_query_report": 1}
                ]
            }
        ]
    )

    print("\n=== EXPORTING CLEAN WORKSPACES ===")
    export_all()

if __name__ == '__main__':
    main()
