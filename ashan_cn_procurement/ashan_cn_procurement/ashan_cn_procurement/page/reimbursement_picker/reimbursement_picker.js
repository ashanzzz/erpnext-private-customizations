// Copyright (c) 2026, Ashan CN Procurement and contributors
// For license information, please see license.txt

frappe.pages["reimbursement-picker"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("🚀 采购全流程选单生单中心"),
        single_column: true,
    });

    wrapper.reim_picker = new ReimbursementPicker(page);
};

class ReimbursementPicker {
    constructor(page) {
        this.page = page;
        this.active_company = "All";
        this.companies = [];
        this.view_mode = "detail"; // detail | doc
        this.match_status = "pending"; // pending | completed | all
        this.selected_items = new Set();
        this.cached_rows = [];
        this.kpis = {};

        this.init();
    }

    async init() {
        this.render_layout();
        await this.load_companies();
        this.bind_global_events();
        this.refresh_all();
    }

    render_layout() {
        const html = `
            <div class="picker-page-container">
                <!-- Top Header & Company Selector -->
                <div class="picker-top-bar">
                    <div class="picker-title-group">
                        <h2>🚀 采购全流程选单生单中心</h2>
                        <div class="picker-subtitle">报销申请</div>
                    </div>
                    <div class="picker-company-group">
                        <label class="picker-company-label" for="reim-company-select">所属公司:</label>
                        <select id="reim-company-select" class="picker-company-select">
                            <option value="All">🌐 全部公司 (汇聚视图)</option>
                        </select>
                    </div>
                </div>

                <!-- 4 KPI Cards Pipeline Bar -->
                <div class="picker-kpi-grid" id="reim-kpi-grid">
                    <div class="picker-kpi-card active" data-step="rr_pending">
                        <div class="picker-kpi-header">
                            <span class="picker-kpi-title">报销申请</span>
                            <span class="picker-kpi-icon">💰</span>
                        </div>
                        <div class="picker-kpi-body">
                            <div class="picker-kpi-number" id="reim-kpi-pending-rr">0</div>
                            <div class="picker-kpi-sub" id="reim-kpi-pending-sub">待结款报销单</div>
                        </div>
                    </div>
                    <div class="picker-kpi-card" data-step="pi">
                        <div class="picker-kpi-header">
                            <span class="picker-kpi-title">采购发票</span>
                            <span class="picker-kpi-icon">🧾</span>
                        </div>
                        <div class="picker-kpi-body">
                            <div class="picker-kpi-number" id="reim-kpi-pi-count">0</div>
                            <div class="picker-kpi-sub">垫付采购发票</div>
                        </div>
                    </div>
                    <div class="picker-kpi-card" data-step="pr">
                        <div class="picker-kpi-header">
                            <span class="picker-kpi-title">采购入库</span>
                            <span class="picker-kpi-icon">📦</span>
                        </div>
                        <div class="picker-kpi-body">
                            <div class="picker-kpi-number" id="reim-kpi-pr-count">0</div>
                            <div class="picker-kpi-sub">自动入库单</div>
                        </div>
                    </div>
                    <div class="picker-kpi-card" data-step="outstanding_amt">
                        <div class="picker-kpi-header">
                            <span class="picker-kpi-title">待报销付款</span>
                            <span class="picker-kpi-icon">💳</span>
                        </div>
                        <div class="picker-kpi-body">
                            <div class="picker-kpi-number" id="reim-kpi-outstanding-amt">¥ 0.00</div>
                            <div class="picker-kpi-sub">待付款结清总额</div>
                        </div>
                    </div>
                </div>

                <!-- Section Context Banner -->
                <div class="picker-section-banner" id="reim-section-banner">
                    <div class="picker-section-main">
                        <div class="picker-section-icon">🚀</div>
                        <div class="picker-section-heading">
                            <div class="picker-section-title">
                                <span>报销申请 · 极速录单与全链路闭环生单中心</span>
                            </div>
                            <div class="picker-section-desc">填写报销申请，系统全自动生成并提交采购订单 (PO) ➔ 采购入库单 (PR，若库存品) ➔ 采购发票 (PI) ➔ 报销申请单 (RR)。</div>
                        </div>
                    </div>
                    <div class="picker-section-badge" id="reim-total-summary-badge">
                        统计: 0 笔
                    </div>
                </div>

                <!-- Filter Controls Bar -->
                <div class="picker-filter-bar" id="reim-filter-bar">
                    <div class="picker-filter-group">
                        <label>付款状态:</label>
                        <div class="picker-status-btn-group" id="reim-status-btn-group">
                            <button type="button" class="picker-status-btn active" data-status="pending">🟡 仅待付款结清</button>
                            <button type="button" class="picker-status-btn" data-status="completed">🟢 仅已付款结清</button>
                            <button type="button" class="picker-status-btn" data-status="all">🌐 全部报销单据</button>
                        </div>
                    </div>
                    <div class="picker-filter-group">
                        <label>报销人员:</label>
                        <input type="text" class="picker-input" data-filter="employee" placeholder="搜索报销人..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>商户/供应商:</label>
                        <input type="text" class="picker-input" data-filter="supplier" placeholder="搜索商户/供应商..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>发票号码:</label>
                        <input type="text" class="picker-input" data-filter="invoice_no" placeholder="发票号码..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>物料/费用项:</label>
                        <input type="text" class="picker-input" data-filter="item_code" placeholder="物料代码/说明..." />
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
                        <span>已选 <strong class="picker-summary-highlight" id="reim-selected-count">0</strong> 项</span>
                        <span>本次总计: <strong class="picker-summary-highlight" id="reim-selected-amount">¥ 0.00</strong></span>
                    </div>
                    <div class="picker-btn-group">
                        <button type="button" class="picker-btn-sub" id="reim-select-all-btn">全选本页</button>
                        <button type="button" class="picker-btn-sub" id="reim-clear-sel-btn">清空选择</button>
                        <button type="button" class="reim-btn-create-rr" id="reim-open-create-modal-btn">🚀 + 新建报销申请单</button>
                    </div>
                </div>

                <!-- Big Wide Data Table Container -->
                <div class="picker-table-wrapper">
                    <!-- Top Sync Scrollbar -->
                    <div class="picker-top-scrollbar-wrap" id="reim-top-scrollbar">
                        <div class="picker-top-scrollbar-inner" id="reim-top-scrollbar-inner"></div>
                    </div>

                    <!-- Main Table Scroll Area -->
                    <div class="picker-main-table-scroll" id="reim-main-table-scroll">
                        <table class="picker-data-table" id="reim-data-table">
                            <thead id="reim-table-thead"></thead>
                            <tbody id="reim-table-tbody"></tbody>
                            <tfoot id="reim-table-tfoot"></tfoot>
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
                const $select = $("#reim-company-select");
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
            console.error("Failed to load companies for reimbursement picker:", e);
        }
    }

    bind_global_events() {
        const self = this;

        // Company change
        $("#reim-company-select").on("change", function () {
            self.active_company = $(this).val();
            self.selected_items.clear();
            self.refresh_all();
        });

        // Filter button group
        $("#reim-status-btn-group").on("click", ".picker-status-btn", function () {
            $(this).siblings().removeClass("active");
            $(this).addClass("active");
            self.match_status = $(this).data("status");
            self.selected_items.clear();
            self.load_table_data();
        });

        // Search inputs with debounce
        let search_timer = null;
        $("#reim-filter-bar").on("input change", "input[data-filter]", function () {
            clearTimeout(search_timer);
            search_timer = setTimeout(() => {
                self.selected_items.clear();
                self.load_table_data();
            }, 300);
        });

        // View mode switch
        $(".picker-view-switch-group").on("click", ".picker-view-btn", function () {
            $(this).siblings().removeClass("active");
            $(this).addClass("active");
            self.view_mode = $(this).data("mode");
            self.selected_items.clear();
            self.render_table();
        });

        // Select All / Clear Select
        $("#reim-select-all-btn").on("click", function () {
            self.cached_rows.forEach((r) => {
                const key = self.view_mode === "detail" ? r.rii_name : r.rr_name;
                self.selected_items.add(key);
            });
            self.update_selection_summary();
            self.sync_checkbox_states();
        });

        $("#reim-clear-sel-btn").on("click", function () {
            self.selected_items.clear();
            self.update_selection_summary();
            self.sync_checkbox_states();
        });

        // Checkbox change in table
        $("#reim-table-tbody").on("change", ".picker-row-checkbox", function () {
            const key = $(this).data("key");
            if ($(this).is(":checked")) {
                self.selected_items.add(key);
            } else {
                self.selected_items.delete(key);
            }
            self.update_selection_summary();
        });

        // Open create modal
        $("#reim-open-create-modal-btn").on("click", function () {
            self.open_create_reimbursement_modal();
        });

        // Table drill-down
        $("#reim-table-tbody").on("click", ".picker-clickable-doc", function () {
            const dt = $(this).data("doctype");
            const dn = $(this).data("name");
            if (dt && dn) {
                self.show_doc_detail_modal(dt, dn);
            }
        });

        // Mousewheel-to-Horizontal Scroll
        this.bind_wheel_horizontal_scroll();
    }

    bind_wheel_horizontal_scroll() {
        const table_container = document.getElementById("reim-main-table-scroll");
        const top_scrollbar = document.getElementById("reim-top-scrollbar");
        const thead = document.getElementById("reim-table-thead");

        if (!table_container || !top_scrollbar) return;

        // Dual scrollbar synchronization
        let is_syncing_main = false;
        let is_syncing_top = false;

        table_container.addEventListener("scroll", () => {
            if (!is_syncing_main) {
                is_syncing_top = true;
                top_scrollbar.scrollLeft = table_container.scrollLeft;
                is_syncing_top = false;
            }
        });

        top_scrollbar.addEventListener("scroll", () => {
            if (!is_syncing_top) {
                is_syncing_main = true;
                table_container.scrollLeft = top_scrollbar.scrollLeft;
                is_syncing_main = false;
            }
        });

        // Convert mousewheel vertical scroll to horizontal scroll
        const handle_wheel = (e) => {
            if (table_container.scrollWidth > table_container.clientWidth) {
                if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
                    e.preventDefault();
                    table_container.scrollLeft += e.deltaY;
                }
            }
        };

        if (thead) thead.addEventListener("wheel", handle_wheel, { passive: false });
        table_container.addEventListener("wheel", handle_wheel, { passive: false });
    }

    sync_top_scrollbar_width() {
        const table = document.getElementById("reim-data-table");
        const inner = document.getElementById("reim-top-scrollbar-inner");
        if (table && inner) {
            inner.style.width = `${table.scrollWidth}px`;
        }
    }

    get_current_filters() {
        const filters = {
            match_status: this.match_status,
        };
        $("#reim-filter-bar input[data-filter]").each(function () {
            const k = $(this).data("filter");
            const v = $(this).val().trim();
            if (v) filters[k] = v;
        });
        return filters;
    }

    async refresh_all() {
        await Promise.all([this.load_kpis(), this.load_table_data()]);
    }

    async load_kpis() {
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_picker_overview_kpis",
                args: { company: this.active_company },
            });
            if (r.message) {
                this.kpis = r.message;
                $("#reim-kpi-pending-rr").text(this.kpis.pending_rr_count || 0);
                $("#reim-kpi-pi-count").text(this.kpis.pi_count || 0);
                $("#reim-kpi-pr-count").text(this.kpis.pr_count || 0);
                $("#reim-kpi-outstanding-amt").text(this.fmt_money(this.kpis.rr_outstanding || 0));
            }
        } catch (e) {
            console.error("Failed to load KPIs:", e);
        }
    }

    async load_table_data() {
        const method = this.view_mode === "detail"
            ? "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_picker_rows"
            : "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_picker_doc_summary_rows";

        try {
            frappe.dom.freeze(__("正在加载报销申请数据..."));
            const r = await frappe.call({
                method: method,
                args: {
                    company: this.active_company,
                    filters: this.get_current_filters(),
                },
            });
            frappe.dom.unfreeze();

            if (r.message) {
                this.cached_rows = r.message.rows || [];
                $("#reim-total-summary-badge").text(`统计: ${this.cached_rows.length} 笔`);
                this.render_table();
            }
        } catch (e) {
            frappe.dom.unfreeze();
            console.error("Failed to load table data:", e);
        }
    }

    render_table() {
        if (this.view_mode === "detail") {
            this.render_detail_view();
        } else {
            this.render_doc_view();
        }
        this.sync_top_scrollbar_width();
        this.update_selection_summary();
    }

    render_detail_view() {
        const thead_html = `
            <tr>
                <th class="qifu-col-sticky-1">
                    <span class="picker-th-badge">SEQ</span>
                    <span class="picker-th-title">#</span>
                </th>
                <th class="picker-col-chk">
                    <span class="picker-th-badge">SEL</span>
                    <span class="picker-th-title">选择</span>
                </th>
                <th>
                    <span class="picker-th-badge">CORP</span>
                    <span class="picker-th-title">所属公司</span>
                </th>
                <th>
                    <span class="picker-th-badge">REIM NO</span>
                    <span class="picker-th-title">报销单号</span>
                </th>
                <th>
                    <span class="picker-th-badge">EMP</span>
                    <span class="picker-th-title">报销人</span>
                </th>
                <th>
                    <span class="picker-th-badge">VENDOR</span>
                    <span class="picker-th-title">商户/供应商</span>
                </th>
                <th>
                    <span class="picker-th-badge">INVOICE</span>
                    <span class="picker-th-title">发票代码/号码</span>
                </th>
                <th>
                    <span class="picker-th-badge">STATUS</span>
                    <span class="picker-th-title">付款状态</span>
                </th>
                <th>
                    <span class="picker-th-badge">ITEM</span>
                    <span class="picker-th-title">费用/物料明细</span>
                </th>
                <th>
                    <span class="picker-th-badge">SPEC</span>
                    <span class="picker-th-title">规格说明</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">QTY</span>
                    <span class="picker-th-title">数量</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">RATE</span>
                    <span class="picker-th-title">单价</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">TAX RATE</span>
                    <span class="picker-th-title">税率</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">AMOUNT</span>
                    <span class="picker-th-title">报销金额</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">OUTSTANDING</span>
                    <span class="picker-th-title">待结款金额</span>
                </th>
                <th>
                    <span class="picker-th-badge">LINKED PI</span>
                    <span class="picker-th-title">关联发票</span>
                </th>
                <th>
                    <span class="picker-th-badge">DATE</span>
                    <span class="picker-th-title">开票/单据日期</span>
                </th>
            </tr>
        `;
        $("#reim-table-thead").html(thead_html);

        if (this.cached_rows.length === 0) {
            $("#reim-table-tbody").html(`
                <tr>
                    <td colspan="17" class="picker-empty-state">
                        <div class="picker-empty-icon">🚀</div>
                        <div class="picker-empty-text">当前暂无报销申请记录，点击上方【🚀 + 新建报销申请单】即可极速录单！</div>
                    </td>
                </tr>
            `);
            $("#reim-table-tfoot").empty();
            return;
        }

        let sum_qty = 0;
        let sum_amt = 0;
        let sum_outstanding = 0;

        let tbody_html = "";
        this.cached_rows.forEach((r, idx) => {
            sum_qty += flt(r.qty);
            sum_amt += flt(r.amount);
            sum_outstanding += flt(r.outstanding_amount);

            const is_checked = this.selected_items.has(r.rii_name) ? "checked" : "";

            tbody_html += `
                <tr>
                    <td class="qifu-col-sticky-1 picker-col-idx">${idx + 1}</td>
                    <td class="picker-col-chk">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${r.rii_name}" ${is_checked} />
                    </td>
                    <td>${frappe.utils.escape_html(r.company)}</td>
                    <td>
                        <span class="picker-clickable-doc" data-doctype="Reimbursement Request" data-name="${r.rr_name}">
                            ${frappe.utils.escape_html(r.rr_name)}
                        </span>
                    </td>
                    <td>${frappe.utils.escape_html(r.employee_name || r.employee || "-")}</td>
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                    <td>${frappe.utils.escape_html(r.invoice_no || "-")}</td>
                    <td><span class="picker-status-tag">${r.status_label}</span></td>
                    <td><strong>${frappe.utils.escape_html(r.item_name)}</strong></td>
                    <td>${frappe.utils.escape_html(r.spec || "-")}</td>
                    <td class="text-right">${flt(r.qty).toFixed(2)}</td>
                    <td class="text-right qifu-money-cell">${this.fmt_money(r.rate)}</td>
                    <td class="text-right">${flt(r.tax_rate)}%</td>
                    <td class="text-right qifu-money-cell font-bold">${this.fmt_money(r.amount)}</td>
                    <td class="text-right qifu-money-cell ${r.outstanding_amount > 0 ? 'text-danger font-bold' : ''}">
                        ${this.fmt_money(r.outstanding_amount)}
                    </td>
                    <td>
                        ${r.source_pi && r.source_pi !== '-' ? `<span class="picker-clickable-doc" data-doctype="Purchase Invoice" data-name="${r.source_pi}">${r.source_pi}</span>` : "-"}
                    </td>
                    <td>${r.posting_date}</td>
                </tr>
            `;
        });
        $("#reim-table-tbody").html(tbody_html);

        const tfoot_html = `
            <tr>
                <td colspan="10" class="text-left font-bold">合计 (共 ${this.cached_rows.length} 笔)</td>
                <td class="text-right font-bold">${sum_qty.toFixed(2)}</td>
                <td colspan="2"></td>
                <td class="text-right qifu-money-cell font-bold">${this.fmt_money(sum_amt)}</td>
                <td class="text-right qifu-money-cell font-bold">${this.fmt_money(sum_outstanding)}</td>
                <td colspan="2"></td>
            </tr>
        `;
        $("#reim-table-tfoot").html(tfoot_html);
    }

    render_doc_view() {
        const thead_html = `
            <tr>
                <th class="qifu-col-sticky-1">
                    <span class="picker-th-badge">SEQ</span>
                    <span class="picker-th-title">#</span>
                </th>
                <th class="picker-col-chk">
                    <span class="picker-th-badge">SEL</span>
                    <span class="picker-th-title">选择</span>
                </th>
                <th>
                    <span class="picker-th-badge">CORP</span>
                    <span class="picker-th-title">所属公司</span>
                </th>
                <th>
                    <span class="picker-th-badge">REIM NO</span>
                    <span class="picker-th-title">报销单号</span>
                </th>
                <th>
                    <span class="picker-th-badge">EMP</span>
                    <span class="picker-th-title">报销人</span>
                </th>
                <th>
                    <span class="picker-th-badge">VENDOR</span>
                    <span class="picker-th-title">商户/供应商</span>
                </th>
                <th>
                    <span class="picker-th-badge">INVOICE</span>
                    <span class="picker-th-title">发票号码</span>
                </th>
                <th>
                    <span class="picker-th-badge">STATUS</span>
                    <span class="picker-th-title">状态</span>
                </th>
                <th>
                    <span class="picker-th-badge">DETAILS</span>
                    <span class="picker-th-title">单据明细</span>
                </th>
                <th>
                    <span class="picker-th-badge">DATE</span>
                    <span class="picker-th-title">申请日期</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">ITEMS</span>
                    <span class="picker-th-title">行数</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">AMOUNT</span>
                    <span class="picker-th-title">报销总额</span>
                </th>
                <th class="text-right">
                    <span class="picker-th-badge">OUTSTANDING</span>
                    <span class="picker-th-title">待结款金额</span>
                </th>
                <th>
                    <span class="picker-th-badge">LINKED PI</span>
                    <span class="picker-th-title">关联发票</span>
                </th>
            </tr>
        `;
        $("#reim-table-thead").html(thead_html);

        if (this.cached_rows.length === 0) {
            $("#reim-table-tbody").html(`
                <tr>
                    <td colspan="14" class="picker-empty-state">
                        <div class="picker-empty-icon">🚀</div>
                        <div class="picker-empty-text">当前暂无报销申请单据记录</div>
                    </td>
                </tr>
            `);
            $("#reim-table-tfoot").empty();
            return;
        }

        let sum_total = 0;
        let sum_outstanding = 0;

        let tbody_html = "";
        this.cached_rows.forEach((r, idx) => {
            sum_total += flt(r.total_amount);
            sum_outstanding += flt(r.outstanding_amount);

            const is_checked = this.selected_items.has(r.rr_name) ? "checked" : "";

            tbody_html += `
                <tr>
                    <td class="qifu-col-sticky-1 picker-col-idx">${idx + 1}</td>
                    <td class="picker-col-chk">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${r.rr_name}" ${is_checked} />
                    </td>
                    <td>${frappe.utils.escape_html(r.company)}</td>
                    <td>
                        <span class="picker-clickable-doc" data-doctype="Reimbursement Request" data-name="${r.rr_name}">
                            ${frappe.utils.escape_html(r.rr_name)}
                        </span>
                    </td>
                    <td>${frappe.utils.escape_html(r.employee_name || r.employee || "-")}</td>
                    <td>${frappe.utils.escape_html(r.suppliers)}</td>
                    <td>${frappe.utils.escape_html(r.invoice_nos)}</td>
                    <td><span class="picker-status-tag">${r.status_label}</span></td>
                    <td>${frappe.utils.escape_html(r.doc_details)}</td>
                    <td>${r.posting_date}</td>
                    <td class="text-right">${r.item_count}</td>
                    <td class="text-right qifu-money-cell font-bold">${this.fmt_money(r.total_amount)}</td>
                    <td class="text-right qifu-money-cell ${r.outstanding_amount > 0 ? 'text-danger font-bold' : ''}">
                        ${this.fmt_money(r.outstanding_amount)}
                    </td>
                    <td>${frappe.utils.escape_html(r.linked_pis || "-")}</td>
                </tr>
            `;
        });
        $("#reim-table-tbody").html(tbody_html);

        const tfoot_html = `
            <tr>
                <td colspan="11" class="text-left font-bold">合计 (共 ${this.cached_rows.length} 笔)</td>
                <td class="text-right qifu-money-cell font-bold">${this.fmt_money(sum_total)}</td>
                <td class="text-right qifu-money-cell font-bold">${this.fmt_money(sum_outstanding)}</td>
                <td></td>
            </tr>
        `;
        $("#reim-table-tfoot").html(tfoot_html);
    }

    update_selection_summary() {
        const count = this.selected_items.size;
        let amount = 0.0;

        if (this.view_mode === "detail") {
            this.cached_rows.forEach((r) => {
                if (this.selected_items.has(r.rii_name)) {
                    amount += flt(r.outstanding_amount > 0 ? r.outstanding_amount : r.amount);
                }
            });
        } else {
            this.cached_rows.forEach((r) => {
                if (this.selected_items.has(r.rr_name)) {
                    amount += flt(r.outstanding_amount > 0 ? r.outstanding_amount : r.total_amount);
                }
            });
        }

        $("#reim-selected-count").text(count);
        $("#reim-selected-amount").text(this.fmt_money(amount));
    }

    sync_checkbox_states() {
        const self = this;
        $("#reim-table-tbody .picker-row-checkbox").each(function () {
            const key = $(this).data("key");
            $(this).prop("checked", self.selected_items.has(key));
        });
    }

    fmt_money(val) {
        return "¥ " + flt(val || 0, 2).toLocaleString("zh-CN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    // =========================================================================
    // Fast Reimbursement Creation Modal (Reimbursement-driven PO+PR+PI+RR Auto Bundle)
    // =========================================================================

    open_create_reimbursement_modal() {
        const self = this;

        const d = new frappe.ui.Dialog({
            title: __("🚀 新建报销申请单 · 极速录单与全链路闭环生单"),
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "form_html",
                },
            ],
            primary_action_label: __("🚀 立即生成全链路单据 (PO+PR+PI+RR)"),
            primary_action: async function () {
                await self.submit_create_reimbursement(d);
            },
        });

        d.$wrapper.find(".modal-dialog").addClass("ashan-smart-modal");

        const comp_options = this.companies.map((c) =>
            `<option value="${c.name}" ${c.name === (self.active_company === "All" ? self.companies[0]?.name : self.active_company) ? "selected" : ""}>${frappe.utils.escape_html(c.company_name || c.name)}</option>`
        ).join("");

        const form_html = `
            <div class="ashan-smart-modal-body">
                <!-- Section 1: Basic Info -->
                <div class="ashan-smart-section">
                    <div class="ashan-smart-section-header">
                        <div class="ashan-smart-section-title">
                            <span>🏢 1. 报销申请上下文与发票基础信息</span>
                        </div>
                    </div>
                    <div class="ashan-smart-grid-4">
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">所属公司 <span class="req">*</span></label>
                            <select class="ashan-smart-control" id="modal-reim-company">
                                ${comp_options}
                            </select>
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">报销人员 (员工)</label>
                            <input type="text" class="ashan-smart-control" id="modal-reim-employee" placeholder="输入员工工号或姓名..." />
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">商户/供应商名称</label>
                            <input type="text" class="ashan-smart-control" id="modal-reim-supplier" placeholder="商户/开票单位..." />
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">发票号码</label>
                            <input type="text" class="ashan-smart-control" id="modal-reim-invoice-no" placeholder="发票代码/号码..." />
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">发票类型</label>
                            <select class="ashan-smart-control" id="modal-reim-invoice-type">
                                <option value="专用发票">专用发票</option>
                                <option value="普通发票">普通发票</option>
                            </select>
                        </div>
                        <div class="ashan-smart-field">
                            <label class="ashan-smart-field-label">开票/报销日期</label>
                            <input type="date" class="ashan-smart-control" id="modal-reim-date" value="${frappe.datetime.nowdate()}" />
                        </div>
                    </div>
                    <div class="ashan-smart-toggle-box">
                        <input type="checkbox" id="modal-reim-auto-stock" checked />
                        <span>📦 若包含允许维护库存的物料，系统全自动生成采购入库单并完成过账 (默认开启)</span>
                    </div>
                </div>

                <!-- Section 2: Items Details Table -->
                <div class="ashan-smart-section">
                    <div class="ashan-smart-section-header">
                        <div class="ashan-smart-section-title">
                            <span>📑 2. 报销物料与费用明细清单</span>
                        </div>
                        <div class="ashan-smart-section-tools">
                            <button type="button" class="btn btn-default btn-xs" id="modal-reim-add-row-btn">➕ 添加明细行</button>
                        </div>
                    </div>

                    <div class="ashan-smart-table-wrap">
                        <table class="ashan-smart-table" id="modal-reim-items-table">
                            <thead>
                                <tr>
                                    <th class="ashan-col-w40">#</th>
                                    <th class="ashan-col-w160">物料/费用代码 <span class="req">*</span></th>
                                    <th class="ashan-col-w180">名称说明</th>
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
                            <tbody id="modal-reim-items-tbody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- Section 3: Live Financial Summary & Discipline Bar -->
                <div class="ashan-smart-summary-bar">
                    <div class="ashan-smart-tip-box">
                        <span class="ashan-smart-tip-badge">🛡️ 财务纪律</span>
                        <span>单价与金额严禁为 0。系统将全自动闭环生成 PO ➔ PR(若库存品) ➔ PI ➔ RR 报销单。</span>
                    </div>
                    <div class="ashan-smart-kpi-group">
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">报销总数</span>
                            <span class="ashan-smart-kpi-value" id="modal-reim-sum-qty">0.00</span>
                        </div>
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">不含税金额</span>
                            <span class="ashan-smart-kpi-value" id="modal-reim-sum-amt">¥ 0.00</span>
                        </div>
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">预估税额</span>
                            <span class="ashan-smart-kpi-value" id="modal-reim-sum-tax">¥ 0.00</span>
                        </div>
                        <div class="ashan-smart-kpi-item">
                            <span class="ashan-smart-kpi-label">报销总额 (应付)</span>
                            <span class="ashan-smart-kpi-value grand-total text-warning" id="modal-reim-sum-total">¥ 0.00</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        d.fields_dict.form_html.$wrapper.html(form_html);

        // Bind Add Row
        d.$wrapper.on("click", "#modal-reim-add-row-btn", () => this.add_reim_modal_row(d));

        // Bind Row Delete
        d.$wrapper.on("click", ".reim-row-delete-btn", function () {
            $(this).closest("tr").remove();
            self.recalc_reim_modal_totals(d);
        });

        // Bind Calculations
        d.$wrapper.on("input change", ".reim-item-qty, .reim-item-rate, .reim-item-tax-rate", function () {
            const $tr = $(this).closest("tr");
            self.recalc_reim_modal_row($tr);
            self.recalc_reim_modal_totals(d);
        });

        // Autocomplete Item Code
        d.$wrapper.on("change", ".reim-item-code", async function () {
            const $tr = $(this).closest("tr");
            const code = $(this).val().trim();
            if (!code) return;

            try {
                const item_info = await frappe.db.get_value("Item", code, ["item_name", "stock_uom", "standard_rate", "description"]);
                if (item_info && item_info.message) {
                    const msg = item_info.message;
                    $tr.find(".reim-item-name").val(msg.item_name || code);
                    $tr.find(".reim-item-uom").val(msg.stock_uom || "Nos");
                    if (flt(msg.standard_rate) > 0 && flt($tr.find(".reim-item-rate").val()) === 0) {
                        $tr.find(".reim-item-rate").val(flt(msg.standard_rate).toFixed(2));
                    }
                    self.recalc_reim_modal_row($tr);
                    self.recalc_reim_modal_totals(d);
                }
            } catch (e) {
                console.log("Item lookup error:", e);
            }
        });

        d.show();

        // Add 2 initial rows
        this.add_reim_modal_row(d);
        this.add_reim_modal_row(d);
    }

