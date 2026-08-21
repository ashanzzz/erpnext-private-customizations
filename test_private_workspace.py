import os
import json
import urllib.request
import urllib.parse

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
TOKEN = os.getenv('ERPNEXT_TOKEN', '')

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

def create_user_workspace(name, title, parent_page="", shortcuts=None):
    # Set public=0 and for_user=ashanzzz1213@gmail.com
    payload = {
        "doctype": "Workspace",
        "name": name,
        "label": name,
        "title": title,
        "public": 0,
        "for_user": "ashanzzz1213@gmail.com",
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
        
    print(f"Creating User Workspace: {name} (Title: {title}, Parent: {parent_page})")
    enc_name = urllib.parse.quote(name)
    existing = call_api(f'/api/resource/Workspace/{enc_name}')
    if existing and 'data' in existing:
        res = call_api(f'/api/resource/Workspace/{enc_name}', method='PUT', data=payload)
    else:
        res = call_api('/api/resource/Workspace', method='POST', data=payload)
    return res

def main():
    # Create private workspace "我的业务" and children for user ashanzzz1213@gmail.com
    create_user_workspace("My Business-ashanzzz1213@gmail.com", "我的业务")
    
    create_user_workspace("Vehicle Management-ashanzzz1213@gmail.com", "车油管理", parent_page="My Business-ashanzzz1213@gmail.com", shortcuts=[
        {"type": "DocType", "link_to": "Vehicle", "name": "车辆台账"},
        {"type": "DocType", "link_to": "Oil Card Refuel Log", "name": "车辆加油台账"},
        {"type": "Report", "link_to": "Vehicle Fuel Cost Summary", "name": "车辆油耗汇总"}
    ])
    
    create_user_workspace("Compliance Center-ashanzzz1213@gmail.com", "公司合规中心", parent_page="My Business-ashanzzz1213@gmail.com", shortcuts=[
        {"type": "DocType", "link_to": "Compliance Equipment Item", "name": "特种设备到期"},
        {"type": "DocType", "link_to": "Employee Certificate Item", "name": "人员证书到期"},
        {"type": "DocType", "link_to": "Environmental Compliance Item", "name": "环保检测到期"}
    ])

    create_user_workspace("Reimbursements-ashanzzz1213@gmail.com", "报销申请", parent_page="My Business-ashanzzz1213@gmail.com", shortcuts=[
        {"type": "DocType", "link_to": "Reimbursement Request", "name": "报销申请台账"}
    ])

    create_user_workspace("Oil Cards-ashanzzz1213@gmail.com", "油卡", parent_page="My Business-ashanzzz1213@gmail.com", shortcuts=[
        {"type": "DocType", "link_to": "Oil Card", "name": "油卡卡片汇总"},
        {"type": "DocType", "link_to": "Oil Card Recharge", "name": "充值台账"}
    ])

if __name__ == '__main__':
    main()
