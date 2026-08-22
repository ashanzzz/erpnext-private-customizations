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
USER = os.getenv('ERPNEXT_USERNAME', 'dev@example.invalid')
PWD = os.getenv('ERPNEXT_PASSWORD', '')

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

def build_workspace(name, title, parent_page="", sequence_id=1.0, sections=None, shortcuts=None):
    content_blocks = []
    
    # Title Header
    content_blocks.append({
        "id": f"hdr_main_{name.lower().replace(' ', '_')}",
        "type": "header",
        "data": {"text": f"<span class=\"h3\"><b>{title}</b></span>", "col": 12}
    })

    formatted_shortcuts = []
    if shortcuts:
        content_blocks.append({
            "id": f"hdr_sc_{name.lower().replace(' ', '_')}",
            "type": "header",
            "data": {"text": "<span class=\"text-muted small\"><b>快捷业务直达</b></span>", "col": 12}
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
                "label": sc['name']
            }
            if sc['type'] == 'URL':
                sc_dict['url'] = sc['link_to']
            elif sc['type'] == 'Report':
                sc_dict['link_to'] = sc['link_to']
                sc_dict['is_query_report'] = sc.get('is_query_report', 1)
            else:
                sc_dict['link_to'] = sc['link_to']
                sc_dict['doc_view'] = sc.get('doc_view', 'List')
            formatted_shortcuts.append(sc_dict)

    formatted_links = []
    if sections:
        for s_idx, sec in enumerate(sections):
            content_blocks.append({
                "id": f"card_block_{s_idx}_{sec['title'].lower().replace(' ', '_')}",
                "type": "card",
                "data": {"card_name": sec['title'], "col": 4}
            })
            # Section Header link
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
        "is_hidden": 0,
        "type": "Workspace",
        "sequence_id": sequence_id,
        "content": json.dumps(content_blocks, ensure_ascii=False),
        "shortcuts": formatted_shortcuts,
        "links": formatted_links
    }

    enc_name = urllib.parse.quote(name)
    existing = call_api(f'/api/resource/Workspace/{enc_name}')
    if existing and 'data' in existing:
        print(f"Updating Workspace: {name} (Title: {title}, Parent: '{parent_page}')")
        res = call_api(f'/api/resource/Workspace/{enc_name}', method='PUT', data=payload)
    else:
        print(f"Creating Workspace: {name} (Title: {title}, Parent: '{parent_page}')")
        res = call_api('/api/resource/Workspace', method='POST', data=payload)
        
    return res

def export_workspace_json(workspace_name, dir_name):
    enc_name = urllib.parse.quote(workspace_name)
    data = call_api(f'/api/resource/Workspace/{enc_name}')
    if not data or 'data' not in data:
        print(f"Failed to fetch workspace {workspace_name} for export!")
        return
        
    ws_doc = data['data']
    for k in ['modified', 'creation', 'owner', 'modified_by', 'docstatus', 'idx', '__last_sync_on']:
        ws_doc.pop(k, None)
        
    target_dir = os.path.join(r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\workspace", dir_name)
    os.makedirs(target_dir, exist_ok=True)
    json_path = os.path.join(target_dir, f"{dir_name}.json")
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ws_doc, f, indent=1, ensure_ascii=False)
    print(f"Exported JSON to {json_path}")

