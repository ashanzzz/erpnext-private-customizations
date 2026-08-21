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

def build_sidebar():
    items = []
    
    def add_section(label, icon="folder", collapsible=1):
        items.append({
            "label": label,
            "type": "Section Break",
            "icon": icon,
            "collapsible": collapsible,
            "idx": len(items) + 1
        })
        
    def add_link(label, link_type, link_to, icon=None, is_query_report=0):
        items.append({
            "label": label,
            "type": "Link",
            "link_type": link_type,
            "link_to": link_to,
            "icon": icon,
            "is_query_report": is_query_report,
            "idx": len(items) + 1
        })

    # 1. 🏠 总控中心
    add_section("总控中心", icon="home", collapsible=0)
    add_link("我的业务 (总控大看板)", "Workspace", "My Business", icon="home")

    # 2. 📦 仓储与库存
    add_section("仓储与库存", icon="package", collapsible=1)
    add_link("仓库与库存工作区", "Workspace", "Stock and Inventory", icon="package")
    add_link("物料主数据", "DocType", "Item", icon="box")
    add_link("仓库管理", "DocType", "Warehouse", icon="warehouse")
    add_link("物料调拨与领用", "DocType", "Stock Entry", icon="move-horizontal")
    add_link("销售出库单", "DocType", "Delivery Note", icon="truck")
    add_link("库存台账明细", "Report", "Stock Ledger", icon="file-spreadsheet", is_query_report=1)

    # 3. 🛒 采购管理
    add_section("采购协同", icon="shopping-cart", collapsible=1)
    add_link("采购管理工作区", "Workspace", "Procurement Management", icon="shopping-cart")
    add_link("采购订单", "DocType", "Purchase Order", icon="file-text")
    add_link("采购入库单", "DocType", "Purchase Receipt", icon="file-check")
    add_link("供应商管理", "DocType", "Supplier", icon="users")
    add_link("采购申请单", "DocType", "Material Request", icon="file-plus")
    add_link("采购执行分析", "Report", "Purchase Order Analysis", icon="pie-chart", is_query_report=1)

    # 4. ⛽ 车油能耗中心
    add_section("车油能耗中心", icon="truck", collapsible=1)
    add_link("车油能耗工作区", "Workspace", "Vehicle Fuel Hub", icon="truck")
    add_link("油卡档案", "DocType", "Oil Card", icon="credit-card")
    add_link("油卡充值流水", "DocType", "Oil Card Recharge", icon="dollar-sign")
    add_link("加油与能耗记录", "DocType", "Oil Card Refuel Log", icon="fuel")
    add_link("油票批量录入", "DocType", "Oil Card Invoice Batch", icon="receipt")
    add_link("车辆加油明细表", "Report", "Vehicle Refuel Ledger", icon="file-text", is_query_report=1)
    add_link("车油月度能耗汇总", "Report", "Vehicle Fuel Cost Summary", icon="bar-chart-2", is_query_report=1)

    # 5. 🛡️ 企业合规中心
    add_section("企业合规中心", icon="shield", collapsible=1)
    add_link("企业合规工作区", "Workspace", "Company Compliance Center", icon="shield")
    add_link("环保合规台账", "DocType", "Environmental Compliance Item", icon="leaf")
    add_link("特种设备校验", "DocType", "Compliance Equipment Item", icon="wrench")
    add_link("员工证书资质", "DocType", "Employee Certificate Item", icon="award")
    add_link("企业合规总览报表", "Report", "Company Compliance Overview", icon="clipboard", is_query_report=1)
    add_link("合规到期趋势预警", "Report", "Compliance Expiry Trend", icon="alert-triangle", is_query_report=1)

    # 6. 💳 会计与财务
    add_section("会计与财务", icon="credit-card", collapsible=1)
    add_link("会计与财务工作区", "Workspace", "Accounting and Finance", icon="credit-card")
    add_link("员工报销申请", "DocType", "Reimbursement Request", icon="wallet")
    add_link("待支付报销明细", "Report", "Unpaid Reimbursement List", icon="list", is_query_report=1)
    add_link("应付发票", "DocType", "Purchase Invoice", icon="file-spreadsheet")
    add_link("付款凭证", "DocType", "Payment Entry", icon="credit-card")

    sidebar_name = "Ashan CN Procurement"
    payload = {
        "doctype": "Workspace Sidebar",
        "name": sidebar_name,
        "title": "业务扩展",
        "app": "ashan_cn_procurement",
        "module": "Ashan CN Procurement",
        "header_icon": "layers",
        "items": items
    }

    enc = urllib.parse.quote(sidebar_name)
    existing = call_api(f'/api/resource/Workspace%20Sidebar/{enc}')
    if existing and 'data' in existing:
        print(f"Updating Workspace Sidebar '{sidebar_name}'...")
        res = call_api(f'/api/resource/Workspace%20Sidebar/{enc}', method='PUT', data=payload)
    else:
        print(f"Creating Workspace Sidebar '{sidebar_name}'...")
        res = call_api('/api/resource/Workspace%20Sidebar', method='POST', data=payload)
    print("Result:", res is not None)

    # Export to app directory
    target_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\workspace_sidebar"
    os.makedirs(target_dir, exist_ok=True)
    json_path = os.path.join(target_dir, "ashan_cn_procurement.json")
    
    data = call_api(f'/api/resource/Workspace%20Sidebar/{enc}')
    if data and 'data' in data:
        doc = data['data']
        for k in ['modified', 'creation', 'owner', 'modified_by', 'docstatus', 'idx', '__last_sync_on']:
            doc.pop(k, None)
        if 'items' in doc:
            for row in doc['items']:
                for rk in ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'parent', 'parentfield', 'parenttype', 'idx']:
                    row.pop(rk, None)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
        print(f"Exported Workspace Sidebar JSON to {json_path}")

if __name__ == '__main__':
    build_sidebar()
