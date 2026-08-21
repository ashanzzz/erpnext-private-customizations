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
        print(f"Error {e.code}: {err_body}")
        return None

def push_client_script(script_name, dt, script_code):
    enc_name = urllib.parse.quote(script_name)
    existing = call_api(f'/api/resource/Client%20Script/{enc_name}')
    
    payload = {
        "dt": dt,
        "script": script_code,
        "enabled": 1
    }
    
    if existing and 'data' in existing:
        res = call_api(f'/api/resource/Client%20Script/{enc_name}', method='PUT', data=payload)
        print(f"[SUCCESS] Updated Client Script: {script_name}")
    else:
        payload["name"] = script_name
        res = call_api('/api/resource/Client%20Script', method='POST', data=payload)
        print(f"[SUCCESS] Created Client Script: {script_name}")

def main():
    js_code = """
$(document).ready(function() {
    init_ashan_sidebar();
    setInterval(init_ashan_sidebar, 1000);
});

function init_ashan_sidebar() {
    if ($('#ashan-custom-left-sidebar').length > 0) {
        return;
    }
    
    var container = $('.body-sidebar-top, .sidebar-items, .body-sidebar').first();
    if (!container.length) return;
    
    var html = `
    <div id="ashan-custom-left-sidebar" style="padding: 10px; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 10px; border-radius: 6px; font-size: 13px;">
        <div style="font-weight: bold; color: #1a202c; font-size: 14px; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 2px solid #3182ce; display: flex; align-items: center; justify-content: space-between;">
            <span>📂 我的业务菜单</span>
            <span style="font-size: 10px; color: #718096;">全架构</span>
        </div>
        
        <!-- 1. 车油管理 -->
        <div class="ashan-group" style="margin-bottom: 6px;">
            <div onclick="$(this).next('.ashan-sub').slideToggle(120)" style="cursor: pointer; padding: 6px 8px; background: #f7fafc; border-radius: 4px; font-weight: bold; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                <span>🚗 车油管理</span>
                <span style="font-size: 10px; color: #a0aec0;">▼</span>
            </div>
            <div class="ashan-sub" style="display: none; padding-left: 12px; padding-top: 4px;">
                <a href="/desk/oil-card-refuel-log" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 车辆加油台账</a>
                <a href="/desk/query-report/Vehicle%20Fuel%20Cost%20Summary" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 车辆油耗汇总</a>
                <a href="/desk/query-report/Vehicle%20Monthly%20Fuel%20Trend" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">└ 车辆月度燃油趋势</a>
            </div>
        </div>

        <!-- 2. 公司合规中心 -->
        <div class="ashan-group" style="margin-bottom: 6px;">
            <div onclick="$(this).next('.ashan-sub').slideToggle(120)" style="cursor: pointer; padding: 6px 8px; background: #f7fafc; border-radius: 4px; font-weight: bold; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                <span>🛡️ 公司合规中心</span>
                <span style="font-size: 10px; color: #a0aec0;">▼</span>
            </div>
            <div class="ashan-sub" style="display: none; padding-left: 12px; padding-top: 4px;">
                <a href="/desk/compliance-equipment-item" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 特种设备到期</a>
                <a href="/desk/employee-certificate-item" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 人员证书到期</a>
                <a href="/desk/environmental-compliance-item" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 环保检测到期</a>
                <a href="/desk/query-report/Company%20Compliance%20Overview" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">└ 合规中心临期逾期总览</a>
            </div>
        </div>

        <!-- 3. 报销申请 -->
        <div class="ashan-group" style="margin-bottom: 6px;">
            <div onclick="$(this).next('.ashan-sub').slideToggle(120)" style="cursor: pointer; padding: 6px 8px; background: #f7fafc; border-radius: 4px; font-weight: bold; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                <span>📄 报销申请</span>
                <span style="font-size: 10px; color: #a0aec0;">▼</span>
            </div>
            <div class="ashan-sub" style="display: none; padding-left: 12px; padding-top: 4px;">
                <a href="/desk/reimbursement-request" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 直接采购报销工作台</a>
                <a href="/desk/query-report/Unpaid%20Reimbursement%20List" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 未付款报销清单</a>
                <a href="/desk/query-report/Reimbursement%20Payment%20Status" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">└ 报销付款状态</a>
            </div>
        </div>

        <!-- 4. 受限单据组 -->
        <div class="ashan-group" style="margin-bottom: 6px;">
            <div onclick="$(this).next('.ashan-sub').slideToggle(120)" style="cursor: pointer; padding: 6px 8px; background: #f7fafc; border-radius: 4px; font-weight: bold; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                <span>🔒 受限单据组</span>
                <span style="font-size: 10px; color: #a0aec0;">▼</span>
            </div>
            <div class="ashan-sub" style="display: none; padding-left: 12px; padding-top: 4px;">
                <a href="/desk/restricted-access-group" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 受限单据组</a>
                <a href="/desk/restricted-access-group-role" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 组角色分配</a>
                <a href="/desk/restricted-access-group-user" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">└ 组人员分配</a>
            </div>
        </div>

        <!-- 5. 油卡管理 -->
        <div class="ashan-group" style="margin-bottom: 6px;">
            <div onclick="$(this).next('.ashan-sub').slideToggle(120)" style="cursor: pointer; padding: 6px 8px; background: #f7fafc; border-radius: 4px; font-weight: bold; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                <span>💳 油卡管理</span>
                <span style="font-size: 10px; color: #a0aec0;">▼</span>
            </div>
            <div class="ashan-sub" style="display: none; padding-left: 12px; padding-top: 4px;">
                <a href="/desk/oil-card" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 油卡卡片汇总</a>
                <a href="/desk/oil-card-recharge" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 充值台账</a>
                <a href="/desk/oil-card-invoice-batch" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 供应商开票汇总</a>
                <a href="/desk/query-report/Oil%20Card%20Monthly%20Ledger" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">├ 油卡月度台账</a>
                <a href="/desk/query-report/Oil%20Card%20Balance%20Reconciliation" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">└ 充值使用结余对账</a>
            </div>
        </div>

        <!-- 6. 报表中心 -->
        <div class="ashan-group" style="margin-bottom: 6px;">
            <div onclick="$(this).next('.ashan-sub').slideToggle(120)" style="cursor: pointer; padding: 6px 8px; background: #f7fafc; border-radius: 4px; font-weight: bold; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                <span>📊 报表与控制台</span>
                <span style="font-size: 10px; color: #a0aec0;">▼</span>
            </div>
            <div class="ashan-sub" style="display: none; padding-left: 12px; padding-top: 4px;">
                <a href="/desk/ashan-cn-procurement" style="display: block; padding: 3px 0; color: #4a5568; text-decoration: none;">└ 业务扩展总控中心</a>
            </div>
        </div>
    </div>
    `;
    
    container.prepend(html);
}
"""
    # Push to Workspace & User & Oil Card
    push_client_script("Ashan Sidebar Workspace Script", "Workspace", js_code)
    push_client_script("Ashan Sidebar User Script", "User", js_code)
    push_client_script("Ashan Sidebar Oil Card Script", "Oil Card", js_code)

if __name__ == '__main__':
    main()
