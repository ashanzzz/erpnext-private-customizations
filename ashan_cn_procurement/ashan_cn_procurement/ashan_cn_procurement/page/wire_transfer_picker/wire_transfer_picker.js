// Copyright (c) 2026, Ashan CN Procurement and contributors
// For license information, please see license.txt

frappe.pages["wire-transfer-picker"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("自办电汇选单生单中心"),
        single_column: true,
    });

    $(page.wrapper).find(".page-head").hide();
    wrapper.wire_transfer_picker = new WireTransferPicker(page);
};

class WireTransferPicker {
    constructor(page) {
        this.page = page;
        this.companies = [];
        this.active_company = "All";
        this.locked_company = null;
        this.view_mode = "detail"; // "detail" | "doc"
        this.filters = {
            match_status: "pending",
            supplier: "",
            bill_no: "",
            item_code: "",
            owner: "",
        };

        this.kpis = {};
        this.table_data = [];
        this.selected_map = new Map();

        this.init();
    }

    async init() {
        this.setup_ui_skeleton();
        await this.load_companies();
        this.bind_global_events();
        this.refresh_all();
    }

    setup_ui_skeleton() {
        const html = `
            <div class="picker-page-container">
                <!-- Top Header & Company Dropdown -->
                <div class="picker-top-bar">
                    <div class="picker-title-group">
                        <h2>⚡ 采购全流程选单生单中心</h2>
                        <div class="picker-subtitle">自办电汇</div>
                    </div>
                    <div class="picker-company-group">
                        <label class="picker-company-label" for="wire-company-select">所属公司:</label>
                        <select class="picker-company-select" id="wire-company-select">
                            <option value="All">🌐 全部公司 (汇聚视图)</option>
                        </select>
                    </div>
                </div>

                <!-- 4-Step KPI Cards Grid -->
                <div class="picker-kpi-grid" id="wire-kpi-grid"></div>

                <!-- Section Context Banner -->
                <div class="picker-section-banner" id="wire-section-banner">
                    <div class="picker-section-main">
                        <div class="picker-section-icon">⚡</div>
                        <div class="picker-section-heading">
                            <div class="picker-section-title">
                                <span>自办电汇 · 极速录单与自动闭环生单中心</span>
                            </div>
                            <div class="picker-section-desc">录入自办电汇发票，系统自动闭环生成采购订单 (PO) ➔ 采购入库单 (PR) ➔ 采购发票 (PI) ➔ 电汇付款申请 (RR)。</div>
                        </div>
                    </div>
                    <div class="picker-section-badge" id="wire-section-count-badge">
                        统计: 0 笔
                    </div>
                </div>

                <!-- Dynamic Filter Bar -->
                <div class="picker-filter-bar" id="wire-filter-bar">
                    <div class="picker-filter-group">
                        <label>付款状态:</label>
                        <div class="picker-status-btn-group" data-filter="match_status">
                            <button type="button" class="picker-status-btn active" data-value="pending">🟡 仅待电汇付款</button>
                            <button type="button" class="picker-status-btn" data-value="completed">🟢 仅已电汇付款</button>
                            <button type="button" class="picker-status-btn" data-value="all">🌐 全部发票单据</button>
                        </div>
                    </div>
                    <div class="picker-filter-group">
                        <label>供应商:</label>
                        <input type="text" class="picker-input" data-filter="supplier" placeholder="搜索供应商..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>发票号码:</label>
                        <input type="text" class="picker-input" data-filter="bill_no" placeholder="发票代码/号码..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>物料编码/名称:</label>
                        <input type="text" class="picker-input" data-filter="item_code" placeholder="物料代码/名称..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>经手人:</label>
                        <input type="text" class="picker-input" data-filter="owner" placeholder="录单人..." />
                    </div>
                </div>

                <!-- Action Bar (View Switcher + Selection Summary + Primary Actions) -->
                <div class="picker-action-bar">
                    <div class="picker-summary-text">
                        <div class="picker-view-switch-group">
                            <button type="button" class="picker-view-btn active" data-mode="detail">📑 明细视图</button>
                            <button type="button" class="picker-view-btn" data-mode="doc">📦 单号视图</button>
                        </div>
                        <span>已选 <strong class="picker-summary-highlight" id="wire-selected-count">0</strong> 项</span>
                        <span>本次总计: <strong class="picker-summary-highlight" id="wire-selected-amount">¥ 0.00</strong></span>
                    </div>
                    <div class="picker-btn-group">
                        <button type="button" class="picker-btn-sub" id="wire-select-all-btn">全选本页</button>
                        <button type="button" class="picker-btn-sub" id="wire-clear-sel-btn">清空选择</button>
                        <button type="button" class="picker-btn-create-wire" id="wire-open-create-modal-btn">⚡ + 新建自办电汇发票</button>
                    </div>
                </div>

                <!-- Big Wide Data Table Container -->
                <div class="picker-table-wrapper">
                    <!-- Top Sync Scrollbar -->
                    <div class="picker-top-scrollbar-wrap" id="wire-top-scrollbar">
                        <div class="picker-top-scrollbar-inner" id="wire-top-scrollbar-inner"></div>
                    </div>

                    <!-- Main Table Scroll Area -->
                    <div class="picker-main-table-scroll" id="wire-main-table-scroll">
                        <table class="picker-data-table" id="wire-data-table">
                            <thead id="wire-table-thead"></thead>
                            <tbody id="wire-table-tbody"></tbody>
                            <tfoot id="wire-table-tfoot"></tfoot>
                        </table>
                    </div>
                </div>
            </div>
        `;
        $(this.page.body).html(html);
    }

