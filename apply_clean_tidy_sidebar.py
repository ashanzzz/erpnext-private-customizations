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

def delete_redundant_workspaces():
    print("=== 1. Deleting Redundant / Cluttered Workspaces ===")
    redundant = ["Ashan CN Procurement", "查看所有物料"]
    for r in redundant:
        enc = urllib.parse.quote(r)
        res = call_api(f'/api/resource/Workspace/{enc}', method='DELETE')
        print(f"Deleted redundant workspace '{r}':", res is not None)

def update_clean_workspaces():
    print("\n=== 2. Configuring Clean Workspaces with hide_custom = 1 ===")
    
    # 1. Super All-in-One Root Workspace
    content_blocks = [
        {"id": "hdr_main", "type": "header", "data": {"text": "<span class=\"h3\"><b>我的业务 (总控主页)</b></span>", "col": 12}},
        {"id": "hdr_sc", "type": "header", "data": {"text": "<span class=\"text-muted small\"><b>常用高频业务直达</b></span>", "col": 12}}
    ]

    shortcuts = [
        {"type": "DocType", "link_to": "Item", "label": "物料主数据", "col": 3},
        {"type": "DocType", "link_to": "Warehouse", "label": "仓库管理", "col": 3},
        {"type": "DocType", "link_to": "Stock Entry", "label": "物料调拨与领用", "col": 3},
        {"type": "DocType", "link_to": "Delivery Note", "label": "销售出库单", "col": 3},
        
        {"type": "DocType", "link_to": "Purchase Order", "label": "采购订单", "col": 3},
        {"type": "DocType", "link_to": "Purchase Receipt", "label": "采购入库单", "col": 3},
        {"type": "DocType", "link_to": "Supplier", "label": "供应商管理", "col": 3},
        {"type": "DocType", "link_to": "Material Request", "label": "采购申请单", "col": 3},
        
        {"type": "DocType", "link_to": "Oil Card", "label": "油卡档案", "col": 3},
        {"type": "DocType", "link_to": "Oil Card Refuel Log", "label": "加油与能耗记录", "col": 3},
        {"type": "DocType", "link_to": "Reimbursement Request", "label": "员工报销申请", "col": 3},
        {"type": "DocType", "link_to": "Environmental Compliance Item", "label": "企业合规台账", "col": 3}
    ]

    for i, sc in enumerate(shortcuts):
        content_blocks.append({
            "id": f"sc_{i}_{sc['link_to'].lower().replace(' ', '_')}",
            "type": "shortcut",
            "data": {"shortcut_name": sc['label'], "col": sc.get('col', 3)}
        })

    sections = [
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

    formatted_links = []
    for s_idx, sec in enumerate(sections):
        content_blocks.append({
            "id": f"card_{s_idx}",
            "type": "card",
            "data": {"card_name": sec['title'], "col": 4}
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

    def save_ws(name, title, parent_page="", seq=1.0, icon="home", c_blocks=None, sc_list=None, l_list=None):
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
            "content": json.dumps(c_blocks or [{"id": "hdr", "type": "header", "data": {"text": f"<span class=\"h3\"><b>{title}</b></span>", "col": 12}}], ensure_ascii=False),
            "shortcuts": sc_list or [],
            "links": l_list or []
        }
        enc = urllib.parse.quote(name)
        existing = call_api(f'/api/resource/Workspace/{enc}')
        if existing and 'data' in existing:
            res = call_api(f'/api/resource/Workspace/{enc}', method='PUT', data=payload)
        else:
            res = call_api('/api/resource/Workspace', method='POST', data=payload)
        print(f"Saved Workspace '{name}' (Title: {title}, Parent: '{parent_page}', hide_custom: 1):", res is not None)

    # Root
    save_ws("My Business", "我的业务", parent_page="", seq=1.0, icon="home", c_blocks=content_blocks, sc_list=shortcuts, l_list=formatted_links)

    # 5 Child Workspaces
    save_ws("Procurement Management", "采购管理", parent_page="My Business", seq=1.1, icon="shopping-cart", sc_list=[
        {"type": "DocType", "link_to": "Purchase Order", "label": "采购订单"},
        {"type": "DocType", "link_to": "Purchase Receipt", "label": "采购入库单"},
        {"type": "DocType", "link_to": "Supplier", "label": "供应商管理"},
        {"type": "DocType", "link_to": "Material Request", "label": "采购申请单"}
    ])

    save_ws("Stock and Inventory", "仓库与库存", parent_page="My Business", seq=1.2, icon="package", sc_list=[
        {"type": "DocType", "link_to": "Item", "label": "物料主数据"},
        {"type": "DocType", "link_to": "Warehouse", "label": "仓库管理"},
        {"type": "DocType", "link_to": "Stock Entry", "label": "物料调拨与领用"},
        {"type": "DocType", "link_to": "Delivery Note", "label": "销售出库单"}
    ])

    save_ws("Accounting and Finance", "会计与财务", parent_page="My Business", seq=1.3, icon="credit-card", sc_list=[
        {"type": "DocType", "link_to": "Purchase Invoice", "label": "应付发票"},
        {"type": "DocType", "link_to": "Sales Invoice", "label": "应收发票"},
        {"type": "DocType", "link_to": "Payment Entry", "label": "付款凭证"},
        {"type": "DocType", "link_to": "Reimbursement Request", "label": "员工报销申请"}
    ])

    save_ws("Vehicle Fuel Hub", "车油能耗管理", parent_page="My Business", seq=1.4, icon="truck", sc_list=[
        {"type": "DocType", "link_to": "Oil Card", "label": "油卡档案"},
        {"type": "DocType", "link_to": "Oil Card Recharge", "label": "油卡充值流水"},
        {"type": "DocType", "link_to": "Oil Card Refuel Log", "label": "加油明细与能耗"},
        {"type": "DocType", "link_to": "Oil Card Invoice Batch", "label": "油票批量录入"}
    ])

    save_ws("Company Compliance Center", "企业合规中心", parent_page="My Business", seq=1.5, icon="shield", sc_list=[
        {"type": "DocType", "link_to": "Environmental Compliance Item", "label": "环保合规台账"},
        {"type": "DocType", "link_to": "Compliance Equipment Item", "label": "特种设备校验"},
        {"type": "DocType", "link_to": "Employee Certificate Item", "label": "员工证书资质"}
    ])

def export_all():
    print("\n=== 3. Exporting Workspaces to Local Git App JSON ===")
    workspaces = [
        ("My Business", "my_business"),
        ("Procurement Management", "procurement_management"),
        ("Stock and Inventory", "stock_and_inventory"),
        ("Accounting and Finance", "accounting_and_finance"),
        ("Vehicle Fuel Hub", "vehicle_fuel_hub"),
        ("Company Compliance Center", "company_compliance_center")
    ]
    # Remove any old exported dirs for redundant workspaces
    for old in ["ashan_cn_procurement", "查看所有物料"]:
        old_dir = os.path.join(r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\workspace", old)
        if os.path.exists(old_dir):
            import shutil
            shutil.rmtree(old_dir)
            print(f"Removed old workspace dir: {old_dir}")

    for ws_name, dir_name in workspaces:
        enc_name = urllib.parse.quote(ws_name)
        data = call_api(f'/api/resource/Workspace/{enc_name}')
        if not data or 'data' not in data:
            continue
        ws_doc = data['data']
        for k in ['modified', 'creation', 'owner', 'modified_by', 'docstatus', 'idx', '__last_sync_on']:
            ws_doc.pop(k, None)
        target_dir = os.path.join(r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\workspace", dir_name)
        os.makedirs(target_dir, exist_ok=True)
        json_path = os.path.join(target_dir, f"{dir_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ws_doc, f, indent=1, ensure_ascii=False)
        print(f"Exported clean JSON to {json_path}")

def main():
    delete_redundant_workspaces()
    update_clean_workspaces()
    export_all()

if __name__ == '__main__':
    main()
