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

def main():
    workspace_name = "Ashan CN Procurement"
    
    # Define blocks for Workspace content
    blocks = [
        # Main Header & KPIs
        {"id": "b_hdr_main", "type": "header", "data": {"text": "<div class=\"my-2\"><span class=\"h3\"><b>业务扩展总控中心</b></span></div>", "col": 12}},
        {"id": "kpi_po", "type": "number_card", "data": {"number_card_name": "近一个月采购总额", "col": 3}},
        {"id": "kpi_fuel", "type": "number_card", "data": {"number_card_name": "本月油耗总支出", "col": 3}},
        {"id": "kpi_reimb", "type": "number_card", "data": {"number_card_name": "待处理报销总额", "col": 3}},
        {"id": "kpi_cards", "type": "number_card", "data": {"number_card_name": "运行中油卡数量", "col": 3}},

        # 1. 🚗 车油管理
        {"id": "b_hdr_fuel", "type": "header", "data": {"text": "<hr class=\"my-4\"/><span class=\"h4 text-primary\"><b>🚗 车油管理</b></span>", "col": 12}},
        {"id": "sc_fuel_1", "type": "shortcut", "data": {"shortcut_name": "车辆加油台账", "col": 4}},
        {"id": "sc_fuel_2", "type": "shortcut", "data": {"shortcut_name": "车辆油耗汇总", "col": 4}},
        {"id": "sc_fuel_3", "type": "shortcut", "data": {"shortcut_name": "车辆月度燃油趋势", "col": 4}},

        # 2. 🛡️ 公司合规中心
        {"id": "b_hdr_comp", "type": "header", "data": {"text": "<hr class=\"my-4\"/><span class=\"h4 text-primary\"><b>🛡️ 公司合规中心</b></span>", "col": 12}},
        {"id": "sc_comp_1", "type": "shortcut", "data": {"shortcut_name": "特种设备到期", "col": 3}},
        {"id": "sc_comp_2", "type": "shortcut", "data": {"shortcut_name": "人员证书到期", "col": 3}},
        {"id": "sc_comp_3", "type": "shortcut", "data": {"shortcut_name": "环保检测到期", "col": 3}},
        {"id": "sc_comp_4", "type": "shortcut", "data": {"shortcut_name": "合规中心临期逾期总览", "col": 3}},

        # 3. 📄 报销申请
        {"id": "b_hdr_reimb", "type": "header", "data": {"text": "<hr class=\"my-4\"/><span class=\"h4 text-primary\"><b>📄 报销申请</b></span>", "col": 12}},
        {"id": "sc_reimb_1", "type": "shortcut", "data": {"shortcut_name": "直接采购报销工作台", "col": 4}},
        {"id": "sc_reimb_2", "type": "shortcut", "data": {"shortcut_name": "未付款报销清单", "col": 4}},
        {"id": "sc_reimb_3", "type": "shortcut", "data": {"shortcut_name": "Reimbursement Payment Status", "col": 4}},

        # 4. 🔒 受限单据组
        {"id": "b_hdr_grp", "type": "header", "data": {"text": "<hr class=\"my-4\"/><span class=\"h4 text-primary\"><b>🔒 受限单据组</b></span>", "col": 12}},
        {"id": "sc_grp_1", "type": "shortcut", "data": {"shortcut_name": "受限单据组", "col": 4}},
        {"id": "sc_grp_2", "type": "shortcut", "data": {"shortcut_name": "受限单据组角色", "col": 4}},
        {"id": "sc_grp_3", "type": "shortcut", "data": {"shortcut_name": "受限单据组用户", "col": 4}},

        # 5. 💳 油卡管理
        {"id": "b_hdr_card", "type": "header", "data": {"text": "<hr class=\"my-4\"/><span class=\"h4 text-primary\"><b>💳 油卡管理</b></span>", "col": 12}},
        {"id": "sc_card_1", "type": "shortcut", "data": {"shortcut_name": "油卡卡片汇总", "col": 4}},
        {"id": "sc_card_2", "type": "shortcut", "data": {"shortcut_name": "充值台账", "col": 4}},
        {"id": "sc_card_3", "type": "shortcut", "data": {"shortcut_name": "供应商开票汇总", "col": 4}},
        {"id": "sc_card_4", "type": "shortcut", "data": {"shortcut_name": "Oil Card Monthly Ledger", "col": 6}},
        {"id": "sc_card_5", "type": "shortcut", "data": {"shortcut_name": "油卡充值使用结余对账", "col": 6}},

        # 6. 📊 趋势大盘
        {"id": "b_hdr_chart", "type": "header", "data": {"text": "<hr class=\"my-4\"/><span class=\"h4 text-primary\"><b>📊 采购与业务趋势大盘</b></span>", "col": 12}},
        {"id": "chart_po_trend", "type": "chart", "data": {"chart_name": "近一年采购订单趋势", "col": 12}},
    ]
    
    # Child table shortcuts definitions
    shortcuts_list = [
        # 车油管理
        {"type": "DocType", "link_to": "Oil Card Refuel Log", "label": "车辆加油台账", "icon": "file-text"},
        {"type": "Report", "link_to": "Vehicle Fuel Cost Summary", "label": "车辆油耗汇总", "icon": "bar-chart-2"},
        {"type": "Report", "link_to": "Vehicle Monthly Fuel Trend", "label": "车辆月度燃油趋势", "icon": "trending-up"},
        # 公司合规中心
        {"type": "DocType", "link_to": "Compliance Equipment Item", "label": "特种设备到期", "icon": "alert-circle"},
        {"type": "DocType", "link_to": "Employee Certificate Item", "label": "人员证书到期", "icon": "user-check"},
        {"type": "DocType", "link_to": "Environmental Compliance Item", "label": "环保检测到期", "icon": "shield"},
        {"type": "Report", "link_to": "Company Compliance Overview", "label": "合规中心临期逾期总览", "icon": "pie-chart"},
        # 报销申请
        {"type": "DocType", "link_to": "Reimbursement Request", "label": "直接采购报销工作台", "icon": "credit-card"},
        {"type": "Report", "link_to": "Unpaid Reimbursement List", "label": "未付款报销清单", "icon": "list"},
        {"type": "Report", "link_to": "Reimbursement Payment Status", "label": "Reimbursement Payment Status", "icon": "check-circle"},
        # 受限单据组
        {"type": "DocType", "link_to": "Restricted Access Group", "label": "受限单据组", "icon": "lock"},
        {"type": "DocType", "link_to": "Restricted Access Group Role", "label": "受限单据组角色", "icon": "users"},
        {"type": "DocType", "link_to": "Restricted Access Group User", "label": "受限单据组用户", "icon": "user"},
        # 油卡
        {"type": "DocType", "link_to": "Oil Card", "label": "油卡卡片汇总", "icon": "credit-card"},
        {"type": "DocType", "link_to": "Oil Card Recharge", "label": "充值台账", "icon": "plus-circle"},
        {"type": "DocType", "link_to": "Oil Card Invoice Batch", "label": "供应商开票汇总", "icon": "file-minus"},
        {"type": "Report", "link_to": "Oil Card Monthly Ledger", "label": "Oil Card Monthly Ledger", "icon": "book-open"},
        {"type": "Report", "link_to": "Oil Card Balance Reconciliation", "label": "油卡充值使用结余对账", "icon": "dollar-sign"},
    ]
    
    # Fetch existing workspace
    enc_name = urllib.parse.quote(workspace_name)
    existing = call_api(f'/api/resource/Workspace/{enc_name}')
    if not existing or 'data' not in existing:
        print("Workspace not found!")
        return

    data = existing['data']
    data['content'] = json.dumps(blocks)
    data['shortcuts'] = shortcuts_list
    data['title'] = "业务扩展"
    data['public'] = 1
    data['is_hidden'] = 0

    print("Updating Workspace content with full 6-module architecture...")
    res = call_api(f'/api/resource/Workspace/{enc_name}', method='PUT', data=data)
    if res and 'data' in res:
        print("[SUCCESS] Updated Workspace Ashan CN Procurement successfully!")
    else:
        print("[FAILED] Update failed:", res)

if __name__ == '__main__':
    main()
