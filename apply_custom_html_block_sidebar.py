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

def main():
    block_name = "Ashan Left Sidebar Block"
    
    html_content = '<div id="ashan-sidebar-injector" style="display:none;"></div>'
    
    script_content = """
(function() {
    function renderAshanSidebar() {
        if ($('#ashan-left-tree').length > 0) return;
        
        var sidebar = $('.body-sidebar-top, .sidebar-items, .body-sidebar').first();
        if (!sidebar.length) return;
        
        var treeHtml = `
        <div id="ashan-left-tree" style="margin-bottom: 15px; padding: 12px; background: #ffffff; border-radius: 8px; border: 1px solid #cbd5e0; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-weight: 700; color: #2d3748; font-size: 14px; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 2px solid #3182ce; display: flex; justify-content: space-between; align-items: center;">
                <span>📂 我的业务全景菜单</span>
                <span style="font-size: 10px; background: #ebf8ff; color: #2b6cb0; padding: 2px 6px; border-radius: 4px; font-weight: bold;">6大板块</span>
            </div>

            <!-- 1. 🚗 车油管理 -->
            <div style="margin-bottom: 6px;">
                <div onclick="$(this).next('.sub-menu').slideToggle(120)" style="cursor: pointer; padding: 7px 10px; background: #edf2f7; border-radius: 6px; font-weight: 600; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                    <span>🚗 车油管理</span>
                    <span style="font-size: 10px; color: #718096;">▼</span>
                </div>
                <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                    <a href="/desk/oil-card-refuel-log" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 车辆加油台账</a>
                    <a href="/desk/query-report/Vehicle%20Fuel%20Cost%20Summary" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 车辆油耗汇总</a>
                    <a href="/desk/query-report/Vehicle%20Monthly%20Fuel%20Trend" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">└ 车辆月度燃油趋势</a>
                </div>
            </div>

            <!-- 2. 🛡️ 公司合规中心 -->
            <div style="margin-bottom: 6px;">
                <div onclick="$(this).next('.sub-menu').slideToggle(120)" style="cursor: pointer; padding: 7px 10px; background: #edf2f7; border-radius: 6px; font-weight: 600; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                    <span>🛡️ 公司合规中心</span>
                    <span style="font-size: 10px; color: #718096;">▼</span>
                </div>
                <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                    <a href="/desk/compliance-equipment-item" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 特种设备到期</a>
                    <a href="/desk/employee-certificate-item" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 人员证书到期</a>
                    <a href="/desk/environmental-compliance-item" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 环保检测到期</a>
                    <a href="/desk/query-report/Company%20Compliance%20Overview" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">└ 合规中心临期逾期总览</a>
                </div>
            </div>

            <!-- 3. 📄 报销申请 -->
            <div style="margin-bottom: 6px;">
                <div onclick="$(this).next('.sub-menu').slideToggle(120)" style="cursor: pointer; padding: 7px 10px; background: #edf2f7; border-radius: 6px; font-weight: 600; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                    <span>📄 报销申请</span>
                    <span style="font-size: 10px; color: #718096;">▼</span>
                </div>
                <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                    <a href="/desk/reimbursement-request" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 直接采购报销工作台</a>
                    <a href="/desk/query-report/Unpaid%20Reimbursement%20List" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 未付款报销清单</a>
                    <a href="/desk/query-report/Reimbursement%20Payment%20Status" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">└ 报销付款状态</a>
                </div>
            </div>

            <!-- 4. 🔒 受限单据组 -->
            <div style="margin-bottom: 6px;">
                <div onclick="$(this).next('.sub-menu').slideToggle(120)" style="cursor: pointer; padding: 7px 10px; background: #edf2f7; border-radius: 6px; font-weight: 600; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                    <span>🔒 受限单据组</span>
                    <span style="font-size: 10px; color: #718096;">▼</span>
                </div>
                <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                    <a href="/desk/restricted-access-group" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 受限单据组</a>
                    <a href="/desk/restricted-access-group-role" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 组角色分配</a>
                    <a href="/desk/restricted-access-group-user" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">└ 组人员分配</a>
                </div>
            </div>

            <!-- 5. 💳 油卡管理 -->
            <div style="margin-bottom: 6px;">
                <div onclick="$(this).next('.sub-menu').slideToggle(120)" style="cursor: pointer; padding: 7px 10px; background: #edf2f7; border-radius: 6px; font-weight: 600; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                    <span>💳 油卡管理</span>
                    <span style="font-size: 10px; color: #718096;">▼</span>
                </div>
                <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                    <a href="/desk/oil-card" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 油卡卡片汇总</a>
                    <a href="/desk/oil-card-recharge" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 充值台账</a>
                    <a href="/desk/oil-card-invoice-batch" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 供应商开票汇总</a>
                    <a href="/desk/query-report/Oil%20Card%20Monthly%20Ledger" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">├ 油卡月度台账</a>
                    <a href="/desk/query-report/Oil%20Card%20Balance%20Reconciliation" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">└ 充值使用结余对账</a>
                </div>
            </div>

            <!-- 6. 📊 报表中心 -->
            <div style="margin-bottom: 6px;">
                <div onclick="$(this).next('.sub-menu').slideToggle(120)" style="cursor: pointer; padding: 7px 10px; background: #edf2f7; border-radius: 6px; font-weight: 600; color: #2d3748; display: flex; justify-content: space-between; align-items: center;">
                    <span>📊 报表中心</span>
                    <span style="font-size: 10px; color: #718096;">▼</span>
                </div>
                <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                    <a href="/desk/ashan-cn-procurement" style="display: block; padding: 4px 0; color: #4a5568; text-decoration: none; font-size: 12px;">└ 业务扩展总控中心</a>
                </div>
            </div>
        </div>
        `;

        sidebar.prepend(treeHtml);
    }

    renderAshanSidebar();
    setInterval(renderAshanSidebar, 1000);
})();
"""

    # 1. Create or update Custom HTML Block
    enc_block = urllib.parse.quote(block_name)
    existing_block = call_api(f'/api/resource/Custom%20HTML%20Block/{enc_block}')
    
    payload_block = {
        "doctype": "Custom HTML Block",
        "name": block_name,
        "private": 0,
        "html": html_content,
        "script": script_content
    }
    
    if existing_block and 'data' in existing_block:
        call_api(f'/api/resource/Custom%20HTML%20Block/{enc_block}', method='PUT', data=payload_block)
        print("[SUCCESS] Updated Custom HTML Block:", block_name)
    else:
        call_api('/api/resource/Custom%20HTML%20Block', method='POST', data=payload_block)
        print("[SUCCESS] Created Custom HTML Block:", block_name)

    # 2. Add this Custom HTML Block to Workspace 'Ashan CN Procurement'
    enc_ws = urllib.parse.quote('Ashan CN Procurement')
    ws = call_api(f'/api/resource/Workspace/{enc_ws}')
    if ws and 'data' in ws:
        ws_data = ws['data']
        content = json.loads(ws_data.get('content', '[]'))
        
        # Add custom block at top if not present
        if not any(b.get('id') == 'ashan_left_sidebar_block' for b in content):
            content.insert(0, {
                "id": "ashan_left_sidebar_block",
                "type": "custom_block",
                "data": {
                    "custom_block_name": block_name,
                    "col": 12
                }
            })
            
            # Also add to child table custom_blocks
            custom_blocks = ws_data.get('custom_blocks', [])
            if not any(cb.get('custom_block_name') == block_name for cb in custom_blocks):
                custom_blocks.append({"custom_block_name": block_name, "label": block_name})
                ws_data['custom_blocks'] = custom_blocks
                
            ws_data['content'] = json.dumps(content)
            res_ws = call_api(f'/api/resource/Workspace/{enc_ws}', method='PUT', data=ws_data)
            print("[SUCCESS] Attached Custom HTML Block to Workspace Ashan CN Procurement!")

if __name__ == '__main__':
    main()
