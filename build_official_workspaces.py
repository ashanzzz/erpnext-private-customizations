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
SITE_URL = 'http://192.168.8.11:6888'
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

def create_or_update_workspace(name, title, parent_page="", shortcuts=None, sequence_id=1.0):
    content_blocks = [
        {
            "id": f"hdr_{name.lower().replace(' ', '_')}",
            "type": "header",
            "data": {"text": f"<span class=\"h3\"><b>{title}</b></span>", "col": 12}
        }
    ]
    
    formatted_shortcuts = []
    if shortcuts:
        for i, sc in enumerate(shortcuts):
            content_blocks.append({
                "id": f"sc_{i}_{sc['link_to'].lower().replace(' ', '_')}",
                "type": "shortcut",
                "data": {"shortcut_name": sc['name'], "col": 4}
            })
            shortcut_dict = {
                "type": sc['type'],
                "label": sc['name']
            }
            if sc['type'] == 'URL':
                shortcut_dict['url'] = sc['link_to']
            else:
                shortcut_dict['link_to'] = sc['link_to']
                
            formatted_shortcuts.append(shortcut_dict)
            
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
        "shortcuts": formatted_shortcuts
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
    # Clean auto fields
    for k in ['modified', 'creation', 'owner', 'modified_by', 'docstatus', 'idx', '__last_sync_on']:
        ws_doc.pop(k, None)
        
    target_dir = os.path.join(r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\workspace", dir_name)
    os.makedirs(target_dir, exist_ok=True)
    json_path = os.path.join(target_dir, f"{dir_name}.json")
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ws_doc, f, indent=1, ensure_ascii=False)
    print(f"Exported JSON to {json_path}")

def main():
    # 1. Root Workspace
    create_or_update_workspace("My Business", "我的业务", parent_page="", sequence_id=1.0)
    
    # 2. Child Workspaces
    create_or_update_workspace("Procurement Management", "采购管理", parent_page="My Business", sequence_id=1.1, shortcuts=[
        {"type": "DocType", "link_to": "Purchase Order", "name": "采购订单"},
        {"type": "DocType", "link_to": "Purchase Receipt", "name": "采购入库单"},
        {"type": "DocType", "link_to": "Supplier", "name": "供应商管理"},
        {"type": "DocType", "link_to": "Material Request", "name": "采购申请单"}
    ])
    
    create_or_update_workspace("Stock and Inventory", "仓库与库存", parent_page="My Business", sequence_id=1.2, shortcuts=[
        {"type": "DocType", "link_to": "Item", "name": "物料主数据"},
        {"type": "DocType", "link_to": "Warehouse", "name": "仓库管理"},
        {"type": "DocType", "link_to": "Stock Entry", "name": "物料调拨与领用"},
        {"type": "DocType", "link_to": "Delivery Note", "name": "销售出库单"}
    ])
    
    create_or_update_workspace("Accounting and Finance", "会计与财务", parent_page="My Business", sequence_id=1.3, shortcuts=[
        {"type": "DocType", "link_to": "Purchase Invoice", "name": "应付发票"},
        {"type": "DocType", "link_to": "Sales Invoice", "name": "应收发票"},
        {"type": "DocType", "link_to": "Payment Entry", "name": "付款凭证"}
    ])
    
    create_or_update_workspace("Vehicle Fuel Hub", "车油能耗管理", parent_page="My Business", sequence_id=1.4, shortcuts=[
        {"type": "DocType", "link_to": "Vehicle", "name": "车辆台账"}
    ])
    
    create_or_update_workspace("Company Compliance Center", "企业合规中心", parent_page="My Business", sequence_id=1.5, shortcuts=[
        {"type": "DocType", "link_to": "Vehicle", "name": "合规设备/车辆关联"}
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