    async load_companies() {
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.get_user_procurement_companies",
            });
            if (r.message && r.message.companies) {
                const comp_names = r.message.companies;
                this.companies = comp_names.map((name) => ({ name, company_name: name }));
                const $select = $("#wire-company-select");
                $select.empty();
                if (this.companies.length > 1) {
                    $select.append(`<option value="All">🌐 全部公司 (汇聚视图)</option>`);
                }
                this.companies.forEach((c) => {
                    $select.append(`<option value="${c.name}">${frappe.utils.escape_html(c.company_name || c.name)}</option>`);
                });
                this.active_company = this.companies.length === 1 ? this.companies[0].name : "All";
                $select.val(this.active_company);
            }
        } catch (e) {
            console.error("Failed to load companies for wire transfer picker:", e);
        }
    }

    bind_global_events() {
        const self = this;

        // Company Change
        $(this.page.body).on("change", "#wire-company-select", function () {
            self.active_company = $(this).val();
            self.locked_company = null;
            self.selected_map.clear();
            self.refresh_all();
        });

        // Filter Inputs
        $(this.page.body).on("input change", ".picker-input", function () {
            const field = $(this).attr("data-filter");
            const val = $(this).val().trim();
            if (field) {
                self.filters[field] = val;
                self.selected_map.clear();
                self.load_table_data();
            }
        });

        // Filter Status Buttons
        $(this.page.body).on("click", ".picker-status-btn", function () {
            const val = $(this).attr("data-value");
            $(this).siblings().removeClass("active");
            $(this).addClass("active");
            self.filters.match_status = val;
            self.selected_map.clear();
            self.load_table_data();
        });

        // View Mode Switcher
        $(this.page.body).on("click", ".picker-view-btn", function () {
            const mode = $(this).attr("data-mode");
            if (mode && self.view_mode !== mode) {
                self.view_mode = mode;
                $(".picker-view-btn").removeClass("active");
                $(this).addClass("active");
                self.selected_map.clear();
                self.load_table_data();
            }
        });

        // Open Create Modal Button
        $(this.page.body).on("click", "#wire-open-create-modal-btn", function () {
            self.open_create_wire_transfer_modal();
        });

        // Dual Scrollbar Sync
        const $top_scroll = $("#wire-top-scrollbar");
        const $table_scroll = $("#wire-main-table-scroll");
        let is_syncing_top = false;
        let is_syncing_main = false;

        $top_scroll.on("scroll", function () {
            if (!is_syncing_top) {
                is_syncing_main = true;
                $table_scroll.scrollLeft($(this).scrollLeft());
            }
            is_syncing_top = false;
        });

        $table_scroll.on("scroll", function () {
            if (!is_syncing_main) {
                is_syncing_top = true;
                $top_scroll.scrollLeft($(this).scrollLeft());
            }
            is_syncing_main = false;
        });

        // Mousewheel-to-Horizontal Scroll
        const handle_wheel_to_horizontal = function (e) {
            const raw_e = e.originalEvent || e;
            const delta_y = raw_e.deltaY;
            const delta_x = raw_e.deltaX;
            if (Math.abs(delta_y) > Math.abs(delta_x) && delta_y !== 0) {
                const el = $table_scroll[0];
                if (el && el.scrollWidth > el.clientWidth) {
                    el.scrollLeft += delta_y;
                    e.preventDefault();
                }
            }
        };

        $table_scroll.on("wheel", handle_wheel_to_horizontal);
        $top_scroll.on("wheel", handle_wheel_to_horizontal);
        $(this.page.body).on("wheel", "#wire-table-thead, #wire-top-scrollbar, #wire-main-table-scroll", handle_wheel_to_horizontal);

        // Row Checkbox Click
        $(this.page.body).on("change", ".picker-row-checkbox", function () {
            const key = $(this).attr("data-key");
            const is_checked = $(this).is(":checked");
            const row = self.table_data.find((r) => self.get_row_key(r) === key);
            if (!row) return;

            if (is_checked) {
                if (self.active_company === "All" && !self.locked_company) {
                    self.locked_company = row.company;
                }
                if (self.locked_company && row.company !== self.locked_company) {
                    $(this).prop("checked", false);
                    return;
                }
                self.selected_map.set(key, row);
                $(this).closest("tr").addClass("row-selected");
            } else {
                self.selected_map.delete(key);
                $(this).closest("tr").removeClass("row-selected");
                if (self.selected_map.size === 0) {
                    self.locked_company = null;
                }
            }
            self.update_action_summary();
        });

        // Select All / Clear Selection
        $(this.page.body).on("change", "#wire-select-all-header", function () {
            if ($(this).is(":checked")) {
                self.select_all_visible();
            } else {
                self.clear_selection();
            }
        });
        $(this.page.body).on("click", "#wire-select-all-btn", () => this.select_all_visible());
        $(this.page.body).on("click", "#wire-clear-sel-btn", () => this.clear_selection());

        // Click on doc link to open Detail Modal
        $(this.page.body).on("click", ".picker-doc-clickable-link", function (e) {
            e.preventDefault();
            e.stopPropagation();
            const dt = $(this).attr("data-doctype");
            const nm = $(this).attr("data-name");
            if (dt && nm) {
                self.show_doc_detail_modal(dt, nm);
            }
        });
    }

    async refresh_all() {
        await this.load_kpis();
        this.render_kpis();
        await this.load_table_data();
    }

    async load_kpis() {
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.wire_transfer_service.get_wire_transfer_overview_kpis",
                args: { company: this.active_company },
            });
            if (r.message && r.message.kpis) {
                this.kpis = r.message.kpis;
            }
        } catch (e) {
            console.error("Failed to load wire transfer KPIs:", e);
        }
    }

    render_kpis() {
        const $container = $("#wire-kpi-grid");
        $container.empty();

        const cards = [
            { id: "invoice", name: "自办发票", icon: "🧾", count: this.kpis.invoice?.count || 0, sub: "待开票/录入" },
            { id: "order", name: "采购订单", icon: "🛒", count: this.kpis.order?.count || 0, sub: "自办订单" },
            { id: "receipt", name: "采购入库", icon: "📦", count: this.kpis.receipt?.count || 0, sub: "自动入库" },
            { id: "payment", name: "电汇付款", icon: "💰", count: this.kpis.payment?.count || 0, sub: "待电汇付款" },
        ];

        cards.forEach((c) => {
            const html = `
                <div class="picker-kpi-card" data-card="${c.id}">
                    <div class="picker-kpi-header">
                        <div class="picker-kpi-title">${c.name}</div>
                        <div class="picker-kpi-icon">${c.icon}</div>
                    </div>
                    <div class="picker-kpi-body">
                        <div class="picker-kpi-number">${c.count}</div>
                        <div class="picker-kpi-sub">${c.sub}</div>
                    </div>
                </div>
            `;
            $container.append(html);
        });
    }

    async load_table_data() {
        const method = this.view_mode === "doc"
            ? "ashan_cn_procurement.services.wire_transfer_service.get_wire_transfer_doc_summary_rows"
            : "ashan_cn_procurement.services.wire_transfer_service.get_wire_transfer_picker_rows";

        try {
            const r = await frappe.call({
                method: method,
                args: {
                    company: this.active_company,
                    filters: this.filters,
                },
            });
            this.table_data = (r.message && r.message.rows) ? r.message.rows : [];
            $("#wire-section-count-badge").text(`统计: ${this.table_data.length} 笔`);
            this.render_table();
        } catch (e) {
            console.error("Failed to load wire transfer table data:", e);
        }
    }

    get_row_key(r) {
        return this.view_mode === "doc" ? r.pi_name : (r.pii_name || `${r.pi_name}_${r.item_code}`);
    }

    render_table() {
        this.render_table_header();
        this.render_table_rows();
        this.render_table_footer();
        this.update_action_summary();
        this.sync_top_scrollbar_width();
    }

    render_table_header() {
        const is_all = this.active_company === "All";
        let ths = `
            <th class="picker-col-sticky-1">#</th>
            <th class="picker-col-sticky-2">
                <input type="checkbox" id="wire-select-all-header" title="全选/取消全选" />
            </th>
        `;
        if (is_all) {
            ths += `<th class="picker-col-sticky-3">所属公司</th>`;
        }

        if (this.view_mode === "doc") {
            ths += `
                <th>采购发票号</th>
                <th>供应商</th>
                <th>发票代码/号码</th>
                <th>票据类型</th>
                <th>单据明细</th>
                <th>开票日期</th>
                <th>录单人</th>
                <th>发票总额</th>
                <th>待报销余额</th>
                <th>关联订单</th>
                <th>关联入库单</th>
                <th>🔗 关联报销单</th>
            `;
        } else {
            ths += `
                <th>采购发票号</th>
                <th>供应商</th>
                <th>发票代码/号码</th>
                <th>物料代码/名称</th>
                <th>单位</th>
                <th>数量</th>
                <th>单价</th>
                <th>明细金额</th>
                <th>税率</th>
                <th>税额</th>
                <th>价税合计</th>
                <th>开票日期</th>
                <th>待报销余额</th>
                <th>🔗 关联报销单</th>
            `;
        }

        $("#wire-table-thead").html(`<tr>${ths}</tr>`);
    }

    render_table_rows() {
        const $tbody = $("#wire-table-tbody");
        $tbody.empty();

        if (!this.table_data || this.table_data.length === 0) {
            const col_span = this.view_mode === "doc" ? 15 : 17;
            $tbody.html(`
                <tr>
                    <td colspan="${col_span}">
                        <div class="picker-empty-state">
                            <div class="picker-empty-icon">⚡</div>
                            <div class="picker-empty-text">当前暂无自办电汇单据记录，点击上方【⚡ + 新建自办电汇发票】即可极速录单！</div>
                        </div>
                    </td>
                </tr>
            `);
            return;
        }

        const is_all = this.active_company === "All";

        this.table_data.forEach((r, idx) => {
            const key = this.get_row_key(r);
            const is_selected = this.selected_map.has(key);

            let tr_html = `
                <tr data-key="${key}" class="${is_selected ? 'row-selected' : ''}">
                    <td class="picker-col-sticky-1">${idx + 1}</td>
                    <td class="picker-col-sticky-2">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${key}" ${is_selected ? 'checked' : ''} />
                    </td>
            `;

            if (is_all) {
                tr_html += `<td class="picker-col-sticky-3"><span class="ashan-tag-badge">${frappe.utils.escape_html(r.company || "")}</span></td>`;
            }

            if (this.view_mode === "doc") {
                const inv_type_badge = r.invoice_type === "专用发票"
                    ? `<span class="ashan-status-badge ashan-status-purple">专用发票</span>`
                    : `<span class="ashan-status-badge ashan-status-blue">普通发票</span>`;
                tr_html += `
                    <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Invoice" data-name="${r.pi_name}">${frappe.utils.escape_html(r.pi_name)}</span></td>
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                    <td><span class="ashan-tag-badge ashan-tag-blue">${frappe.utils.escape_html(r.bill_no || "未填")}</span></td>
                    <td>${inv_type_badge}</td>
                    <td>${this.render_doc_badges(r.custom_doc_details)}</td>
                    <td>${r.bill_date || r.posting_date || "-"}</td>
                    <td>${frappe.utils.escape_html(r.owner || "-")}</td>
                    <td class="picker-money-cell">${this.fmt_money(r.grand_total)}</td>
                    <td class="picker-money-cell cell-row-amt"><strong>${this.fmt_money(r.net_available_amount)}</strong></td>
                    <td>${this.render_linked_badges(r.linked_po_names, "purchase-order")}</td>
                    <td>${this.render_linked_badges(r.linked_pr_names, "purchase-receipt")}</td>
                    <td>${this.render_linked_badges(r.linked_rr_names, "reimbursement-request")}</td>
                `;
            } else {
                tr_html += `
                    <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Invoice" data-name="${r.pi_name}">${frappe.utils.escape_html(r.pi_name)}</span></td>
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                    <td><span class="ashan-tag-badge ashan-tag-blue">${frappe.utils.escape_html(r.bill_no || "未填")}</span></td>
                    <td><span class="ashan-tag-badge">${frappe.utils.escape_html(r.item_code)}</span> ${frappe.utils.escape_html(r.item_name || "")}</td>
                    <td>${frappe.utils.escape_html(r.uom || "")}</td>
                    <td class="picker-qty-cell">${r.qty}</td>
                    <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                    <td class="picker-money-cell">${this.fmt_money(r.amount)}</td>
                    <td>${flt(r.tax_rate)}%</td>
                    <td class="picker-money-cell">${this.fmt_money(r.tax_amount)}</td>
                    <td class="picker-money-cell">${this.fmt_money(r.total_amount)}</td>
                    <td>${r.bill_date || r.posting_date || "-"}</td>
                    <td class="picker-money-cell cell-row-amt"><strong>${this.fmt_money(r.net_available_amount)}</strong></td>
                    <td>${this.render_linked_badges(r.linked_rr_names, "reimbursement-request")}</td>
                `;
            }

            tr_html += `</tr>`;
            $tbody.append(tr_html);
        });
    }

    render_table_footer() {
        const is_all = this.active_company === "All";
        let total_qty = 0;
        let total_amt = 0;
        let total_tax = 0;
        let total_grand = 0;

        this.table_data.forEach((r) => {
            total_qty += flt(r.qty || r.total_qty || 0);
            total_amt += flt(r.amount || r.grand_total || 0);
            total_tax += flt(r.tax_amount || 0);
            total_grand += flt(r.total_amount || r.grand_total || 0);
        });

        const prefix_cols = is_all ? 3 : 2;
        let foot_html = `
            <tr>
                <td colspan="${prefix_cols}" class="picker-col-sticky-foot">合计 (共 ${this.table_data.length} 笔)</td>
        `;

        if (this.view_mode === "doc") {
            foot_html += `
                <td colspan="5"></td>
                <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                <td colspan="3"></td>
            `;
        } else {
            foot_html += `
                <td colspan="3"></td>
                <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                <td></td>
                <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                <td></td>
                <td class="picker-money-cell">${this.fmt_money(total_tax)}</td>
                <td class="picker-money-cell">${this.fmt_money(total_grand)}</td>
                <td></td>
                <td class="picker-money-cell">${this.fmt_money(total_grand)}</td>
                <td></td>
            `;
        }

        foot_html += `</tr>`;
        $("#wire-table-tfoot").html(foot_html);
    }

    update_action_summary() {
        const count = this.selected_map.size;
        let total_amt = 0;
        this.selected_map.forEach((r) => {
            total_amt += flt(r.net_available_amount || r.total_amount || r.grand_total || 0);
        });

        $("#wire-selected-count").text(count);
        $("#wire-selected-amount").text(this.fmt_money(total_amt));
    }

    select_all_visible() {
        this.selected_map.clear();
        this.table_data.forEach((r) => {
            const key = this.get_row_key(r);
            this.selected_map.set(key, r);
        });
        $(".picker-row-checkbox").prop("checked", true);
        $("#wire-table-tbody tr").addClass("row-selected");
        this.update_action_summary();
    }

    clear_selection() {
        this.selected_map.clear();
        this.locked_company = null;
        $(".picker-row-checkbox").prop("checked", false);
        $("#wire-table-tbody tr").removeClass("row-selected");
        $("#wire-select-all-header").prop("checked", false);
        this.update_action_summary();
    }

    sync_top_scrollbar_width() {
        const table_width = $("#wire-data-table").outerWidth() || 1200;
        $("#wire-top-scrollbar-inner").css("width", `${table_width}px`);
    }

    fmt_money(val) {
        return (window.AshanUI && AshanUI.formatMoney) ? AshanUI.formatMoney(val) : `¥ ${flt(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    render_doc_badges(doc_details_str) {
        if (!doc_details_str) return "-";
        const items = doc_details_str.split("、").map((s) => s.trim()).filter(Boolean);
        if (!items.length) return "-";
        return items.map((it) => {
            const match = it.match(/^(.+?)\s*\((.+?)\)$/);
            if (match) {
                return `<span class="ashan-doc-detail-badge"><span class="badge-item-name">${frappe.utils.escape_html(match[1])}</span><span class="badge-item-qty">${frappe.utils.escape_html(match[2])}</span></span>`;
            }
            return `<span class="ashan-doc-detail-badge">${frappe.utils.escape_html(it)}</span>`;
        }).join(" ");
    }

    render_linked_badges(linked_str, doctype_class) {
        if (!linked_str) return `<span class="picker-linked-none">-</span>`;
        const names = linked_str.split("、").map((s) => s.trim()).filter(Boolean);
        if (!names.length) return `<span class="picker-linked-none">-</span>`;
        return `<div class="picker-linked-wrap">${names.map((nm) => `<span class="picker-linked-badge badge-${doctype_class} picker-doc-clickable-link" data-doctype="${this.get_doctype_by_class(doctype_class)}" data-name="${nm}">${frappe.utils.escape_html(nm)}</span>`).join("")}</div>`;
    }

    get_doctype_by_class(cls) {
        if (cls === "purchase-order") return "Purchase Order";
        if (cls === "purchase-receipt") return "Purchase Receipt";
        if (cls === "purchase-invoice") return "Purchase Invoice";
        if (cls === "reimbursement-request") return "Reimbursement Request";
        return "";
    }

    // =========================================================================
    // Create Self-Service Wire Transfer Modal
    // =========================================================================

    open_create_wire_transfer_modal() {
        const self = this;
        let default_company = this.active_company !== "All" ? this.active_company : (this.companies[0]?.name || "");

        const d = new frappe.ui.Dialog({
            title: __("⚡ 新建自办电汇发票 · 极速录单与自动闭环生单"),
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "form_html",
                },
            ],
            primary_action_label: __("🚀 立即生成全套单据 (PO+PR+PI)"),
            primary_action: async function () {
                await self.submit_create_wire_transfer(d);
            },
        });

        d.$wrapper.find(".modal-dialog").addClass("ashan-smart-modal");

        let company_options = this.companies.map((c) => `<option value="${c.name}" ${c.name === default_company ? 'selected' : ''}>${frappe.utils.escape_html(c.company_name || c.name)}</option>`).join("");

        const form_html = `
            <div class="ashan-smart-modal-body">
                <!-- Section 1: Basic Info -->
                <div class="ashan-smart-section">
                    <div class="ashan-smart-section-header">
                        <div class="ashan-smart-section-title">
                            <span>🏢 1. 电汇业务上下文与发票基本信息</span>
                        </div>
                    </div>
                    <div class="ashan-smart-grid-4">
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">所属公司 <span class="req">*</span></label>
                            <select id="modal-wire-company" class="ashan-smart-control">
                                ${company_options}
                            </select>
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">供应商名称 <span class="req">*</span></label>
                            <input type="text" class="ashan-smart-control" id="modal-wire-supplier" placeholder="输入或搜索供应商..." />
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">发票号码 <span class="req">*</span></label>
                            <input type="text" class="ashan-smart-control" id="modal-wire-bill-no" placeholder="如 20268899..." />
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">发票日期</label>
                            <input type="date" class="ashan-smart-control" id="modal-wire-bill-date" value="${frappe.datetime.nowdate()}" />
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">发票类型</label>
                            <select class="ashan-smart-control" id="modal-wire-inv-type">
                                <option value="专用发票" selected>专用发票 (增值税专票)</option>
                                <option value="普通发票">普通发票 (增值税普票)</option>
                            </select>
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">默认目标仓库</label>
                            <input type="text" class="ashan-smart-control" id="modal-wire-warehouse" placeholder="默认 Goods In Transit..." />
                        </div>
                    </div>
                    <div class="ashan-smart-toggle-box">
                        <input type="checkbox" id="modal-wire-auto-receive" checked />
                        <span>⚡ 允许维护库存的物料系统全自动生成采购入库单并完成过账 (默认开启)</span>
                    </div>
                </div>

                <!-- Section 2: Items Details Table -->
                <div class="ashan-smart-section">
                    <div class="ashan-smart-section-header">
                        <div class="ashan-smart-section-title">
                            <span>📑 2. 自办电汇物料明细清单</span>
                        </div>
                        <div class="ashan-smart-section-tools">
                            <button type="button" class="btn btn-default btn-xs" id="modal-wire-add-row-btn">➕ 添加物料行</button>
                        </div>
                    </div>

                    <div class="ashan-smart-table-wrap">
                        <table class="ashan-smart-table" id="modal-wire-items-table">
                            <thead>
                                <tr>
                                    <th class="ashan-col-w40">#</th>
                                    <th class="ashan-col-w160">物料代码 <span class="req">*</span></th>
                                    <th class="ashan-col-w180">物料名称</th>
                                    <th class="ashan-col-w120">规格型号</th>
                                    <th class="ashan-col-w70">单位</th>
                                    <th class="ashan-col-w80">数量 <span class="req">*</span></th>
                                    <th class="ashan-col-w90">单价 (元) <span class="req">*</span></th>
                                    <th class="ashan-col-w70">税率(%)</th>
                                    <th class="ashan-col-w95">金额 (元)</th>
                                    <th class="ashan-col-w85">税额 (元)</th>
                                    <th class="ashan-col-w105">价税合计</th>
                                    <th class="ashan-col-w140">用途/备注</th>
                                    <th class="ashan-col-w45">操作</th>
                                </tr>
                            </thead>
                            <tbody id="modal-wire-items-tbody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- Section 3: Live Financial Summary & Discipline Bar -->
                <div class="ashan-smart-summary-bar">
                    <div class="ashan-smart-tip-box">
                        <span class="ashan-smart-tip-badge">🛡️ 财务纪律</span>
                        <span>单价与金额严禁为 0。系统将全自动闭环生成 PO ➔ PR(若库存品) ➔ PI ➔ RR。</span>
                    </div>
                    <div class="ashan-smart-kpi-group">
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">订购总数</span>
                            <span class="ashan-smart-kpi-value" id="modal-wire-sum-qty">0.00</span>
                        </div>
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">不含税金额</span>
                            <span class="ashan-smart-kpi-value" id="modal-wire-sum-amt">¥ 0.00</span>
                        </div>
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">预估税额</span>
                            <span class="ashan-smart-kpi-value" id="modal-wire-sum-tax">¥ 0.00</span>
                        </div>
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">电汇总额 (价税合计)</span>
                            <span class="ashan-smart-kpi-value grand-total text-primary" id="modal-wire-sum-total">¥ 0.00</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        d.fields_dict.form_html.$wrapper.html(form_html);

        // Bind Add Row
        d.$wrapper.on("click", "#modal-wire-add-row-btn", () => this.add_wire_modal_row(d));

        // Bind Row Delete
        d.$wrapper.on("click", ".wire-row-delete-btn", function () {
            $(this).closest("tr").remove();
            self.recalc_wire_modal_totals(d);
        });

        // Bind Calculations
        d.$wrapper.on("input change", ".wire-item-qty, .wire-item-rate, .wire-item-tax-rate", function () {
            const $tr = $(this).closest("tr");
            self.recalc_wire_modal_row($tr);
            self.recalc_wire_modal_totals(d);
        });

        // Autocomplete Item Code
        d.$wrapper.on("change", ".wire-item-code", async function () {
            const $tr = $(this).closest("tr");
            const code = $(this).val().trim();
            if (!code) return;

            try {
                const item_info = await frappe.db.get_value("Item", code, ["item_name", "stock_uom", "standard_rate", "description"]);
                if (item_info && item_info.message) {
                    const msg = item_info.message;
                    $tr.find(".wire-item-name").val(msg.item_name || code);
                    $tr.find(".wire-item-uom").val(msg.stock_uom || "Nos");
                    if (flt(msg.standard_rate) > 0 && flt($tr.find(".wire-item-rate").val()) === 0) {
                        $tr.find(".wire-item-rate").val(flt(msg.standard_rate).toFixed(2));
                    }
                    self.recalc_wire_modal_row($tr);
                    self.recalc_wire_modal_totals(d);
                }
            } catch (e) {
                console.log("Item lookup error:", e);
            }
        });

        d.show();

        // Add 2 initial rows after show
        this.add_wire_modal_row(d);
        this.add_wire_modal_row(d);
    }

    add_wire_modal_row(dialog) {
        const $tbody = (dialog && dialog.$wrapper) ? dialog.$wrapper.find("#modal-wire-items-tbody") : $("#modal-wire-items-tbody");
        const row_idx = $tbody.find("tr").length + 1;
        const tr_html = `
            <tr>
                <td class="ashan-smart-cell-idx">${row_idx}</td>
                <td><input type="text" class="ashan-smart-cell-input wire-item-code" placeholder="输入物料代码..." /></td>
                <td><input type="text" class="ashan-smart-cell-input wire-item-name" placeholder="物料名称" /></td>
                <td><input type="text" class="ashan-smart-cell-input wire-item-spec" placeholder="规格型号" /></td>
                <td><input type="text" class="ashan-smart-cell-input wire-item-uom text-center" value="Nos" /></td>
                <td><input type="number" class="ashan-smart-cell-input wire-item-qty text-right font-bold" value="1" min="0.001" step="any" /></td>
                <td><input type="number" class="ashan-smart-cell-input wire-item-rate text-right font-bold" value="0.00" min="0.01" step="any" /></td>
                <td><input type="number" class="ashan-smart-cell-input wire-item-tax-rate text-center" value="13" min="0" max="100" /></td>
                <td><input type="number" class="ashan-smart-cell-input wire-item-amt text-right font-bold" value="0.00" readonly /></td>
                <td><input type="number" class="ashan-smart-cell-input wire-item-tax-amt text-right" value="0.00" readonly /></td>
                <td><input type="number" class="ashan-smart-cell-input wire-item-total text-right font-bold text-primary" value="0.00" readonly /></td>
                <td><input type="text" class="ashan-smart-cell-input wire-item-remarks" placeholder="备注用途..." /></td>
                <td class="text-center">
                    <button type="button" class="btn btn-xs btn-default wire-row-delete-btn ashan-smart-btn-del" title="删除此行">✕</button>
                </td>
            </tr>
        `;
        $tbody.append(tr_html);
    }

    recalc_wire_modal_row($tr) {
        const qty = flt($tr.find(".wire-item-qty").val());
        const rate = flt($tr.find(".wire-item-rate").val());
        const tax_rate = flt($tr.find(".wire-item-tax-rate").val());

        const amt = flt(qty * rate, 2);
        const tax_amt = flt(amt * (tax_rate / 100.0), 2);
        const total = flt(amt + tax_amt, 2);

        $tr.find(".wire-item-amt").val(amt.toFixed(2));
        $tr.find(".wire-item-tax-amt").val(tax_amt.toFixed(2));
        $tr.find(".wire-item-total").val(total.toFixed(2));
    }

    recalc_wire_modal_totals(dialog) {
        const $wrap = (dialog && dialog.$wrapper) ? dialog.$wrapper : $(document);
        let sum_qty = 0;
        let sum_amt = 0;
        let sum_tax = 0;
        let sum_total = 0;

        $wrap.find("#modal-wire-items-tbody tr").each(function () {
            sum_qty += flt($(this).find(".wire-item-qty").val());
            sum_amt += flt($(this).find(".wire-item-amt").val());
            sum_tax += flt($(this).find(".wire-item-tax-amt").val());
            sum_total += flt($(this).find(".wire-item-total").val());
        });

        $wrap.find("#modal-wire-sum-qty").text(sum_qty.toFixed(2));
        $wrap.find("#modal-wire-sum-amt").text(this.fmt_money(sum_amt));
        $wrap.find("#modal-wire-sum-tax").text(this.fmt_money(sum_tax));
        $wrap.find("#modal-wire-sum-total").text(this.fmt_money(sum_total));
    }

    async submit_create_wire_transfer(dialog) {
        const $wrap = dialog.$wrapper;
        const company = $wrap.find("#modal-wire-company").val();
        const supplier = $wrap.find("#modal-wire-supplier").val().trim();
        const bill_no = $wrap.find("#modal-wire-bill-no").val().trim();
        const bill_date = $wrap.find("#modal-wire-bill-date").val();
        const invoice_type = $wrap.find("#modal-wire-inv-type").val();
        const warehouse = $wrap.find("#modal-wire-warehouse").val().trim();
        const auto_receive_stock = $wrap.find("#modal-wire-auto-receive").is(":checked") ? 1 : 0;

        if (!supplier) {
            frappe.msgprint(__("请填写供应商名称！"));
            return;
        }
        if (!bill_no) {
            frappe.msgprint(__("请填写发票号码！"));
            return;
        }

        const items = [];
        let has_zero_error = false;

        $wrap.find("#modal-wire-items-tbody tr").each(function (idx) {
            const item_code = $(this).find(".wire-item-code").val().trim();
            const item_name = $(this).find(".wire-item-name").val().trim();
            const spec = $(this).find(".wire-item-spec").val().trim();
            const uom = $(this).find(".wire-item-uom").val().trim();
            const qty = flt($(this).find(".wire-item-qty").val());
            const rate = flt($(this).find(".wire-item-rate").val());
            const tax_rate = flt($(this).find(".wire-item-tax-rate").val());
            const amount = flt($(this).find(".wire-item-amt").val());
            const tax_amount = flt($(this).find(".wire-item-tax-amt").val());
            const total_amount = flt($(this).find(".wire-item-total").val());
            const remarks = $(this).find(".wire-item-remarks").val().trim();

            if (!item_code) return; // ignore blank

            if (qty <= 0 || rate <= 0 || amount <= 0) {
                frappe.msgprint(`第 ${idx + 1} 行物料 [${item_code}] 的单价或金额为 0！根据财务纪律，单价与金额严禁为 0。`);
                has_zero_error = true;
                return false;
            }

            items.push({
                item_code,
                item_name,
                spec,
                uom,
                qty,
                rate,
                tax_rate,
                amount,
                tax_amount,
                total_amount,
                remarks,
            });
        });

        if (has_zero_error) return;

        if (items.length === 0) {
            frappe.msgprint(__("请录入至少一行有效的发票物料明细！"));
            return;
        }

        frappe.dom.freeze(__("正在自动闭环生成自办电汇单据..."));
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.wire_transfer_service.create_self_service_wire_transfer_bundle",
                args: {
                    company,
                    supplier,
                    bill_no,
                    bill_date,
                    invoice_type,
                    warehouse,
                    auto_receive_stock,
                    items,
                },
            });
            frappe.dom.unfreeze();

            if (r.message && r.message.success) {
                dialog.hide();
                frappe.show_alert({
                    message: `🎉 成功生成自办电汇单据！发票：${r.message.pi_name}`,
                    indicator: "green",
                }, 5);

                this.refresh_all();
                this.show_doc_detail_modal("Purchase Invoice", r.message.pi_name);
            }
        } catch (e) {
            frappe.dom.unfreeze();
            console.error("Failed to create wire transfer bundle:", e);
        }
    }

    // =========================================================================
    // Document Detail Modal (Full Upstream/Downstream Inspection)
    // =========================================================================

    async show_doc_detail_modal(doctype, name) {
        try {
            frappe.dom.freeze(__("正在拉取单据详情..."));
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.get_document_details",
                args: { doctype, name },
            });
            frappe.dom.unfreeze();

            if (!r.message) return;
            const doc = r.message;

            const d = new frappe.ui.Dialog({
                title: `${doc.doctype_label || doctype}: ${frappe.utils.escape_html(name)}`,
                size: "large",
                fields: [{ fieldtype: "HTML", fieldname: "detail_html" }],
                primary_action_label: __("打印单据"),
                primary_action: function () {
                    window.open(`/printview?doctype=${encodeURIComponent(doctype)}&name=${encodeURIComponent(name)}&trigger_print=1`, "_blank");
                },
                secondary_action_label: __("关闭"),
                secondary_action: function () {
                    d.hide();
                },
            });

            let items_html = (doc.items || []).map((it, idx) => `
                <tr>
                    <td class="wire-col-idx-val">${idx + 1}</td>
                    <td><strong>${frappe.utils.escape_html(it.item_code)}</strong></td>
                    <td>${frappe.utils.escape_html(it.item_name || "")}</td>
                    <td>${frappe.utils.escape_html(it.spec || "-")}</td>
                    <td>${frappe.utils.escape_html(it.uom || "")}</td>
                    <td class="picker-qty-cell">${it.qty}</td>
                    <td class="picker-money-cell">${this.fmt_money(it.rate)}</td>
                    <td class="picker-money-cell">${this.fmt_money(it.amount)}</td>
                    <td class="picker-money-cell">${this.fmt_money(it.tax_amount)}</td>
                    <td class="picker-money-cell wire-col-total">${this.fmt_money(it.total_amount)}</td>
                    <td>${frappe.utils.escape_html(it.remarks || "-")}</td>
                </tr>
            `).join("");

            const html = `
                <div class="wire-detail-wrap">
                    <div class="wire-detail-meta-grid">
                        <div><strong class="wire-detail-meta-label">所属公司:</strong> <span class="ashan-tag-badge">${frappe.utils.escape_html(doc.company)}</span></div>
                        <div><strong class="wire-detail-meta-label">单据日期:</strong> ${doc.date}</div>
                        <div><strong class="wire-detail-meta-label">单据状态:</strong> <span class="ashan-status-badge ashan-status-blue">${frappe.utils.escape_html(doc.status)}</span></div>
                        <div><strong class="wire-detail-meta-label">经手人:</strong> ${frappe.utils.escape_html(doc.owner)}</div>
                        ${doc.supplier ? `<div class="wire-detail-grid-span2"><strong class="wire-detail-meta-label">供应商:</strong> <strong>${frappe.utils.escape_html(doc.supplier)}</strong></div>` : ""}
                        ${doc.bill_no ? `<div class="wire-detail-grid-span2"><strong class="wire-detail-meta-label">发票号码:</strong> <span class="ashan-tag-badge ashan-tag-blue">${frappe.utils.escape_html(doc.bill_no)}</span></div>` : ""}
                    </div>

                    <div class="wire-detail-table-wrap">
                        <table class="picker-data-table">
                            <thead>
                                <tr>
                                    <th class="wire-col-idx">#</th>
                                    <th>物料代码</th>
                                    <th>物料名称</th>
                                    <th>规格型号</th>
                                    <th>单位</th>
                                    <th>数量</th>
                                    <th>单价</th>
                                    <th>金额</th>
                                    <th>税额</th>
                                    <th>价税合计</th>
                                    <th>备注/用途</th>
                                </tr>
                            </thead>
                            <tbody>${items_html}</tbody>
                            <tfoot>
                                <tr>
                                    <td colspan="5" class="wire-sum-label">合计:</td>
                                    <td class="picker-qty-cell wire-sum-num">${doc.total_qty.toFixed(2)}</td>
                                    <td></td>
                                    <td class="picker-money-cell wire-sum-num">${this.fmt_money(doc.total_amount)}</td>
                                    <td></td>
                                    <td class="picker-money-cell wire-sum-highlight">${this.fmt_money(doc.total_amount)}</td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            `;

            d.fields_dict.detail_html.$wrapper.html(html);
            d.show();
        } catch (e) {
            frappe.dom.unfreeze();
            console.error("Failed to load document details:", e);
        }
    }
}