    add_reim_modal_row(dialog) {
        const $tbody = (dialog && dialog.$wrapper) ? dialog.$wrapper.find("#modal-reim-items-tbody") : $("#modal-reim-items-tbody");
        const row_idx = $tbody.find("tr").length + 1;
        const tr_html = `
            <tr>
                <td class="ashan-smart-cell-idx">${row_idx}</td>
                <td><input type="text" class="ashan-smart-cell-input reim-item-code" placeholder="物料/费用代码..." /></td>
                <td><input type="text" class="ashan-smart-cell-input reim-item-name" placeholder="名称说明" /></td>
                <td><input type="text" class="ashan-smart-cell-input reim-item-spec" placeholder="规格型号" /></td>
                <td><input type="text" class="ashan-smart-cell-input reim-item-uom text-center" value="Nos" /></td>
                <td><input type="number" class="ashan-smart-cell-input reim-item-qty text-right font-bold" value="1" min="0.001" step="any" /></td>
                <td><input type="number" class="ashan-smart-cell-input reim-item-rate text-right font-bold" value="0.00" min="0.01" step="any" /></td>
                <td><input type="number" class="ashan-smart-cell-input reim-item-tax-rate text-center" value="13" min="0" max="100" /></td>
                <td><input type="number" class="ashan-smart-cell-input reim-item-amt text-right font-bold" value="0.00" readonly /></td>
                <td><input type="number" class="ashan-smart-cell-input reim-item-tax-amt text-right" value="0.00" readonly /></td>
                <td><input type="number" class="ashan-smart-cell-input reim-item-total text-right font-bold text-warning" value="0.00" readonly /></td>
                <td><input type="text" class="ashan-smart-cell-input reim-item-remarks" placeholder="备注用途..." /></td>
                <td class="text-center">
                    <button type="button" class="btn btn-xs btn-default reim-row-delete-btn ashan-smart-btn-del" title="删除此行">✕</button>
                </td>
            </tr>
        `;
        $tbody.append(tr_html);
    }

