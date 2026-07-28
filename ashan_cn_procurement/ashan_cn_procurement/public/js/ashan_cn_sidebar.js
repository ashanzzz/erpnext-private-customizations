// Copyright (c) 2026, Ashan CN Procurement
// 全功能一二级级联侧边栏菜单 (Procurement, Stock, Accounting, Fuel & Compliance)

$(document).on('app_ready page-change', function () {
    init_ashan_cn_sidebar();
});

function init_ashan_cn_sidebar() {
    // 移除旧容器，实现响应式重绘与页面切换高亮更新
    $('#ashan-cn-sidebar-container').remove();

    const $sidebar = $('.workspace-sidebar .standard-sidebar-section, .body-sidebar .standard-sidebar-section').first();
    if (!$sidebar.length) {
        setTimeout(init_ashan_cn_sidebar, 400);
        return;
    }

    const current_path = window.location.pathname;

    const menu_tree = [
        {
            title: "🛒 采购管理",
            id: "menu-procurement",
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
            items: [
                { label: "受限访问分组", route: "/app/restricted-access-group" },
                { label: "车辆油耗参数配置", route: "/app/vehicle-fuel-settings" }
            ]
        }
    ];

    let html = `
    <div id="ashan-cn-sidebar-container" class="ashan-sidebar-wrapper" style="margin-top: 12px; border-top: 1px solid var(--border-color); padding-top: 8px;">
        <div class="sidebar-section-header" style="font-weight: 700; font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; padding: 0 12px; letter-spacing: 0.5px;">
            业务全能导航 (一二级级联)
        </div>
    `;

    menu_tree.forEach(group => {
        // 判断当前路由是否属于此分组
        const has_active = group.items.some(item => current_path.toLowerCase() === item.route.toLowerCase());
        const display_style = has_active ? 'block' : 'none';
        const arrow_icon = has_active ? '▼' : '▶';

        html += `
        <div class="ashan-menu-group" style="margin-bottom: 3px;">
            <div class="ashan-group-header" data-toggle="${group.id}" style="cursor: pointer; padding: 7px 12px; font-weight: 600; font-size: 13px; border-radius: var(--border-radius-sm, 6px); display: flex; justify-content: space-between; align-items: center; color: var(--text-color); transition: background-color 0.2s;">
                <span>${group.title}</span>
                <span class="ashan-icon" style="font-size: 9px; transition: transform 0.2s; color: var(--text-muted);">${arrow_icon}</span>
            </div>
            <div id="${group.id}" class="ashan-group-items" style="display: ${display_style}; padding-left: 8px; margin-top: 2px;">
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

        html += `
            </div>
        </div>
        `;
    });

    html += `</div>`;

    $sidebar.prepend(html);

    // 折叠展开点击绑定
    $('.ashan-group-header').off('click').on('click', function () {
        const targetId = $(this).attr('data-toggle');
        const $target = $('#' + targetId);
        const $icon = $(this).find('.ashan-icon');

        $target.slideToggle(150);
        if ($icon.text() === '▼') {
            $icon.text('▶');
        } else {
            $icon.text('▼');
        }
    });

    // Hover 视觉提升
    $('.ashan-menu-item, .ashan-group-header').hover(
        function() {
            if (!$(this).hasClass('active-route')) {
                $(this).css('background-color', 'var(--fg-hover-color)');
            }
        },
        function() {
            if (!$(this).attr('style').includes('border-left')) {
                $(this).css('background-color', 'transparent');
            }
        }
    );
}
