// Copyright (c) 2026, Ashan CN Procurement
// 左侧一二级级联菜单 (Two-Level Collapsible Sidebar) 前端增强脚本

$(document).on('app_ready page-change', function () {
    init_ashan_cn_sidebar();
});

function init_ashan_cn_sidebar() {
    // 限制在 Frappe Desk 页面下运行，避免重复初始化
    if ($('#ashan-cn-sidebar-container').length > 0) {
        return;
    }

    const $sidebar = $('.workspace-sidebar .standard-sidebar-section, .body-sidebar .standard-sidebar-section').first();
    if (!$sidebar.length) {
        // 如果侧边栏尚未加载完成，延迟重试
        setTimeout(init_ashan_cn_sidebar, 500);
        return;
    }

    const menu_tree = [
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
            title: "💰 费用与报销管理",
            id: "menu-reimbursement",
            items: [
                { label: "费用报销申请", route: "/app/reimbursement-request" },
                { label: "报销发票明细", route: "/app/reimbursement-invoice-item" },
                { label: "未付报销清单", route: "/app/query-report/Unpaid%20Reimbursement%20List" },
                { label: "报销支付状态表", route: "/app/query-report/Reimbursement%20Payment%20Status" }
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
    <div id="ashan-cn-sidebar-container" class="ashan-sidebar-wrapper" style="margin-top: 15px; border-top: 1px solid var(--border-color); padding-top: 10px;">
        <div class="sidebar-section-header" style="font-weight: 600; font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; padding: 0 12px;">
            业务扩展功能 (一二级菜单)
        </div>
    `;

    menu_tree.forEach(group => {
        html += `
        <div class="ashan-menu-group" style="margin-bottom: 4px;">
            <div class="ashan-group-header" data-toggle="${group.id}" style="cursor: pointer; padding: 6px 12px; font-weight: 500; font-size: 13px; border-radius: var(--border-radius); display: flex; justify-content: space-between; align-items: center; color: var(--text-color);">
                <span>${group.title}</span>
                <span class="ashan-icon" style="font-size: 10px; transition: transform 0.2s;">▼</span>
            </div>
            <div id="${group.id}" class="ashan-group-items" style="display: block; padding-left: 12px; margin-top: 2px;">
        `;
        group.items.forEach(item => {
            html += `
                <a href="${item.route}" class="ashan-menu-item" style="display: block; padding: 5px 12px; font-size: 12px; color: var(--text-muted); border-radius: var(--border-radius); text-decoration: none; margin: 1px 0;">
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

    // 绑定展开/折叠交互事件
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

    // 悬浮高亮效果
    $('.ashan-menu-item, .ashan-group-header').hover(
        function() { $(this).css('background-color', 'var(--fg-hover-color)'); },
        function() { $(this).css('background-color', 'transparent'); }
    );
}