    recalc_reim_modal_row($tr) {
        const qty = flt($tr.find(".reim-item-qty").val());
        const rate = flt($tr.find(".reim-item-rate").val());
        const tax_rate = flt($tr.find(".reim-item-tax-rate").val());

        const amt = flt(qty * rate, 2);
        const tax_amt = flt(amt * (tax_rate / 100.0), 2);
        const total = flt(amt + tax_amt, 2);

        $tr.find(".reim-item-amt").val(amt.toFixed(2));
        $tr.find(".reim-item-tax-amt").val(tax_amt.toFixed(2));
        $tr.find(".reim-item-total").val(total.toFixed(2));
    }

    recalc_reim_modal_totals(dialog) {
        const $wrap = (dialog && dialog.$wrapper) ? dialog.$wrapper : $(document);
        let sum_qty = 0;
        let sum_amt = 0;
        let sum_tax = 0;
        let sum_total = 0;

        $wrap.find("#modal-reim-items-tbody tr").each(function () {
            sum_qty += flt($(this).find(".reim-item-qty").val());
            sum_amt += flt($(this).find(".reim-item-amt").val());
            sum_tax += flt($(this).find(".reim-item-tax-amt").val());
            sum_total += flt($(this).find(".reim-item-total").val());
        });

        $wrap.find("#modal-reim-sum-qty").text(sum_qty.toFixed(2));
        $wrap.find("#modal-reim-sum-amt").text(this.fmt_money(sum_amt));
        $wrap.find("#modal-reim-sum-tax").text(this.fmt_money(sum_tax));
        $wrap.find("#modal-reim-sum-total").text(this.fmt_money(sum_total));
    }

