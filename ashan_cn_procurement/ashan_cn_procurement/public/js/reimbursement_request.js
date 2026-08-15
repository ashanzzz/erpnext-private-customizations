// Copyright (c) 2026, Ashan CN Procurement and contributors
// For license information, please see license.txt

(function () {
    "use strict";

    const IMPORT_METHOD = "ashan_cn_procurement.reimbursement.api.import_unpaid_purchase_invoices";
    const PREVIEW_METHOD = "ashan_cn_procurement.reimbursement.api.preview_unpaid_purchase_invoice_items";
    const FILTER_OPTIONS_METHOD = "ashan_cn_procurement.reimbursement.api.get_unpaid_purchase_invoice_filter_options";
    const PICKER_ROWS_METHOD = "ashan_cn_procurement.reimbursement.api.get_unpaid_purchase_invoice_picker_rows";

    frappe.ui.form.on("Reimbursement Request", {
        refresh(frm) {
            add_unpaid_invoice_action(frm);
        },
    });

    // app_include_js may finish loading after a directly-opened Form has
    // already emitted refresh. Reapply on route changes so the action does not
    // disappear on a new reimbursement request or after Desk navigation.
    frappe.router.on("change", () => {
        window.setTimeout(() => add_unpaid_invoice_action(window.cur_frm), 150);
    });

    function add_unpaid_invoice_action(frm) {
        if (!frm || frm.doctype !== "Reimbursement Request" || !frm.page) return;
        frm.page.set_secondary_action(__("获取未付款发票"), () => open_unpaid_invoice_picker(frm));
    }

    function open_unpaid_invoice_picker(frm) {
        if (!frm.doc.company) {
            frappe.msgprint(__("请先填写公司。"));
            return;
        }
        frappe.call({
            method: FILTER_OPTIONS_METHOD,
            args: { company: frm.doc.company },
            callback(response) {
                show_unpaid_invoice_picker(frm, (response.message || {}).invoice_types || []);
            },
        });
    }

    function show_unpaid_invoice_picker(frm, invoiceTypes) {
        const selectedInvoices = new Map();
        let rows = [];
        let refreshTimer;
        let latestRequest = 0;
        const invoiceTypeOptions = ["<option value=\"\">全部类型</option>"]
            .concat(invoiceTypes.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`))
            .join("");
        const html = `
            <style>
                .rr-picker-modal .modal-dialog { width: 92vw; max-width: 1460px; }
                .rr-picker-modal .modal-body { max-height: calc(100vh - 170px); overflow: hidden; }
                .rr-picker-filters { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 10px; align-items: end; }
                .rr-picker-filters label { color: var(--text-muted); font-size: 12px; margin-bottom: 4px; }
                .rr-picker-toolbar { display: flex; align-items: center; gap: 8px; margin: 12px 0 8px; }
                .rr-picker-status { color: var(--text-muted); font-size: 12px; flex: 1; }
                .rr-picker-scroll { max-height: 480px; overflow: auto; border: 1px solid var(--border-color); border-radius: var(--border-radius-md); }
                .rr-picker-table { width: 100%; border-collapse: collapse; font-size: 12px; }
                .rr-picker-table th, .rr-picker-table td { padding: 9px 8px; border-bottom: 1px solid var(--border-color); vertical-align: top; }
                .rr-picker-table th { position: sticky; top: 0; z-index: 1; background: var(--fg-color); color: var(--text-muted); font-weight: 600; white-space: nowrap; }
                .rr-picker-table tr:hover { background: var(--subtle-fg); }
                .rr-picker-item-summary { color: var(--text-muted); line-height: 1.45; }
                .rr-picker-amount { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
                .rr-picker-summary { margin-top: 10px; padding: 10px 12px; background: var(--subtle-fg); border-radius: var(--border-radius-md); text-align: right; }
                .rr-picker-empty { color: var(--text-muted); padding: 28px; text-align: center; }
                @media (max-width: 900px) { .rr-picker-filters { grid-template-columns: repeat(2, minmax(150px, 1fr)); } }
            </style>
            <div class="rr-picker-filters">
                <div><label>发票号</label><input class="form-control rr-picker-filter" data-filter="bill_no" placeholder="包含匹配"></div>
                <div><label>发票日期（起）</label><input type="date" class="form-control rr-picker-filter" data-filter="bill_date_from"></div>
                <div><label>发票日期（止）</label><input type="date" class="form-control rr-picker-filter" data-filter="bill_date_to"></div>
                <div><label>发票类型</label><select class="form-control rr-picker-filter" data-filter="custom_invoice_type">${invoiceTypeOptions}</select></div>
                <div><label>供应商</label><input class="form-control rr-picker-filter" data-filter="supplier" placeholder="包含匹配"></div>
                <div><label>物料名</label><input class="form-control rr-picker-filter" data-filter="item_name" placeholder="包含匹配"></div>
                <div><label>待付金额（最小）</label><input type="number" min="0" step="0.01" class="form-control rr-picker-filter" data-filter="min_outstanding_amount"></div>
                <div><label>待付金额（最大）</label><input type="number" min="0" step="0.01" class="form-control rr-picker-filter" data-filter="max_outstanding_amount"></div>
            </div>
            <div class="rr-picker-toolbar">
                <span class="rr-picker-status">正在加载未付款采购发票…</span>
                <button type="button" class="btn btn-default btn-sm rr-picker-refresh">刷新</button>
                <button type="button" class="btn btn-default btn-sm rr-picker-select-page">全选当前结果</button>
                <button type="button" class="btn btn-default btn-sm rr-picker-clear">清空选择</button>
            </div>
            <div class="rr-picker-scroll"><table class="rr-picker-table"><thead><tr>
                <th style="width:42px"><input type="checkbox" class="rr-picker-select-all" title="全选当前结果"></th>
                <th>发票号</th><th>发票日期</th><th>发票类型</th><th>供应商</th><th>包含物料</th><th class="rr-picker-amount">待付金额</th>
            </tr></thead><tbody class="rr-picker-body"></tbody></table></div>
            <div class="rr-picker-summary">已选 <strong class="rr-picker-count">0</strong> 张，待付合计 <strong class="rr-picker-total">${format_currency(0)}</strong></div>
        `;
        const dialog = new frappe.ui.Dialog({
            title: __("选择未付款采购发票"),
            size: "extra-large",
            fields: [{ fieldtype: "HTML", fieldname: "picker", options: html }],
            primary_action_label: __("确认添加"),
            primary_action() {
                import_selected_invoices(frm, [...selectedInvoices.keys()], dialog);
            },
        });
        dialog.show();
        dialog.$wrapper.addClass("rr-picker-modal");
        const $root = dialog.$wrapper;

        $root.on("input change", ".rr-picker-filter", () => {
            window.clearTimeout(refreshTimer);
            refreshTimer = window.setTimeout(refresh_rows, 250);
        });
        $root.on("click", ".rr-picker-refresh", refresh_rows);
        $root.on("click", ".rr-picker-select-page", () => {
            rows.forEach((row) => selectedInvoices.set(row.name, Number(row.outstanding_amount) || 0));
            render_rows();
        });
        $root.on("click", ".rr-picker-clear", () => {
            selectedInvoices.clear();
            render_rows();
        });
        $root.on("change", ".rr-picker-select-all", function () {
            if (this.checked) rows.forEach((row) => selectedInvoices.set(row.name, Number(row.outstanding_amount) || 0));
            else rows.forEach((row) => selectedInvoices.delete(row.name));
            render_rows();
        });
        $root.on("change", ".rr-picker-row-check", function () {
            const $check = $(this);
            if (this.checked) selectedInvoices.set($check.data("name"), Number($check.data("amount")) || 0);
            else selectedInvoices.delete($check.data("name"));
            render_summary();
        });

        function get_filters() {
            const filters = {};
            $root.find(".rr-picker-filter").each(function () {
                filters[$(this).data("filter")] = $(this).val();
            });
            return filters;
        }

        function refresh_rows() {
            const requestNumber = ++latestRequest;
            $root.find(".rr-picker-status").text(__("正在筛选…"));
            frappe.call({
                method: PICKER_ROWS_METHOD,
                args: { company: frm.doc.company, filters: get_filters() },
                callback(response) {
                    if (requestNumber !== latestRequest) return;
                    rows = (response.message || {}).rows || [];
                    $root.find(".rr-picker-status").text(__("共 {0} 张未付款发票", [rows.length]));
                    render_rows();
                },
                error() {
                    if (requestNumber === latestRequest) $root.find(".rr-picker-status").text(__("加载失败，请刷新后重试。"));
                },
            });
        }

        function render_rows() {
            const content = rows.length ? rows.map((row) => `
                <tr><td><input type="checkbox" class="rr-picker-row-check" data-name="${escapeHtml(row.name)}" data-amount="${Number(row.outstanding_amount) || 0}" ${selectedInvoices.has(row.name) ? "checked" : ""}></td>
                <td>${escapeHtml(row.bill_no || row.name)}</td><td>${escapeHtml(row.bill_date || "")}</td><td>${escapeHtml(row.custom_invoice_type || "")}</td>
                <td>${escapeHtml(row.supplier || "")}</td><td class="rr-picker-item-summary">${escapeHtml(row.item_summary || "—")}</td>
                <td class="rr-picker-amount">${format_currency(row.outstanding_amount || 0)}</td></tr>`).join("") :
                `<tr><td colspan="7" class="rr-picker-empty">没有符合条件的未付款采购发票。</td></tr>`;
            $root.find(".rr-picker-body").html(content);
            $root.find(".rr-picker-select-all").prop("checked", rows.length && rows.every((row) => selectedInvoices.has(row.name)));
            render_summary();
        }

        function render_summary() {
            const amount = [...selectedInvoices.values()].reduce((total, value) => total + value, 0);
            $root.find(".rr-picker-count").text(selectedInvoices.size);
            $root.find(".rr-picker-total").text(format_currency(amount));
        }

        refresh_rows();
    }

    function import_selected_invoices(frm, invoiceNames, dialog) {
        if (!invoiceNames.length) {
            frappe.show_alert({ message: __("请选择至少一张采购发票。"), indicator: "orange" }, 4);
            return;
        }
        const isNew = frm.is_new();
        frappe.call({
            method: isNew ? PREVIEW_METHOD : IMPORT_METHOD,
            args: {
                ...(isNew ? { company: frm.doc.company } : { reimbursement_request_name: frm.doc.name }),
                purchase_invoice_names: invoiceNames,
            },
            freeze: true,
            freeze_message: __("正在核验并导入来源发票明细…"),
            callback(response) {
                const result = response.message || {};
                if (isNew) {
                    (result.items || []).forEach((item) => frm.add_child("invoice_items", item));
                    frm.refresh_field("invoice_items");
                } else {
                    frm.reload_doc();
                }
                dialog.hide();
                frappe.show_alert({
                    message: __("已导入 {0} 行，可报销合计 {1}", [result.imported_count || 0, format_currency(result.imported_amount || 0)]),
                    indicator: "green",
                }, 6);
            },
        });
    }

    function escapeHtml(value) {
        return $("<div>").text(value == null ? "" : String(value)).html();
    }
})();
