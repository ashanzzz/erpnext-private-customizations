/* ==========================================================================
   ERPNext 16 采购发票列表页定制 (Purchase Invoice List View)
   1. 渲染【开票物料明细】：将物料名称及数量渲染为清爽中文化胶囊徽章 (Badges)
   2. 保持纯净布局与快捷筛选支持
   ========================================================================== */

frappe.listview_settings['Purchase Invoice'] = {
    add_fields: ["custom_items_summary", "supplier", "bill_no", "bill_date", "grand_total", "status"],
    
    formatters: {
        custom_items_summary: function(value, df, doc) {
            if (!value) {
                return `<span style="color: #94a3b8; font-size: 12px;">-</span>`;
            }

            // 按顿号分隔并渲染为优雅胶囊标签
            const items = value.split("、");
            const badges = items.map(it => {
                const text = it.trim();
                if (text.includes("等共") || text.includes("项")) {
                    return `<span style="background: #eff6ff; color: #2563eb; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; display: inline-block; border: 1px solid #dbeafe;">${frappe.utils.escape_html(text)}</span>`;
                }
                return `<span style="background: #f8fafc; color: #334155; padding: 2px 6px; border-radius: 4px; font-size: 11.5px; font-weight: 500; margin-right: 4px; margin-bottom: 2px; display: inline-block; border: 1px solid #e2e8f0;">${frappe.utils.escape_html(text)}</span>`;
            }).join("");

            return `<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 2px;">${badges}</div>`;
        }
    }
};
