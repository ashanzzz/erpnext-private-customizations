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
        var sidebar = $('.body-sidebar');
        if (!sidebar.length) return;
        
        var isHideOriginal = localStorage.getItem('ashan_hide_original') === '1';
        
        if ($('#ashan-custom-styles').length === 0) {
            $('head').append(`<style id="ashan-custom-styles">
                .ashan-sidebar-module { cursor: pointer; padding: 7px 10px; border-radius: 6px; font-weight: 500; color: #1f272e; display: flex; justify-content: space-between; align-items: center; transition: background-color 0.2s; }
                .ashan-sidebar-module:hover { background-color: #f3f4f6; }
                .ashan-sidebar-link { display: block; padding: 6px 10px; border-radius: 6px; color: #1f272e; text-decoration: none; font-size: 13px; margin-bottom: 2px; transition: background-color 0.2s; }
                .ashan-sidebar-link:hover { background-color: #f3f4f6; }
                .ashan-sidebar-title { font-weight: 600; color: #8d99a6; font-size: 11px; margin-bottom: 10px; padding: 4px 8px; display: flex; justify-content: space-between; align-items: center; text-transform: uppercase; letter-spacing: 0.5px; }
            </style>`);
        }

        if ($('#ashan-left-tree').length === 0) {
            var treeHtml = `
            <div id="ashan-left-tree" style="margin: 10px 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <!-- Title & Toggle Switch -->
                <div class="ashan-sidebar-title">
                    <span>📂 我的业务全景菜单</span>
                    <label style="display: flex; align-items: center; cursor: pointer; font-size: 11px; color: #8d99a6; margin: 0; user-select: none; text-transform: none; letter-spacing: normal;">
                        <input type="checkbox" id="ashan-toggle-original" ${isHideOriginal ? 'checked' : ''} style="margin-right: 4px; cursor: pointer;" onchange="window.ashanToggleOriginal(this.checked)">
                        <span>隐藏原生菜单</span>
                    </label>
                </div>

                <!-- 1. 📊 业务总览与大盘 -->
                <div style="margin-bottom: 6px;">
                    <div class="ashan-sidebar-module" onclick="$(this).next('.sub-menu').slideToggle(120)">
                        <span>📊 业务总览与大盘</span>
                        <span style="font-size: 10px; color: #718096;">▼</span>
                    </div>
                    <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('Workspaces', 'Ashan CN Procurement'); return false;">业务扩展总控中心</a>
                    </div>
                </div>

                <!-- 2. ⛽ 车辆与油卡一体化管理 -->
                <div style="margin-bottom: 6px;">
                    <div class="ashan-sidebar-module" onclick="$(this).next('.sub-menu').slideToggle(120)">
                        <span>⛽ 车辆与油卡管理</span>
                        <span style="font-size: 10px; color: #718096;">▼</span>
                    </div>
                    <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                        <!-- 业务台账 -->
                        <div style="font-size: 11px; color: #a0aec0; margin-top: 4px; margin-bottom: 2px; padding-left: 10px;">业务台账</div>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Oil Card'); return false;">油卡卡片汇总</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Oil Card Refuel Log'); return false;">车辆加油台账</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Oil Card Recharge'); return false;">油卡充值台账</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Oil Card Invoice Batch'); return false;">供应商开票汇总</a>
                        <!-- 数据报表 -->
                        <div style="font-size: 11px; color: #a0aec0; margin-top: 6px; margin-bottom: 2px; padding-left: 10px;">数据报表</div>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('query-report', 'Vehicle Fuel Cost Summary'); return false;">车辆油耗汇总</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('query-report', 'Vehicle Monthly Fuel Trend'); return false;">车辆月度燃油趋势</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('query-report', 'Oil Card Monthly Ledger'); return false;">油卡月度台账</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('query-report', 'Oil Card Balance Reconciliation'); return false;">充值使用结余对账</a>
                    </div>
                </div>

                <!-- 3. 🛡️ 公司合规风控中心 -->
                <div style="margin-bottom: 6px;">
                    <div class="ashan-sidebar-module" onclick="$(this).next('.sub-menu').slideToggle(120)">
                        <span>🛡️ 公司合规风控中心</span>
                        <span style="font-size: 10px; color: #718096;">▼</span>
                    </div>
                    <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Compliance Equipment Item'); return false;">特种设备到期</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Employee Certificate Item'); return false;">人员证书到期</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Environmental Compliance Item'); return false;">环保检测到期</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('query-report', 'Company Compliance Overview'); return false;">合规中心临期逾期总览</a>
                    </div>
                </div>

                <!-- 4. 📄 采购报销流转 -->
                <div style="margin-bottom: 6px;">
                    <div class="ashan-sidebar-module" onclick="$(this).next('.sub-menu').slideToggle(120)">
                        <span>📄 采购报销流转</span>
                        <span style="font-size: 10px; color: #718096;">▼</span>
                    </div>
                    <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Reimbursement Request'); return false;">直接采购报销工作台</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('query-report', 'Unpaid Reimbursement List'); return false;">未付款报销清单</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('query-report', 'Reimbursement Payment Status'); return false;">报销付款状态</a>
                    </div>
                </div>

                <!-- 5. 🔒 系统底层与权限组 -->
                <div style="margin-bottom: 6px;">
                    <div class="ashan-sidebar-module" onclick="$(this).next('.sub-menu').slideToggle(120)">
                        <span>🔒 系统底层与权限组</span>
                        <span style="font-size: 10px; color: #718096;">▼</span>
                    </div>
                    <div class="sub-menu" style="display: none; padding-left: 12px; padding-top: 4px;">
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Restricted Access Group'); return false;">受限单据组</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Restricted Access Group Role'); return false;">组角色分配</a>
                        <a href="#" class="ashan-sidebar-link" onclick="frappe.set_route('List', 'Restricted Access Group User'); return false;">组人员分配</a>
                    </div>
                </div>
            </div>
            `;
            
            var bottomArea = sidebar.find('.body-sidebar-bottom');
            if (bottomArea.length) {
                bottomArea.before(treeHtml);
            } else {
                sidebar.append(treeHtml);
            }
        } else {
            // If it exists, ensure it is still positioned correctly just before .body-sidebar-bottom
            var bottomArea = sidebar.find('.body-sidebar-bottom');
            var menu = $('#ashan-left-tree');
            if (bottomArea.length && menu.next()[0] !== bottomArea[0]) {
                bottomArea.before(menu);
            }
        }
        
        applyOriginalVisibility();
    }

    window.ashanToggleOriginal = function(hide) {
        localStorage.setItem('ashan_hide_original', hide ? '1' : '0');
        // Update checkbox state if changed programmatically
        $('#ashan-toggle-original').prop('checked', hide);
        applyOriginalVisibility();
    };

    function applyOriginalVisibility() {
        var isHide = localStorage.getItem('ashan_hide_original') === '1';
        var styleId = 'ashan-hide-original-style';
        var styleEl = $('#' + styleId);
        
        var sidebar = $('.body-sidebar');
        var menu = $('#ashan-left-tree');
        
        if (isHide) {
            if (styleEl.length === 0) {
                $('head').append('<style id="' + styleId + '">\\
                    .sidebar-items > * { display: none !important; }\\
                </style>');
            }
            
            // Move menu to the top (just inside body-sidebar-top, before sidebar-items)
            var topArea = sidebar.find('.body-sidebar-top');
            if (topArea.length && menu.parent()[0] !== topArea[0]) {
                topArea.prepend(menu);
            }
        } else {
            styleEl.remove();
            
            // Move menu back to the bottom (before body-sidebar-bottom)
            var bottomArea = sidebar.find('.body-sidebar-bottom');
            if (bottomArea.length && menu.next()[0] !== bottomArea[0]) {
                bottomArea.before(menu);
            }
        }
    }

    renderAshanSidebar();
    setInterval(renderAshanSidebar, 800);
})();
"""

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
        print("[SUCCESS] Updated Custom HTML Block at BOTTOM with Toggle!")

if __name__ == '__main__':
    main()