def main():
    print("=== BUILDING ALL-IN-ONE SUPER WORKSPACE (OPTION 1) ===")
    
    # 1. Super All-in-One Root Workspace: My Business
    build_workspace(
        name="My Business",
        title="我的业务",
        parent_page="",
        sequence_id=1.0,
        shortcuts=[
            # Row 1: Stock & Warehouse
            {"type": "DocType", "link_to": "Item", "name": "物料主数据", "col": 3},
            {"type": "DocType", "link_to": "Warehouse", "name": "仓库管理", "col": 3},
            {"type": "DocType", "link_to": "Stock Entry", "name": "物料调拨与领用", "col": 3},
            {"type": "DocType", "link_to": "Delivery Note", "name": "销售出库单", "col": 3},
            
            # Row 2: Procurement & Supplier
            {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单", "col": 3},
            {"type": "DocType", "link_to": "Purchase Receipt", "name": "采购入库单", "col": 3},
            {"type": "DocType", "link_to": "Supplier", "name": "供应商管理", "col": 3},
            {"type": "DocType", "link_to": "Material Request", "name": "采购申请单", "col": 3},
            
            # Row 3: Vehicles, Fuel & Compliance
            {"type": "DocType", "link_to": "Oil Card", "name": "油卡档案", "col": 3},
            {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "加油与能耗记录", "col": 3},
            {"type": "DocType", "link_to": "Reimbursement Request", "name": "员工报销申请", "col": 3},
            {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "企业合规台账", "col": 3}
        ],
        sections=[
            {
                "title": "仓储与库存中心",
                "items": [
                    {"type": "DocType", "link_to": "Item", "name": "物料主数据"},
                    {"type": "DocType", "link_to": "Warehouse", "name": "仓库档案"},
                    {"type": "DocType", "link_to": "Stock Entry", "name": "物料领料/调拨/退料"},
                    {"type": "DocType", "link_to": "Delivery Note", "name": "出库单据"},
                    {"type": "Report", "link_to": "Stock Ledger", "name": "库存台账报表", "is_query_report": 1}
                ]
            },
            {
                "title": "采购与供应链业务",
                "items": [
                    {"type": "DocType", "link_to": "Material Request", "name": "采购申请"},
                    {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单"},
                    {"type": "DocType", "link_to": "Purchase Receipt", "name": "采购入库单"},
                    {"type": "DocType", "link_to": "Supplier", "name": "供应商档案"},
                    {"type": "Report", "link_to": "Purchase Order Analysis", "name": "采购分析报表", "is_query_report": 1}
                ]
            },
            {
                "title": "车油能耗与合规中心",
                "items": [
                    {"type": "DocType", "link_to": "Oil Card", "name": "油卡档案"},
                    {"type": "DocType", "link_to": "Oil Card Recharge", "name": "油卡充值记录"},
                    {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "加油与能耗记录"},
                    {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "环保合规项"},
                    {"type": "DocType", "link_to": "Compliance Equipment Item", "name": "特种设备台账"},
                    {"type": "DocType", "link_to": "Employee Certificate Item", "name": "员工证书资质"}
                ]
            }
        ]
    )

    # 2. Child Workspaces
    build_workspace("Procurement Management", "采购管理", parent_page="My Business", sequence_id=1.1, shortcuts=[
        {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单"},
        {"type": "DocType", "link_to": "Purchase Receipt", "name": "采购入库单"},
        {"type": "DocType", "link_to": "Supplier", "name": "供应商管理"},
        {"type": "DocType", "link_to": "Material Request", "name": "采购申请单"}
    ])

    build_workspace("Stock and Inventory", "仓库与库存", parent_page="My Business", sequence_id=1.2, shortcuts=[
        {"type": "DocType", "link_to": "Item", "name": "物料主数据"},
        {"type": "DocType", "link_to": "Warehouse", "name": "仓库管理"},
        {"type": "DocType", "link_to": "Stock Entry", "name": "物料调拨与领用"},
        {"type": "DocType", "link_to": "Delivery Note", "name": "销售出库单"}
    ])

    build_workspace("Accounting and Finance", "会计与财务", parent_page="My Business", sequence_id=1.3, shortcuts=[
        {"type": "DocType", "link_to": "Purchase Invoice", "name": "应付发票"},
        {"type": "DocType", "link_to": "Sales Invoice", "name": "应收发票"},
        {"type": "DocType", "link_to": "Payment Entry", "name": "付款凭证"},
        {"type": "DocType", "link_to": "Reimbursement Request", "name": "员工报销申请"}
    ])

    build_workspace("Vehicle Fuel Hub", "车油能耗管理", parent_page="My Business", sequence_id=1.4, shortcuts=[
        {"type": "DocType", "link_to": "Oil Card", "name": "油卡档案"},
        {"type": "DocType", "link_to": "Oil Card Recharge", "name": "油卡充值流水"},
        {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "加油明细与能耗"},
        {"type": "DocType", "link_to": "Oil Card Invoice Batch", "name": "油票批量录入"}
    ])

    build_workspace("Company Compliance Center", "企业合规中心", parent_page="My Business", sequence_id=1.5, shortcuts=[
        {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "环保合规台账"},
        {"type": "DocType", "link_to": "Compliance Equipment Item", "name": "特种设备校验"},
        {"type": "DocType", "link_to": "Employee Certificate Item", "name": "员工证书资质"}
    ])

    print("\n=== EXPORTING WORKSPACES TO GIT APP ===")
    export_workspace_json("My Business", "my_business")
    export_workspace_json("Procurement Management", "procurement_management")
    export_workspace_json("Stock and Inventory", "stock_and_inventory")
    export_workspace_json("Accounting and Finance", "accounting_and_finance")
    export_workspace_json("Vehicle Fuel Hub", "vehicle_fuel_hub")
    export_workspace_json("Company Compliance Center", "company_compliance_center")

if __name__ == '__main__':
    main()
