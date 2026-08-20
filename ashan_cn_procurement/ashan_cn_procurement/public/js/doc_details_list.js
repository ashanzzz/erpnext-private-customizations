/* ==========================================================================
   ERPNext 16 采购与财务全单据【单据明细】高颜值胶囊徽章渲染引擎 (Badges Engine)
   特性:
     1. 独立小卡片胶囊 (Badges)
     2. 单行整齐排列，绝对不折行撑高表格 (No-Wrap)
     3. 超出列宽自动省略并附带省略卡片 (···)
     4. 原生 Tooltip 悬浮完整预览 (Hover to view all)
   ========================================================================== */

frappe.provide("ashan.doc_details");

ashan.doc_details.render_badges = function (value) {
    if (!value || typeof value !== 'string' || value.trim() === '') {
        return `<span style="color: #94a3b8; font-size: 12px;">—</span>`;
    }

    const items = value.split(/[、;；]/).map(s => s.trim()).filter(s => s.length > 0);
    if (!items.length) {
        return `<span style="color: #94a3b8; font-size: 12px;">—</span>`;
    }

    const maxVisible = 2; // 最多显示前 2 个完整卡片，其余以省略胶囊显示，确保单行优雅不拥挤
    const visibleItems = items.slice(0, maxVisible);
    const hasMore = items.length > maxVisible;

    const badges = visibleItems.map(it => {
        if (it.includes("等共") || it.includes("项") || it.includes("张")) {
            return `<span style="display: inline-flex; align-items: center; flex-shrink: 0; background: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd; padding: 2px 7px; border-radius: 5px; font-size: 11.5px; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.03); white-space: nowrap;">${frappe.utils.escape_html(it)}</span>`;
        }

        // 分离品名与 (数量/金额)
        const match = it.match(/^(.*?)\s*(\(.*?\))$/);
        if (match) {
            const namePart = match[1].trim();
            const qtyPart = match[2].trim();
            return `<span style="display: inline-flex; align-items: center; flex-shrink: 0; background: #f8fafc; color: #1e293b; border: 1px solid #cbd5e1; padding: 2px 7px; border-radius: 5px; font-size: 11.5px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.03); white-space: nowrap;">
                <span style="color: #0f172a; font-weight: 500;">${frappe.utils.escape_html(namePart)}</span>
                <span style="color: #2563eb; font-weight: 600; margin-left: 4px; background: #eff6ff; padding: 1px 4px; border-radius: 3px; border: 1px solid #dbeafe;">${frappe.utils.escape_html(qtyPart)}</span>
            </span>`;
        }

        return `<span style="display: inline-flex; align-items: center; flex-shrink: 0; background: #f8fafc; color: #1e293b; border: 1px solid #cbd5e1; padding: 2px 7px; border-radius: 5px; font-size: 11.5px; font-weight: 500; box-shadow: 0 1px 2px rgba(0,0,0,0.03); white-space: nowrap;">${frappe.utils.escape_html(it)}</span>`;
    }).join("");

    let moreBadge = "";
    if (hasMore) {
        const remainingCount = items.length - maxVisible;
        moreBadge = `<span style="display: inline-flex; align-items: center; flex-shrink: 0; background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; padding: 2px 6px; border-radius: 5px; font-size: 11px; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.03); white-space: nowrap;" title="还有 ${remainingCount} 项：${frappe.utils.escape_html(items.slice(maxVisible).join('、'))}">+${remainingCount}···</span>`;
    }

    return `<div class="doc-details-badges-wrapper" style="display: flex; flex-wrap: nowrap; align-items: center; gap: 4px; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 1px 0;" title="${frappe.utils.escape_html(value)}">${badges}${moreBadge}</div>`;
};

// 全局对所有 DocType 的 listview_settings 注册统一 formatter
const targetDocTypes = [
    "Material Request",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice",
    "Reimbursement Request"
];

function register_doc_details_formatter(dt) {
    if (!frappe.listview_settings[dt]) {
        frappe.listview_settings[dt] = {};
    }
    if (!frappe.listview_settings[dt].formatters) {
        frappe.listview_settings[dt].formatters = {};
    }
    frappe.listview_settings[dt].formatters["custom_doc_details"] = function (val, df, doc) {
        return ashan.doc_details.render_badges(val || (doc && doc.custom_doc_details));
    };
    frappe.listview_settings[dt].formatters["custom_items_summary"] = function (val, df, doc) {
        return ashan.doc_details.render_badges(val || (doc && (doc.custom_doc_details || doc.custom_items_summary)));
    };
}

// 1. 初始化时注册
targetDocTypes.forEach(register_doc_details_formatter);

// 2. 页面切换时保证注册
$(document).on("page-change", function () {
    targetDocTypes.forEach(register_doc_details_formatter);
});

// 3. 动态 DOM 扫描替换器 (三重保障，确保所有列表列中呈现精致立体的单行小卡片徽章与省略号)
setInterval(function () {
    const cur_route = frappe.get_route();
    if (cur_route && cur_route[0] === 'List') {
        const dt = cur_route[1];
        if (targetDocTypes.includes(dt)) {
            register_doc_details_formatter(dt);
            $('.list-row-col[data-fieldname="custom_doc_details"], .list-row-col[data-fieldname="custom_items_summary"]').each(function () {
                const $col = $(this);
                if ($col.find('.doc-details-badges-wrapper').length > 0) return;
                const rawText = $col.text().trim();
                if (rawText && rawText !== '—' && rawText !== '-' && !rawText.includes('单据明细') && !rawText.includes('开票物料明细')) {
                    $col.html(ashan.doc_details.render_badges(rawText));
                }
            });
        }
    }
}, 250);