    async submit_create_reimbursement(dialog) {
        const $wrap = dialog.$wrapper;
        const company = $wrap.find("#modal-reim-company").val();
        const employee = $wrap.find("#modal-reim-employee").val().trim();
        const supplier = $wrap.find("#modal-reim-supplier").val().trim();
        const bill_no = $wrap.find("#modal-reim-invoice-no").val().trim();
        const invoice_type = $wrap.find("#modal-reim-invoice-type").val();
        const bill_date = $wrap.find("#modal-reim-date").val();
        const auto_receive_stock = $wrap.find("#modal-reim-auto-stock").is(":checked") ? 1 : 0;

        const items = [];
        let has_zero_error = false;

        $wrap.find("#modal-reim-items-tbody tr").each(function (idx) {
            const item_code = $(this).find(".reim-item-code").val().trim();
            const item_name = $(this).find(".reim-item-name").val().trim();
            const spec = $(this).find(".reim-item-spec").val().trim();
            const uom = $(this).find(".reim-item-uom").val().trim();
            const qty = flt($(this).find(".reim-item-qty").val());
            const rate = flt($(this).find(".reim-item-rate").val());
            const tax_rate = flt($(this).find(".reim-item-tax-rate").val());
            const amount = flt($(this).find(".reim-item-amt").val());
            const tax_amount = flt($(this).find(".reim-item-tax-amt").val());
            const total_amount = flt($(this).find(".reim-item-total").val());
            const remarks = $(this).find(".reim-item-remarks").val().trim();

            if (!item_code) return;

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
            frappe.msgprint(__("请至少添加一行有效的报销明细！"));
            return;
        }

        try {
            frappe.dom.freeze(__("正在全自动生成全链路单据 (PO+PR+PI+RR)..."));
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.reimbursement_picker_service.create_self_service_reimbursement_bundle",
                args: {
                    company,
                    employee,
                    supplier,
                    bill_no,
                    bill_date,
                    invoice_type,
                    auto_receive_stock,
                    items,
                },
            });
            frappe.dom.unfreeze();

            if (r.message && r.message.success) {
                dialog.hide();
                frappe.show_alert({
                    message: `🎉 成功生成报销申请全链路单据！报销单：${r.message.rr_name}`,
                    indicator: "green",
                }, 5);

                this.refresh_all();
                this.show_doc_detail_modal("Reimbursement Request", r.message.rr_name);
            }
        } catch (e) {
            frappe.dom.unfreeze();
            console.error("Failed to create reimbursement bundle:", e);
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

            const items_tbody = (doc.items || []).map((it) => `
                <tr>
                    <td class="text-center font-bold">${it.idx}</td>
                    <td><strong>${frappe.utils.escape_html(it.item_code)}</strong></td>
                    <td>${frappe.utils.escape_html(it.item_name)}</td>
                    <td>${frappe.utils.escape_html(it.spec || "-")}</td>
                    <td>${frappe.utils.escape_html(it.uom)}</td>
                    <td class="text-right">${flt(it.qty).toFixed(2)}</td>
                    <td class="text-right qifu-money-cell">${this.fmt_money(it.rate)}</td>
                    <td class="text-right qifu-money-cell">${this.fmt_money(it.amount)}</td>
                    <td class="text-right">${it.tax_rate}%</td>
                    <td class="text-right qifu-money-cell">${this.fmt_money(it.tax_amount)}</td>
                    <td class="text-right qifu-money-cell font-bold text-primary">${this.fmt_money(it.total_amount)}</td>
                    <td>${frappe.utils.escape_html(it.description || "-")}</td>
                </tr>
            `).join("");

            const html = `
                <div class="picker-detail-modal-root">
                    <div class="picker-detail-hdr-grid">
                        <div class="picker-detail-hdr-card">
                            <span class="picker-detail-hdr-label">所属公司</span>
                            <span class="picker-detail-hdr-val">${frappe.utils.escape_html(doc.company)}</span>
                        </div>
                        <div class="picker-detail-hdr-card">
                            <span class="picker-detail-hdr-label">报销人/供应商</span>
                            <span class="picker-detail-hdr-val">${frappe.utils.escape_html(doc.supplier || doc.owner)}</span>
                        </div>
                        <div class="picker-detail-hdr-card">
                            <span class="picker-detail-hdr-label">经手人</span>
                            <span class="picker-detail-hdr-val">${frappe.utils.escape_html(doc.owner)}</span>
                        </div>
                        <div class="picker-detail-hdr-card">
                            <span class="picker-detail-hdr-label">单据总额</span>
                            <span class="picker-detail-hdr-val text-primary font-bold">${this.fmt_money(doc.total_amount || doc.grand_total)}</span>
                        </div>
                    </div>

                    <div class="picker-detail-table-wrap">
                        <table class="picker-data-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>物料/项目</th>
                                    <th>名称说明</th>
                                    <th>规格型号</th>
                                    <th>单位</th>
                                    <th class="text-right">数量</th>
                                    <th class="text-right">单价</th>
                                    <th class="text-right">金额</th>
                                    <th class="text-right">税率</th>
                                    <th class="text-right">税额</th>
                                    <th class="text-right">价税合计</th>
                                    <th>备注/用途</th>
                                </tr>
                            </thead>
                            <tbody>${items_tbody}</tbody>
                            <tfoot>
                                <tr>
                                    <td colspan="5" class="text-right font-bold">合计:</td>
                                    <td class="text-right font-bold">${flt(doc.total_qty).toFixed(2)}</td>
                                    <td></td>
                                    <td class="text-right qifu-money-cell font-bold">${this.fmt_money(doc.total_amount || doc.grand_total)}</td>
                                    <td></td>
                                    <td></td>
                                    <td class="text-right qifu-money-cell font-bold text-primary">${this.fmt_money(doc.total_amount || doc.grand_total)}</td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            `;

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

            d.fields_dict.detail_html.$wrapper.html(html);
            d.show();
        } catch (e) {
            frappe.dom.unfreeze();
            console.error("Failed to load document details:", e);
        }
    }
}
