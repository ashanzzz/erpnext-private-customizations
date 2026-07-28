// Copyright (c) 2026, Ashan CN Procurement
// 全功能一二级级联侧边栏菜单 (支持不同用户个性化自定义标题与菜单)

$(document).on('app_ready page-change', function () {
    init_ashan_cn_sidebar();
});

function init_ashan_cn_sidebar() {
    $('#ashan-cn-sidebar-container').remove();

    const $sidebar = $('.workspace-sidebar .standard-sidebar-section, .body-sidebar .standard-sidebar-section').first();
    if (!$sidebar.length) {
        setTimeout(init_ashan_cn_sidebar, 400);
        return;
    }

    const current_user = (window.frappe && frappe.session && frappe.session.user) ? frappe.session.user : 'default';
    const storage_key = 'ashan_sidebar_title_' + current_user;
    
    // 获取当前登录用户自定义的标题，默认显示“我的业务”
    let custom_title = localStorage.getItem(storage_key) || '我的业务';

    const current_path = window.location.pathname;

    const menu_tree = [
        {
            title: "🏠 业务扩展总控主页",
            id: "menu-home-main",
            main_route: "/app/ashan-cn-procurement",
            items: []
        },
        {
            title: "🛒 采购管理",
            id: "menu-procurement",
            main_route: "/app/buying",
            items: [
                { label: "采购订单", route: "/app/purchase-order" },
                { label: "采购入库单", route: "/app/purchase-receipt" },
                { label: "供应商管理", route: "/app/supplier" },
                { label: "采购申请单", route: "/app/material-request" },
                { label: "采购分析对账表", route: "/app/query-report/Purchase%20Order%20Analysis" }
            ]
        },
        {
            title: "📦 仓库与库存",
            id: "menu-stock",
            main_route: "/app/stock",
            items: [
                { label: "物料主数据", route: "/app/item" },
                { label: "仓库管理", route: "/app/warehouse" },
                { label: "物料调拨与领用", route: "/app/stock-entry" },
                { label: "销售出库单", route: "/app/delivery-note" },
                { label: "库存台账明细", route: "/app/query-report/Stock%20Ledger" }
            ]
        },
        {
            title: "💳 会计与财务",
            id: "menu-accounting",
            main_route: "/app/invoicing",
            items: [
                { label: "应付发票", route: "/app/purchase-invoice" },
                { label: "应收发票", route: "/app/sales-invoice" },
                { label: "付款凭证", route: "/app/payment-entry" },
                { label: "费用报销申请 (扩展)", route: "/app/reimbursement-request" },
                { label: "报销发票明细 (扩展)", route: "/app/reimbursement-invoice-item" },
                { label: "未付报销清单", route: "/app/query-report/Unpaid%20Reimbursement%20List" },
                { label: "报销支付状态表", route: "/app/query-report/Reimbursement%20Payment%20Status" }
            ]
        },
        {
            title: "⛽ 车油能耗管理",
            id: "menu-fuel",
            main_route: "/app/vehicle-fuel-hub",
            items: [
                { label: "油卡台账", route: "/app/oil-card" },
                { label: "油卡充值记录", route: "/app/oil-card-recharge" },
                { label: "车辆加油日志", route: "/app/oil-card-refuel-log" },
                { label: "油卡开票批次", route: "/app/oil-card-invoice-batch" },
                { label: "车辆油耗汇总表", route: "/app/query-report/Vehicle%20Fuel%20Cost%20Summary" },
                { label: "油卡月度台账", route: "/app/query-report/Oil%20Card%20Monthly%20Ledger" }
            ]
        },
        {
            title: "🛡️ 企业合规中心",
            id: "menu-compliance",
            main_route: "/app/company-compliance-center",
            items: [
                { label: "环保合规项目", route: "/app/environmental-compliance-item" },
                { label: "合规设备清单", route: "/app/compliance-equipment-item" },
                { label: "员工证书管理", route: "/app/employee-certificate-item" },
                { label: "合规到期预警趋势", route: "/app/query-report/Compliance%20Expiry%20Trend" }
            ]
        },
        {
            title: "⚙️ 权限与系统配置",
            id: "menu-access",
            main_route: "/app/restricted-access-group",
            items: [
                { label: "受限访问分组", route: "/app/restricted-access-group" },
                { label: "车辆油耗参数配置", route: "/app/vehicle-fuel-settings" }
            ]
        }
    ];

    let html = `
    <div id="ashan-cn-sidebar-container" class="ashan-sidebar-wrapper" style="margin-top: 12px; border-top: 1px solid var(--border-color); padding-top: 8px;">
        <div class="sidebar-section-header" style="font-weight: 700; font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; padding: 0 12px; letter-spacing: 0.5px; display: flex; justify-content: space-between; align-items: center;">
            <span id="ashan-sidebar-custom-title-text">${custom_title}</span>
            <span id="ashan-edit-sidebar-title-btn" style="cursor: pointer; font-size: 11px; color: var(--text-muted);" title="点击自定义我的业务名称">✏️</span>
        </div>
    `;

    menu_tree.forEach(group => {
        const is_group_active = current_path.toLowerCase() === group.main_route.toLowerCase();
        const has_active_child = group.items.some(item => current_path.toLowerCase() === item.route.toLowerCase());
        const is_open = is_group_active || has_active_child;
        const display_style = is_open ? 'block' : 'none';
        const arrow_icon = is_open ? '▼' : '▶';

        const group_active_style = is_group_active
            ? 'background-color: var(--fg-hover-color); color: var(--primary-color, #2490ef); font-weight: 700;'
            : '';

        html += `
        <div class="ashan-menu-group" style="margin-bottom: 3px;">
            <div class="ashan-group-header" style="padding: 7px 12px; font-size: 13px; border-radius: var(--border-radius-sm, 6px); display: flex; justify-content: space-between; align-items: center; color: var(--text-color); transition: background-color 0.2s; ${group_active_style}">
                <a href="${group.main_route}" class="ashan-group-title-link" style="color: inherit; text-decoration: none; font-weight: inherit; flex-grow: 1;">
                    ${group.title}
                </a>
                ${group.items.length > 0 ? `<span class="ashan-toggle-btn" data-toggle="${group.id}" style="cursor: pointer; padding: 2px 6px; font-size: 9px; transition: transform 0.2s; color: var(--text-muted);">${arrow_icon}</span>` : ''}
            </div>
            ${group.items.length > 0 ? `
            <div id="${group.id}" class="ashan-group-items" style="display: ${display_style}; padding-left: 8px; margin-top: 2px;">
            ` : ''}
        `;

        group.items.forEach(item => {
            const is_active = current_path.toLowerCase() === item.route.toLowerCase();
            const active_style = is_active 
                ? 'background-color: var(--fg-hover-color); color: var(--primary-color, #2490ef); font-weight: 600; border-left: 3px solid var(--primary-color, #2490ef); padding-left: 11px;' 
                : 'color: var(--text-muted);';

            html += `
                <a href="${item.route}" class="ashan-menu-item" style="display: block; padding: 5px 12px; font-size: 12.5px; border-radius: var(--border-radius-sm, 4px); text-decoration: none; margin: 1px 0; transition: all 0.15s; ${active_style}">
                    • ${item.label}
                </a>
            `;
        });

        if (group.items.length > 0) {
            html += `</div>`;
        }

        html += `</div>`;
    });

    html += `</div>`;

    $sidebar.prepend(html);

    // 绑定左上角自定义编辑标题按钮
    $('#ashan-edit-sidebar-title-btn').off('click').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (window.frappe && frappe.prompt) {
            frappe.prompt({
                label: '自定义您的业务栏目名称',
                fieldname: 'custom_title',
                fieldtype: 'Data',
                default: custom_title
            }, (values) => {
                if (values.custom_title) {
                    const new_title = values.custom_title.trim();
                    localStorage.setItem(storage_key, new_title);
                    $('#ashan-sidebar-custom-title-text').text(new_title);
                    frappe.show_alert({ message: '侧边栏名称已成功个性化保存！', indicator: 'green' });
                }
            }, '个性化设置', '保存');
        } else {
            const new_title = prompt('自定义您的业务栏目名称:', custom_title);
            if (new_title) {
                localStorage.setItem(storage_key, new_title.trim());
                $('#ashan-sidebar-custom-title-text').text(new_title.trim());
            }
        }
    });

    // 绑定右侧箭头单独控制折叠/展开
    $('.ashan-toggle-btn').off('click').on('click', function (e) {
        e.stopPropagation();
        e.preventDefault();
        const targetId = $(this).attr('data-toggle');
        const $target = $('#' + targetId);
        const $icon = $(this);

        $target.slideToggle(150);
        if ($icon.text().trim() === '▼') {
            $icon.text('▶');
        } else {
            $icon.text('▼');
        }
    });

    // Hover 效果
    $('.ashan-menu-item, .ashan-group-header').hover(
        function() { $(this).css('background-color', 'var(--fg-hover-color)'); },
        function() {
            if (!$(this).attr('style').includes('border-left') && !$(this).find('.ashan-group-title-link').hasClass('active-link')) {
                $(this).css('background-color', 'transparent');
            }
        }
    );
}
