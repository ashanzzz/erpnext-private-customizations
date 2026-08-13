import os
import json
import urllib.request
import urllib.parse
import sys

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
TOKEN = os.getenv('ERPNEXT_TOKEN', 'token 781e6538a0816f3:ebfe8d61c03e289')

def call_api(endpoint, method='GET', data=None):
    headers = {
        'Authorization': TOKEN,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    req_url = f"{SITE_URL.rstrip('/')}{endpoint}"
    encoded_data = json.dumps(data).encode('utf-8') if data else None
    
    req = urllib.request.Request(req_url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"Error {e.code} on {method} {endpoint}: {err_body}")
        return None

def create_workspace(name, title, parent_page="", is_root=False, shortcuts=None):
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
        "content": "[]",
    }
    
    if shortcuts:
        payload["content"] = json.dumps([
            {
                "id": f"hdr_{name}",
                "type": "header",
                "data": {"text": f"<span class=\"h4\"><b>{title} 快捷入口</b></span>", "col": 12}
            }
        ] + [
            {
                "id": f"sc_{i}",
                "type": "shortcut",
                "data": {"shortcut_name": sc['name'], "col": 4}
            } for i, sc in enumerate(shortcuts)
        ])
        
        payload["shortcuts"] = [
            {
                "type": sc['type'],
                "link_to": sc['link_to'],
                "label": sc['name']
            } for sc in shortcuts
        ]
        
    print(f"Creating Workspace: {name} (Title: {title}, Parent: {parent_page})")
    enc_name = urllib.parse.quote(name)
    existing = call_api(f'/api/resource/Workspace/{enc_name}')
    if existing and 'data' in existing:
        res = call_api(f'/api/resource/Workspace/{enc_name}', method='PUT', data=payload)
    else:
        res = call_api('/api/resource/Workspace', method='POST', data=payload)
        
    if not res:
        print(f"FAILED to create {name}!")
        sys.exit(1)
    return res

def main():
    res = create_workspace("My Business", "我的业务", is_root=True)
    
    create_workspace("Vehicle Management", "车油管理", parent_page="My Business", shortcuts=[
        {"type": "DocType", "link_to": "Vehicle", "name": "车辆台账"},
        {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "车辆加油台账"},
        {"type": "Report", "link_to": "Vehicle Fuel Cost Summary", "name": "车辆油耗汇总"}
    ])
    
    create_workspace("Compliance Center", "公司合规中心", parent_page="My Business", shortcuts=[
        {"type": "DocType", "link_to": "Compliance Equipment Item", "name": "特种设备到期"},
        {"type": "DocType", "link_to": "Employee Certificate Item", "name": "人员证书到期"},
        {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "环保检测到期"}
    ])
    
    create_workspace("Reimbursements", "报销申请", parent_page="My Business", shortcuts=[
        {"type": "DocType", "link_to": "Reimbursement Request", "name": "报销申请台账"}
    ])
    
    create_workspace("Oil Cards", "油卡", parent_page="My Business", shortcuts=[
        {"type": "DocType", "link_to": "Oil Card", "name": "油卡卡片汇总"},
        {"type": "DocType", "link_to": "Oil Card Recharge", "name": "充值台账"}
    ])
    
    # Update Ashan CN Procurement
    home_ws = call_api('/api/resource/Workspace/Ashan%20CN%20Procurement')
    if home_ws and 'data' in home_ws:
        home_payload = home_ws['data']
        home_payload['parent_page'] = "My Business"
        call_api('/api/resource/Workspace/Ashan%20CN%20Procurement', method='PUT', data=home_payload)

if __name__ == '__main__':
    main()
