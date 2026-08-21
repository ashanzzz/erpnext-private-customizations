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

def build_collapsible_sidebar():
    items = []
    
    # 1. 🏠 一级菜单：我的业务 (总控主页)
    items.append({
        "label": "我的业务 (总控主页)",
        "type": "Link",
        "link_type": "Workspace",
        "link_to": "My Business",
        "icon": "home",
        "child": 0,
        "collapsible": 0,
        "indent": 0,
        "keep_closed": 0,
        "idx": len(items) + 1
    })

    def add_level1_group(section_label, icon, children, default_closed=0):
        # 一级菜单 (Section Break / 标题，点击既折叠又联动小分类看板)
        items.append({
            "label": section_label,
            "type": "Section Break",
            "icon": icon,
            "child": 0,
            "collapsible": 1,
            "indent": 1,
            "keep_closed": default_closed,
            "idx": len(items) + 1
        })
        # 二级菜单 (纯文字，无图标，缩进)
        for child in children:
            items.append({
                "label": child['label'],
                "type": "Link",
                "link_type": child['link_type'],
                "link_to": child['link_to'],
                "icon": None,  # 二级菜单绝对无图标
                "is_query_report": child.get('is_query_report', 0),
                "child": 1,
                "collapsible": 0,
                "indent": 0,
                "keep_closed": 0,
                "idx": len(items) + 1
            })

    # 2. 一级菜单：仓库与库存
    add_level1_group(
        section_label="仓库与库存",
        icon="package",
        children=[
            {"label": "物料主数据", "link_type": "DocType", "link_to": "Item"},
            {"label": "仓库管理", "link_type": "DocType", "link_to": "Warehouse"},
            {"label": "物料调拨与领用", "link_type": "DocType", "link_to": "Stock Entry"},
            {"label": "销售出库单", "link_type": "DocType", "link_to": "Delivery Note"},
            {"label": "库存台账明细", "link_type": "Report", "link_to": "Stock Ledger", "is_query_report": 1}
        ]
    )

    # 3. 一级菜单：采购协同
    add_level1_group(
        section_label="采购协同",
        icon="shopping-cart",
        children=[
            {"label": "采购订单", "link_type": "DocType", "link_to": "Purchase Order"},
            {"label": "采购入库单", "link_type": "DocType", "link_to": "Purchase Receipt"},
            {"label": "供应商管理", "link_type": "DocType", "link_to": "Supplier"},
            {"label": "采购申请单", "link_type": "DocType", "link_to": "Material Request"},
            {"label": "采购执行分析", "link_type": "Report", "link_to": "Purchase Order Analysis", "is_query_report": 1}
        ]
    )

    # 4. 一级菜单：车油能耗中心
    add_level1_group(
        section_label="车油能耗中心",
        icon="truck",
        children=[
            {"label": "油卡档案", "link_type": "DocType", "link_to": "Oil Card"},
            {"label": "油卡充值流水", "link_type": "DocType", "link_to": "Oil Card Recharge"},
            {"label": "加油与能耗记录", "link_type": "DocType", "link_to": "Oil Card Refuel Log"},
            {"label": "油票批量录入", "link_type": "DocType", "link_to": "Oil Card Invoice Batch"},
            {"label": "车辆加油明细表", "link_type": "Report", "link_to": "Vehicle Refuel Ledger", "is_query_report": 1},
            {"label": "车油月度能耗汇总", "link_type": "Report", "link_to": "Vehicle Fuel Cost Summary", "is_query_report": 1}
        ]
    )

    # 5. 一级菜单：企业合规中心
    add_level1_group(
        section_label="企业合规中心",
        icon="shield",
        children=[
            {"label": "环保合规台账", "link_type": "DocType", "link_to": "Environmental Compliance Item"},
            {"label": "特种设备校验", "link_type": "DocType", "link_to": "Compliance Equipment Item"},
            {"label": "员工证书资质", "link_type": "DocType", "link_to": "Employee Certificate Item"},
            {"label": "企业合规总览报表", "link_type": "Report", "link_to": "Company Compliance Overview", "is_query_report": 1},
            {"label": "合规到期趋势预警", "link_type": "Report", "link_to": "Compliance Expiry Trend", "is_query_report": 1}
        ]
    )

    # 6. 一级菜单：财务与报销
    add_level1_group(
        section_label="财务与报销",
        icon="credit-card",
        children=[
            {"label": "员工报销申请", "link_type": "DocType", "link_to": "Reimbursement Request"},
            {"label": "待支付报销明细", "link_type": "Report", "link_to": "Unpaid Reimbursement List", "is_query_report": 1},
            {"label": "采购应付发票", "link_type": "DocType", "link_to": "Purchase Invoice"},
            {"label": "付款与核销凭证", "link_type": "DocType", "link_to": "Payment Entry"}
        ]
    )

    # Find existing sidebar
    sidebars = call_api('/api/resource/Workspace%20Sidebar?filters=[["app","=","ashan_cn_procurement"]]')
    if sidebars and 'data' in sidebars and len(sidebars['data']) > 0:
        sb_name = sidebars['data'][0]['name']
    else:
        sb_name = "业务扩展"

    payload = {
        "doctype": "Workspace Sidebar",
        "name": sb_name,
        "title": "业务扩展",
        "app": "ashan_cn_procurement",
        "module": "Ashan CN Procurement",
        "header_icon": "layers",
        "items": items
    }

    enc = urllib.parse.quote(sb_name)
    existing = call_api(f'/api/resource/Workspace%20Sidebar/{enc}')
    if existing and 'data' in existing:
        print(f"Updating Workspace Sidebar '{sb_name}'...")
        res = call_api(f'/api/resource/Workspace%20Sidebar/{enc}', method='PUT', data=payload)
    else:
        print(f"Creating Workspace Sidebar '{sb_name}'...")
        res = call_api('/api/resource/Workspace%20Sidebar', method='POST', data=payload)
    print("API update result:", res is not None)

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
        print(f"Exported clean Workspace Sidebar JSON to {json_path}")

if __name__ == '__main__':
    build_collapsible_sidebar()
