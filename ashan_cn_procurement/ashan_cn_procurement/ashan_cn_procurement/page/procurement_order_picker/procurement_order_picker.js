// Copyright (c) 2026, Ashan CN Procurement and contributors
// Procurement Order Selection & Downstream Document Generation Hub

frappe.pages["procurement-order-picker"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("采购选单生单中心"),
        single_column: true,
    });
    new ProcurementOrderPickerCenter(page);
};

class ProcurementOrderPickerCenter {
    constructor(page) {
        this.page = page;
        this.active_stage = "mr_to_po"; // mr_to_po, po_to_pr, pr_to_pi, pi_to_rr
        this.company = frappe.defaults.get_user_default("Company") || "";
        this.companies = [];
        this.kpis = {};
        this.table_data = [];
        this.selected_map = new Map(); // key -> row object with current input qty
        this.filters = {
            mr_to_po: { supplier: "", department: "", item_code: "", from_date: "", to_date: "" },
            po_to_pr: { supplier: "", warehouse: "", po_name: "", item_code: "" },
            pr_to_pi: { supplier: "", pr_name: "", item_code: "" },
            pi_to_rr: { supplier: "", bill_no: "", owner: "" },
        };
        this.loading = false;

        this.init_dom();
        this.bind_events();
        this.parse_route_params();
        this.load_companies();
    }

    parse_route_params() {
        const route = frappe.get_route();
        const stage_map = {
            "mr_to_po": "mr_to_po",
            "po": "mr_to_po",
            "po_to_pr": "po_to_pr",
            "pr": "po_to_pr",
            "pr_to_pi": "pr_to_pi",
            "pi": "pr_to_pi",
            "pi_to_rr": "pi_to_rr",
            "rr": "pi_to_rr",
            "reimbursement": "pi_to_rr",
        };
        if (route && route.length > 1 && stage_map[route[1]]) {
            this.active_stage = stage_map[route[1]];
        }
        const query_params = frappe.utils.get_query_params();
        if (query_params && query_params.stage && stage_map[query_params.stage]) {
            this.active_stage = stage_map[query_params.stage];
        }
    }

    init_dom() {
        const $main = $(this.page.main);
        $main.html(`
            <div class="picker-page-container">
                <!-- Top Toolbar & Company Chips -->
                <div class="picker-top-bar">
                    <div class="picker-title-group">
                        <h2>🛒 采购选单生单中心</h2>
                        <div class="picker-subtitle">全链路待办明细池：采购需求 ➔ 采购订单 ➔ 采购入库 ➔ 采购发票 ➔ 报销申请</div>
                    </div>
                    <div class="picker-company-group">
                        <span class="picker-company-label">公司:</span>
                        <div class="picker-company-options"></div>
                    </div>
                </div>

                <!-- KPI Summary 4-Cards Grid -->
                <div class="picker-kpi-grid">
                    <div class="picker-kpi-card" data-stage="mr_to_po">
                        <div class="picker-kpi-info">
                            <div class="picker-kpi-stage-tag">阶段 1 · 需求转订单</div>
                            <div class="picker-kpi-name">待订货需求明细</div>
                            <div class="picker-kpi-value" id="kpi-mr-count">-</div>
                            <div class="picker-kpi-extra">已审批待采购物料</div>
                        </div>
                        <div class="picker-kpi-icon">📋</div>
                    </div>
                    <div class="picker-kpi-card" data-stage="po_to_pr">
                        <div class="picker-kpi-info">
                            <div class="picker-kpi-stage-tag">阶段 2 · 订单转入库</div>
                            <div class="picker-kpi-name">待收货订单明细</div>
                            <div class="picker-kpi-value" id="kpi-po-count">-</div>
                            <div class="picker-kpi-extra">已下达待入库订单</div>
                        </div>
                        <div class="picker-kpi-icon">📦</div>
                    </div>
                    <div class="picker-kpi-card" data-stage="pr_to_pi">
                        <div class="picker-kpi-info">
                            <div class="picker-kpi-stage-tag">阶段 3 · 入库转开票</div>
                            <div class="picker-kpi-name">待开票入库明细</div>
                            <div class="picker-kpi-value" id="kpi-pr-count">-</div>
                            <div class="picker-kpi-extra">已收货待结算发票</div>
                        </div>
                        <div class="picker-kpi-icon">🧾</div>
                    </div>
                    <div class="picker-kpi-card" data-stage="pi_to_rr">
                        <div class="picker-kpi-info">
                            <div class="picker-kpi-stage-tag">阶段 4 · 发票转报销</div>
                            <div class="picker-kpi-name">待报销付款发票</div>
                            <div class="picker-kpi-value" id="kpi-pi-count">-</div>
                            <div class="picker-kpi-extra" id="kpi-pi-amount">-</div>
                        </div>
                        <div class="picker-kpi-icon">💰</div>
                    </div>
                </div>

                <!-- Stage Nav Tabs -->
                <div class="picker-nav-tabs">
                    <button type="button" class="picker-tab-btn" data-stage="mr_to_po">
                        <span>📋 采购订货选单 (需求 ➔ 订单)</span>
                        <span class="badge-pill" id="tab-badge-mr">0</span>
                    </button>
                    <button type="button" class="picker-tab-btn" data-stage="po_to_pr">
                        <span>📦 采购入库选单 (订单 ➔ 入库)</span>
                        <span class="badge-pill" id="tab-badge-po">0</span>
                    </button>
                    <button type="button" class="picker-tab-btn" data-stage="pr_to_pi">
                        <span>🧾 采购开票选单 (入库 ➔ 发票)</span>
                        <span class="badge-pill" id="tab-badge-pr">0</span>
                    </button>
                    <button type="button" class="picker-tab-btn" data-stage="pi_to_rr">
                        <span>💰 报销申请选单 (发票 ➔ 报销)</span>
                        <span class="badge-pill" id="tab-badge-pi">0</span>
                    </button>
                </div>

                <!-- Stage Filter Toolbar -->
                <div class="picker-filter-panel"></div>

                <!-- Batch Action Toolbar -->
                <div class="picker-action-bar">
                    <div class="picker-selection-stats">
                        <span>已选 <strong id="stat-selected-count">0</strong> 行明细</span>
                        <span id="stat-selected-sum-wrap">| 本次总计: <strong id="stat-selected-amount">¥ 0.00</strong></span>
                    </div>
                    <div class="picker-batch-controls">
                        <button type="button" class="picker-btn picker-btn-default btn-select-all">全选本页</button>
                        <button type="button" class="picker-btn picker-btn-default btn-deselect-all">清空选择</button>
                        <button type="button" class="picker-btn picker-btn-default btn-fill-max">填充最大待办数</button>
                        <div class="picker-stage-extra-inputs"></div>
                        <button type="button" class="picker-btn picker-btn-success btn-generate">
                            <span>⚡ 一键生单</span>
                        </button>
                    </div>
                </div>

                <!-- Data Table Card with Dual Scrollbar & Freeze Panes -->
                <div class="picker-grid-card">
                    <div class="picker-top-scrollbar-track">
                        <div class="picker-top-scrollbar-thumb"></div>
                    </div>
                    <div class="picker-table-wrapper">
                        <table class="picker-data-table">
                            <thead></thead>
                            <tbody></tbody>
                            <tfoot></tfoot>
                        </table>
                    </div>
                </div>
            </div>
        `);

        this.$wrapper = $main.find(".picker-page-container");
    }

    bind_events() {
        const self = this;

        // KPI card click & tab switch
        this.$wrapper.on("click", ".picker-kpi-card, .picker-tab-btn", function () {
            const stage = $(this).data("stage");
            if (stage && stage !== self.active_stage) {
                self.switch_stage(stage);
            }
        });

        // Company chip click
        this.$wrapper.on("click", ".picker-company-chip", function () {
            if (self.loading) return;
            self.company = $(this).data("company");
            self.render_companies();
            self.load_all();
        });

        // Filter inputs change
        this.$wrapper.on("input change", ".picker-filter-control", function () {
            const field = $(this).data("field");
            self.filters[self.active_stage][field] = $(this).val();
            clearTimeout(self._filter_debounce);
            self._filter_debounce = setTimeout(() => self.load_stage_data(), 300);
        });

        // Row checkbox click
        this.$wrapper.on("change", ".picker-row-checkbox", function () {
            const rowKey = $(this).data("key");
            const checked = $(this).prop("checked");
            const $tr = $(this).closest("tr");
            if (checked) {
                $tr.addClass("is-selected");
                const rowData = self.get_row_by_key(rowKey);
                if (rowData) {
                    const inputQty = flt($tr.find(".picker-qty-input").val()) || rowData.pending_qty || rowData.net_available_amount || 0;
                    self.selected_map.set(rowKey, { ...rowData, this_qty: inputQty, this_amount: inputQty });
                }
            } else {
                $tr.removeClass("is-selected");
                self.selected_map.delete(rowKey);
            }
            self.update_selection_stats();
        });

        // Editable input change in row
        this.$wrapper.on("input change", ".picker-qty-input", function () {
            const rowKey = $(this).data("key");
            const val = flt($(this).val());
            const $tr = $(this).closest("tr");
            const rowData = self.get_row_by_key(rowKey);
            if (rowData) {
                rowData.this_qty = val;
                rowData.this_amount = val;
                if (self.selected_map.has(rowKey)) {
                    const sel = self.selected_map.get(rowKey);
                    sel.this_qty = val;
                    sel.this_amount = val;
                }
            }
            self.update_selection_stats();
        });

        // Select all / Deselect all
        this.$wrapper.on("click", ".btn-select-all", () => self.select_all_rows(true));
        this.$wrapper.on("click", ".btn-deselect-all", () => self.select_all_rows(false));

        // Fill max pending qty
        this.$wrapper.on("click", ".btn-fill-max", () => self.fill_max_quantities());

        // Generate Action Button
        this.$wrapper.on("click", ".btn-generate", () => self.handle_generate_action());

        // Dual Scrollbars Sync
        const $topScroll = this.$wrapper.find(".picker-top-scrollbar-track");
        const $tableWrapper = this.$wrapper.find(".picker-table-wrapper");

        $topScroll.on("scroll", function () {
            if (!self._syncing_scroll) {
                self._syncing_scroll = true;
                $tableWrapper.scrollLeft($(this).scrollLeft());
                self._syncing_scroll = false;
            }
        });

        $tableWrapper.on("scroll", function () {
            if (!self._syncing_scroll) {
                self._syncing_scroll = true;
                $topScroll.scrollLeft($(this).scrollLeft());
                self._syncing_scroll = false;
            }
        });

        $(window).on("resize", () => self.adjust_table_height());
        this.page.set_secondary_action(__("刷新"), () => self.load_all(), "refresh");
    }

    load_companies() {
        frappe.db.get_list("Company", {
            fields: ["name"],
            order_by: "name asc",
            limit: 50,
        }).then((rows) => {
            this.companies = rows || [];
            if (!this.company && this.companies.length) {
                this.company = this.companies[0].name;
            }
            this.render_companies();
            this.load_all();
        }).catch(() => {
            this.load_all();
        });
    }

    render_companies() {
        const $opts = this.$wrapper.find(".picker-company-options").empty();
        this.companies.forEach((c) => {
            const active = c.name === this.company ? "active" : "";
            $opts.append(`
                <button type="button" class="picker-company-chip ${active}" data-company="${frappe.utils.escape_html(c.name)}">
                    ${frappe.utils.escape_html(c.name)}
                </button>
            `);
        });
    }

    switch_stage(stage) {
        this.active_stage = stage;
        this.selected_map.clear();
        this.update_stage_ui();
        this.render_filters();
        this.render_stage_extra_controls();
        this.load_stage_data();
    }

    update_stage_ui() {
        this.$wrapper.find(".picker-kpi-card").removeClass("active");
        this.$wrapper.find(`.picker-kpi-card[data-stage="${this.active_stage}"]`).addClass("active");

        this.$wrapper.find(".picker-tab-btn").removeClass("active");
        this.$wrapper.find(`.picker-tab-btn[data-stage="${this.active_stage}"]`).addClass("active");

        const stage_titles = {
            mr_to_po: "⚡ 生成采购订单草稿",
            po_to_pr: "⚡ 生成采购入库单草稿",
            pr_to_pi: "⚡ 生成采购发票草稿",
            pi_to_rr: "⚡ 生成报销申请单草稿",
        };
        this.$wrapper.find(".btn-generate span").text(stage_titles[this.active_stage] || "⚡ 一键生单");
    }

    render_filters() {
        const $panel = this.$wrapper.find(".picker-filter-panel").empty();
        const f = this.filters[this.active_stage];

        if (this.active_stage === "mr_to_po") {
            $panel.html(`
                <div class="picker-filter-item">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="item_code" value="${frappe.utils.escape_html(f.item_code || "")}" placeholder="搜索物料…">
                </div>
                <div class="picker-filter-item">
                    <label>建议供应商:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="supplier" value="${frappe.utils.escape_html(f.supplier || "")}" placeholder="供应商名称…">
                </div>
                <div class="picker-filter-item">
                    <label>申请部门:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="department" value="${frappe.utils.escape_html(f.department || "")}" placeholder="部门…">
                </div>
                <div class="picker-filter-item">
                    <label>申请日期:</label>
                    <input type="date" class="picker-input picker-filter-control" data-field="from_date" value="${f.from_date || ""}">
                    <span>至</span>
                    <input type="date" class="picker-input picker-filter-control" data-field="to_date" value="${f.to_date || ""}">
                </div>
            `);
        } else if (this.active_stage === "po_to_pr") {
            $panel.html(`
                <div class="picker-filter-item">
                    <label>供应商:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="supplier" value="${frappe.utils.escape_html(f.supplier || "")}" placeholder="搜索供应商…">
                </div>
                <div class="picker-filter-item">
                    <label>采购订单号:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="po_name" value="${frappe.utils.escape_html(f.po_name || "")}" placeholder="PO-...">
                </div>
                <div class="picker-filter-item">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="item_code" value="${frappe.utils.escape_html(f.item_code || "")}" placeholder="物料…">
                </div>
                <div class="picker-filter-item">
                    <label>收货仓库:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="warehouse" value="${frappe.utils.escape_html(f.warehouse || "")}" placeholder="仓库名称…">
                </div>
            `);
        } else if (this.active_stage === "pr_to_pi") {
            $panel.html(`
                <div class="picker-filter-item">
                    <label>供应商:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="supplier" value="${frappe.utils.escape_html(f.supplier || "")}" placeholder="搜索供应商…">
                </div>
                <div class="picker-filter-item">
                    <label>入库单号:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="pr_name" value="${frappe.utils.escape_html(f.pr_name || "")}" placeholder="MAT-PRE-...">
                </div>
                <div class="picker-filter-item">
                    <label>物料搜索:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="item_code" value="${frappe.utils.escape_html(f.item_code || "")}" placeholder="物料编码/描述…">
                </div>
            `);
        } else if (this.active_stage === "pi_to_rr") {
            $panel.html(`
                <div class="picker-filter-item">
                    <label>供应商:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="supplier" value="${frappe.utils.escape_html(f.supplier || "")}" placeholder="搜索供应商…">
                </div>
                <div class="picker-filter-item">
                    <label>发票号码:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="bill_no" value="${frappe.utils.escape_html(f.bill_no || "")}" placeholder="发票代码/号码…">
                </div>
                <div class="picker-filter-item">
                    <label>经手人:</label>
                    <input type="text" class="picker-input picker-filter-control" data-field="owner" value="${frappe.utils.escape_html(f.owner || "")}" placeholder="录单人…">
                </div>
            `);
        }
    }

    render_stage_extra_controls() {
        const $extra = this.$wrapper.find(".picker-stage-extra-inputs").empty();
        if (this.active_stage === "mr_to_po") {
            $extra.html(`
                <input type="text" class="picker-input extra-supplier-override" placeholder="统一指定供应商(可选)">
            `);
        } else if (this.active_stage === "po_to_pr") {
            $extra.html(`
                <input type="text" class="picker-input extra-warehouse-override" placeholder="统一指定入库仓库(可选)">
            `);
        } else if (this.active_stage === "pr_to_pi") {
            $extra.html(`
                <input type="text" class="picker-input extra-bill-no" placeholder="输入发票号码">
                <input type="date" class="picker-input extra-bill-date">
            `);
        } else if (this.active_stage === "pi_to_rr") {
            $extra.html(`
                <input type="text" class="picker-input extra-applicant" placeholder="报销申请人(邮箱/员工)">
            `);
        }
    }

    load_all() {
        this.load_kpis();
        this.update_stage_ui();
        this.render_filters();
        this.render_stage_extra_controls();
        this.load_stage_data();
    }

    load_kpis() {
        frappe.call({
            method: "ashan_cn_procurement.services.procurement_picker_service.get_procurement_picker_overview_kpis",
            args: { company: this.company },
            callback: (r) => {
                const kpis = (r.message || {}).kpis || {};
                this.kpis = kpis;
                $("#kpi-mr-count").text(kpis.mr_to_po?.count ?? 0);
                $("#kpi-po-count").text(kpis.po_to_pr?.count ?? 0);
                $("#kpi-pr-count").text(kpis.pr_to_pi?.count ?? 0);
                $("#kpi-pi-count").text(kpis.pi_to_rr?.count ?? 0);
                $("#kpi-pi-amount").text("待报销: " + format_currency(kpis.pi_to_rr?.amount || 0, "CNY"));

                $("#tab-badge-mr").text(kpis.mr_to_po?.count ?? 0);
                $("#tab-badge-po").text(kpis.po_to_pr?.count ?? 0);
                $("#tab-badge-pr").text(kpis.pr_to_pi?.count ?? 0);
                $("#tab-badge-pi").text(kpis.pi_to_rr?.count ?? 0);
            }
        });
    }

    load_stage_data() {
        this.loading = true;
        const method_map = {
            mr_to_po: "ashan_cn_procurement.services.procurement_picker_service.get_pending_material_request_items",
            po_to_pr: "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_order_items",
            pr_to_pi: "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_receipt_items",
            pi_to_rr: "ashan_cn_procurement.services.procurement_picker_service.get_pending_reimbursement_invoices",
        };

        const current_method = method_map[this.active_stage];
        const current_filters = this.filters[this.active_stage];

        const $tbody = this.$wrapper.find(".picker-data-table tbody");
        $tbody.html(`<tr><td colspan="15" class="picker-empty-state">⏳ 正在加载待办选单明细池…</td></tr>`);

        frappe.call({
            method: current_method,
            args: {
                company: this.company,
                filters: current_filters,
            },
            callback: (r) => {
                this.loading = false;
                const data = r.message || {};
                this.table_data = data.rows || [];
                this.render_table();
                this.update_selection_stats();
                this.adjust_table_height();
            },
            error: () => {
                this.loading = false;
                $tbody.html(`<tr><td colspan="15" class="picker-empty-state">❌ 数据加载失败，请重试。</td></tr>`);
            }
        });
    }

    get_row_key(row) {
        if (this.active_stage === "mr_to_po") return row.mri_name;
        if (this.active_stage === "po_to_pr") return row.poi_name;
        if (this.active_stage === "pr_to_pi") return row.pri_name;
        if (this.active_stage === "pi_to_rr") return row.pi_name;
        return row.name;
    }

    get_row_by_key(key) {
        return this.table_data.find((r) => this.get_row_key(r) === key);
    }

    render_table() {
        const $thead = this.$wrapper.find(".picker-data-table thead").empty();
        const $tbody = this.$wrapper.find(".picker-data-table tbody").empty();
        const $tfoot = this.$wrapper.find(".picker-data-table tfoot").empty();

        if (this.active_stage === "mr_to_po") {
            this.render_mr_to_po_table($thead, $tbody, $tfoot);
        } else if (this.active_stage === "po_to_pr") {
            this.render_po_to_pr_table($thead, $tbody, $tfoot);
        } else if (this.active_stage === "pr_to_pi") {
            this.render_pr_to_pi_table($thead, $tbody, $tfoot);
        } else if (this.active_stage === "pi_to_rr") {
            this.render_pi_to_rr_table($thead, $tbody, $tfoot);
        }

        // Adjust top scrollbar track width
        const tableWidth = this.$wrapper.find(".picker-data-table").outerWidth();
        this.$wrapper.find(".picker-top-scrollbar-thumb").css("width", tableWidth + "px");
    }

    render_mr_to_po_table($thead, $tbody, $tfoot) {
        $thead.html(`
            <tr>
                <th class="picker-sticky-1"><span class="picker-th-pill">序号</span><span class="picker-th-title">#</span></th>
                <th class="picker-sticky-2"><span class="picker-th-pill">选择</span><span class="picker-th-title">勾选</span></th>
                <th class="picker-sticky-3"><span class="picker-th-pill">申请单号</span><span class="picker-th-title">采购需求单</span></th>
                <th><span class="picker-th-pill">需求交期</span><span class="picker-th-title">期望到货</span></th>
                <th><span class="picker-th-pill">部门/申请人</span><span class="picker-th-title">需求部门</span></th>
                <th><span class="picker-th-pill">物料编码</span><span class="picker-th-title">物料代码</span></th>
                <th><span class="picker-th-pill">物料名称/规格</span><span class="picker-th-title">名称规格</span></th>
                <th><span class="picker-th-pill">单位</span><span class="picker-th-title">单位</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">申请数</span><span class="picker-th-title">总数量</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">已订数</span><span class="picker-th-title">已订</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">待订数</span><span class="picker-th-title">未订数量</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">本次订购</span><span class="picker-th-title">本次下单数</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">参考单价</span><span class="picker-th-title">单价</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">预估金额</span><span class="picker-th-title">金额</span></th>
                <th><span class="picker-th-pill">建议供应商</span><span class="picker-th-title">供应商</span></th>
            </tr>
        `);

        if (!this.table_data.length) {
            $tbody.html(`<tr><td colspan="15" class="picker-empty-state"><div class="picker-empty-icon">🎉</div>没有待订货的采购申请明细</td></tr>`);
            return;
        }

        let sum_pending_qty = 0;
        let sum_amount = 0;

        this.table_data.forEach((row, idx) => {
            const key = row.mri_name;
            const isSelected = this.selected_map.has(key);
            const thisQty = isSelected ? this.selected_map.get(key).this_qty : row.pending_qty;

            sum_pending_qty += row.pending_qty;
            sum_amount += row.estimated_amount;

            let badgeHtml = "";
            if (row.is_overdue) {
                badgeHtml = `<span class="picker-badge-overdue">已超期</span> `;
            } else if (row.is_urgent) {
                badgeHtml = `<span class="picker-badge-urgent">急需</span> `;
            }

            $tbody.append(`
                <tr class="${isSelected ? "is-selected" : ""}" data-key="${key}">
                    <td class="picker-sticky-1">${idx + 1}</td>
                    <td class="picker-sticky-2">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${key}" ${isSelected ? "checked" : ""}>
                    </td>
                    <td class="picker-sticky-3">
                        <a href="/app/material-request/${encodeURIComponent(row.mr_name)}" target="_blank"><strong>${row.mr_name}</strong></a>
                        <div class="picker-subtitle">第 ${row.idx} 行</div>
                    </td>
                    <td>${badgeHtml}${row.schedule_date || "-"}</td>
                    <td>${row.department || "-"} / ${row.requested_by || "-"}</td>
                    <td><code>${row.item_code}</code></td>
                    <td><strong>${row.item_name}</strong><br><small class="text-muted">${row.description || ""}</small></td>
                    <td>${row.uom || "-"}</td>
                    <td class="ashan-money-cell">${row.qty}</td>
                    <td class="ashan-money-cell">${row.ordered_qty}</td>
                    <td class="ashan-money-cell"><strong>${row.pending_qty}</strong></td>
                    <td class="ashan-money-cell">
                        <input type="number" step="any" class="picker-cell-input picker-qty-input" data-key="${key}" value="${thisQty}" max="${row.pending_qty}" min="0.001">
                    </td>
                    <td class="ashan-money-cell">${format_currency(row.rate, "CNY")}</td>
                    <td class="ashan-money-cell">${format_currency(row.estimated_amount, "CNY")}</td>
                    <td>${row.supplier ? `<strong>${row.supplier}</strong>` : `<span class="text-muted">待指定</span>`}</td>
                </tr>
            `);
        });

        $tfoot.html(`
            <tr class="picker-sticky-foot">
                <td colspan="8" class="text-right"><strong>合计 (共 ${this.table_data.length} 行)</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="ashan-money-cell"><strong>${sum_pending_qty.toFixed(2)}</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="ashan-money-cell"><strong>${format_currency(sum_amount, "CNY")}</strong></td>
                <td></td>
            </tr>
        `);
    }

    render_po_to_pr_table($thead, $tbody, $tfoot) {
        $thead.html(`
            <tr>
                <th class="picker-sticky-1"><span class="picker-th-pill">序号</span><span class="picker-th-title">#</span></th>
                <th class="picker-sticky-2"><span class="picker-th-pill">选择</span><span class="picker-th-title">勾选</span></th>
                <th class="picker-sticky-3"><span class="picker-th-pill">供应商</span><span class="picker-th-title">供应商</span></th>
                <th><span class="picker-th-pill">采购订单</span><span class="picker-th-title">订单单号</span></th>
                <th><span class="picker-th-pill">下单日期</span><span class="picker-th-title">订单日期</span></th>
                <th><span class="picker-th-pill">交期状态</span><span class="picker-th-title">承诺交期</span></th>
                <th><span class="picker-th-pill">物料编码/名称</span><span class="picker-th-title">物料描述</span></th>
                <th><span class="picker-th-pill">目的仓库</span><span class="picker-th-title">默认仓库</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">订单数量</span><span class="picker-th-title">订购总数</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">已收数量</span><span class="picker-th-title">已收</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">待收数量</span><span class="picker-th-title">未收数量</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">本次实收</span><span class="picker-th-title">本次到货数</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">单价</span><span class="picker-th-title">采购单价</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">待收金额</span><span class="picker-th-title">未收金额</span></th>
            </tr>
        `);

        if (!this.table_data.length) {
            $tbody.html(`<tr><td colspan="14" class="picker-empty-state"><div class="picker-empty-icon">📦</div>没有待收货的采购订单明细</td></tr>`);
            return;
        }

        let sum_pending_qty = 0;
        let sum_amount = 0;

        this.table_data.forEach((row, idx) => {
            const key = row.poi_name;
            const isSelected = this.selected_map.has(key);
            const thisQty = isSelected ? this.selected_map.get(key).this_qty : row.pending_qty;

            sum_pending_qty += row.pending_qty;
            sum_amount += row.pending_amount;

            $tbody.append(`
                <tr class="${isSelected ? "is-selected" : ""}" data-key="${key}">
                    <td class="picker-sticky-1">${idx + 1}</td>
                    <td class="picker-sticky-2">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${key}" ${isSelected ? "checked" : ""}>
                    </td>
                    <td class="picker-sticky-3"><strong>${row.supplier}</strong></td>
                    <td><a href="/app/purchase-order/${encodeURIComponent(row.po_name)}" target="_blank">${row.po_name}</a></td>
                    <td>${row.po_date || "-"}</td>
                    <td>${row.is_overdue ? `<span class="picker-badge-overdue">已超期</span> ` : ""}${row.schedule_date || "-"}</td>
                    <td><code>${row.item_code}</code> <strong>${row.item_name}</strong></td>
                    <td>${row.warehouse || "-"}</td>
                    <td class="ashan-money-cell">${row.qty}</td>
                    <td class="ashan-money-cell">${row.received_qty}</td>
                    <td class="ashan-money-cell"><strong>${row.pending_qty}</strong></td>
                    <td class="ashan-money-cell">
                        <input type="number" step="any" class="picker-cell-input picker-qty-input" data-key="${key}" value="${thisQty}" max="${row.pending_qty}" min="0.001">
                    </td>
                    <td class="ashan-money-cell">${format_currency(row.rate, "CNY")}</td>
                    <td class="ashan-money-cell">${format_currency(row.pending_amount, "CNY")}</td>
                </tr>
            `);
        });

        $tfoot.html(`
            <tr class="picker-sticky-foot">
                <td colspan="8" class="text-right"><strong>合计 (共 ${this.table_data.length} 行)</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="ashan-money-cell"><strong>${sum_pending_qty.toFixed(2)}</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="ashan-money-cell"><strong>${format_currency(sum_amount, "CNY")}</strong></td>
            </tr>
        `);
    }

    render_pr_to_pi_table($thead, $tbody, $tfoot) {
        $thead.html(`
            <tr>
                <th class="picker-sticky-1"><span class="picker-th-pill">序号</span><span class="picker-th-title">#</span></th>
                <th class="picker-sticky-2"><span class="picker-th-pill">选择</span><span class="picker-th-title">勾选</span></th>
                <th class="picker-sticky-3"><span class="picker-th-pill">供应商</span><span class="picker-th-title">供应商</span></th>
                <th><span class="picker-th-pill">采购入库单</span><span class="picker-th-title">入库单号</span></th>
                <th><span class="picker-th-pill">入库日期</span><span class="picker-th-title">过账日期</span></th>
                <th><span class="picker-th-pill">物料编码/名称</span><span class="picker-th-title">物料描述</span></th>
                <th><span class="picker-th-pill">关联合同/订单</span><span class="picker-th-title">源采购订单</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">入库总数</span><span class="picker-th-title">收货数量</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">已开票数</span><span class="picker-th-title">已开票</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">待开票数</span><span class="picker-th-title">未开票数量</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">本次开票</span><span class="picker-th-title">本次开票数</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">单价</span><span class="picker-th-title">入库单价</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">待开票金额</span><span class="picker-th-title">暂估待开金额</span></th>
            </tr>
        `);

        if (!this.table_data.length) {
            $tbody.html(`<tr><td colspan="13" class="picker-empty-state"><div class="picker-empty-icon">🧾</div>没有待开票的采购入库明细</td></tr>`);
            return;
        }

        let sum_pending_qty = 0;
        let sum_amount = 0;

        this.table_data.forEach((row, idx) => {
            const key = row.pri_name;
            const isSelected = this.selected_map.has(key);
            const thisQty = isSelected ? this.selected_map.get(key).this_qty : row.pending_qty;

            sum_pending_qty += row.pending_qty;
            sum_amount += row.pending_amount;

            $tbody.append(`
                <tr class="${isSelected ? "is-selected" : ""}" data-key="${key}">
                    <td class="picker-sticky-1">${idx + 1}</td>
                    <td class="picker-sticky-2">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${key}" ${isSelected ? "checked" : ""}>
                    </td>
                    <td class="picker-sticky-3"><strong>${row.supplier}</strong></td>
                    <td><a href="/app/purchase-receipt/${encodeURIComponent(row.pr_name)}" target="_blank">${row.pr_name}</a></td>
                    <td>${row.pr_date || "-"}</td>
                    <td><code>${row.item_code}</code> <strong>${row.item_name}</strong></td>
                    <td>${row.purchase_order ? `<a href="/app/purchase-order/${encodeURIComponent(row.purchase_order)}" target="_blank">${row.purchase_order}</a>` : "-"}</td>
                    <td class="ashan-money-cell">${row.qty}</td>
                    <td class="ashan-money-cell">${row.billed_qty}</td>
                    <td class="ashan-money-cell"><strong>${row.pending_qty}</strong></td>
                    <td class="ashan-money-cell">
                        <input type="number" step="any" class="picker-cell-input picker-qty-input" data-key="${key}" value="${thisQty}" max="${row.pending_qty}" min="0.001">
                    </td>
                    <td class="ashan-money-cell">${format_currency(row.rate, "CNY")}</td>
                    <td class="ashan-money-cell">${format_currency(row.pending_amount, "CNY")}</td>
                </tr>
            `);
        });

        $tfoot.html(`
            <tr class="picker-sticky-foot">
                <td colspan="7" class="text-right"><strong>合计 (共 ${this.table_data.length} 行)</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="ashan-money-cell"><strong>${sum_pending_qty.toFixed(2)}</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="ashan-money-cell"><strong>${format_currency(sum_amount, "CNY")}</strong></td>
            </tr>
        `);
    }

    render_pi_to_rr_table($thead, $tbody, $tfoot) {
        $thead.html(`
            <tr>
                <th class="picker-sticky-1"><span class="picker-th-pill">序号</span><span class="picker-th-title">#</span></th>
                <th class="picker-sticky-2"><span class="picker-th-pill">选择</span><span class="picker-th-title">勾选</span></th>
                <th class="picker-sticky-3"><span class="picker-th-pill">发票单号</span><span class="picker-th-title">ERP发票号</span></th>
                <th><span class="picker-th-pill">供应商/销售方</span><span class="picker-th-title">供应商</span></th>
                <th><span class="picker-th-pill">纸质/金税发票号</span><span class="picker-th-title">发票号码</span></th>
                <th><span class="picker-th-pill">发票类型</span><span class="picker-th-title">票据类别</span></th>
                <th><span class="picker-th-pill">开票日期</span><span class="picker-th-title">开票日期</span></th>
                <th><span class="picker-th-pill">经办人</span><span class="picker-th-title">录单人</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">发票总额</span><span class="picker-th-title">含税总额</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">已付/已报额</span><span class="picker-th-title">已核销</span></th>
                <th class="ashan-money-cell"><span class="picker-th-pill">待报销余额</span><span class="picker-th-title">可报销应付</span></th>
            </tr>
        `);

        if (!this.table_data.length) {
            $tbody.html(`<tr><td colspan="11" class="picker-empty-state"><div class="picker-empty-icon">💰</div>没有待报销的采购发票</td></tr>`);
            return;
        }

        let sum_outstanding = 0;

        this.table_data.forEach((row, idx) => {
            const key = row.pi_name;
            const isSelected = this.selected_map.has(key);
            sum_outstanding += row.net_available_amount;

            $tbody.append(`
                <tr class="${isSelected ? "is-selected" : ""}" data-key="${key}">
                    <td class="picker-sticky-1">${idx + 1}</td>
                    <td class="picker-sticky-2">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${key}" ${isSelected ? "checked" : ""}>
                    </td>
                    <td class="picker-sticky-3">
                        <a href="/app/purchase-invoice/${encodeURIComponent(row.pi_name)}" target="_blank"><strong>${row.pi_name}</strong></a>
                    </td>
                    <td><strong>${row.supplier}</strong></td>
                    <td><code>${row.bill_no || "未填"}</code></td>
                    <td><span class="badge badge-info">${row.invoice_type}</span></td>
                    <td>${row.bill_date || row.posting_date || "-"}</td>
                    <td>${row.owner || "-"}</td>
                    <td class="ashan-money-cell">${format_currency(row.grand_total, "CNY")}</td>
                    <td class="ashan-money-cell">${format_currency(row.grand_total - row.outstanding_amount, "CNY")}</td>
                    <td class="ashan-money-cell"><strong>${format_currency(row.net_available_amount, "CNY")}</strong></td>
                </tr>
            `);
        });

        $tfoot.html(`
            <tr class="picker-sticky-foot">
                <td colspan="8" class="text-right"><strong>合计 (共 ${this.table_data.length} 张发票)</strong></td>
                <td>-</td>
                <td>-</td>
                <td class="ashan-money-cell"><strong>${format_currency(sum_outstanding, "CNY")}</strong></td>
            </tr>
        `);
    }

    select_all_rows(selectAll) {
        this.selected_map.clear();
        const $trs = this.$wrapper.find(".picker-data-table tbody tr");
        if (selectAll) {
            this.table_data.forEach((row) => {
                const key = this.get_row_key(row);
                const qty = row.pending_qty || row.net_available_amount || 0;
                this.selected_map.set(key, { ...row, this_qty: qty, this_amount: qty });
            });
            $trs.addClass("is-selected").find(".picker-row-checkbox").prop("checked", true);
        } else {
            $trs.removeClass("is-selected").find(".picker-row-checkbox").prop("checked", false);
        }
        this.update_selection_stats();
    }

    fill_max_quantities() {
        this.table_data.forEach((row) => {
            const key = this.get_row_key(row);
            const maxVal = row.pending_qty || row.net_available_amount || 0;
            row.this_qty = maxVal;
            row.this_amount = maxVal;
            this.$wrapper.find(`.picker-qty-input[data-key="${key}"]`).val(maxVal);
            if (this.selected_map.has(key)) {
                const sel = this.selected_map.get(key);
                sel.this_qty = maxVal;
                sel.this_amount = maxVal;
            }
        });
        this.update_selection_stats();
        frappe.show_alert({ message: __("已填充全部待办最大数量"), indicator: "green" });
    }

    update_selection_stats() {
        const count = this.selected_map.size;
        $("#stat-selected-count").text(count);

        let totalAmt = 0;
        this.selected_map.forEach((item) => {
            if (this.active_stage === "mr_to_po") {
                totalAmt += (flt(item.this_qty) * flt(item.rate)) || 0;
            } else if (this.active_stage === "po_to_pr") {
                totalAmt += (flt(item.this_qty) * flt(item.rate)) || 0;
            } else if (this.active_stage === "pr_to_pi") {
                totalAmt += (flt(item.this_qty) * flt(item.rate)) || 0;
            } else if (this.active_stage === "pi_to_rr") {
                totalAmt += flt(item.net_available_amount) || 0;
            }
        });

        $("#stat-selected-amount").text(format_currency(totalAmt, "CNY"));
    }

    adjust_table_height() {
        const topOffset = this.$wrapper.find(".picker-grid-card").offset()?.top || 300;
        const windowHeight = $(window).height();
        const availableHeight = Math.max(300, windowHeight - topOffset - 60);
        this.$wrapper.find(".picker-table-wrapper").css("max-height", availableHeight + "px");
    }

    handle_generate_action() {
        if (!this.selected_map.size) {
            frappe.msgprint(__("请至少勾选一行明细进行生单。"));
            return;
        }

        const selected_list = Array.from(this.selected_map.values());

        if (this.active_stage === "mr_to_po") {
            this.generate_po(selected_list);
        } else if (this.active_stage === "po_to_pr") {
            this.generate_pr(selected_list);
        } else if (this.active_stage === "pr_to_pi") {
            this.generate_pi(selected_list);
        } else if (this.active_stage === "pi_to_rr") {
            this.generate_rr(selected_list);
        }
    }

    generate_po(selected_list) {
        const supplier_override = this.$wrapper.find(".extra-supplier-override").val();
        frappe.confirm(__("确定将选中的 {0} 行采购需求生成采购订单？", [selected_list.length]), () => {
            frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_orders_from_mr_items",
                args: {
                    company: this.company,
                    selected_items: selected_list,
                    supplier_override: supplier_override || null,
                },
                freeze: true,
                freeze_message: __("正在生成采购订单草稿…"),
                callback: (r) => {
                    if (r.message && r.message.success) {
                        this.show_generation_success_dialog("采购订单", r.message.orders || []);
                        this.load_all();
                    }
                }
            });
        });
    }

    generate_pr(selected_list) {
        const warehouse_override = this.$wrapper.find(".extra-warehouse-override").val();
        frappe.confirm(__("确定将选中的 {0} 行采购订单明细生成采购入库单？", [selected_list.length]), () => {
            frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_receipts_from_po_items",
                args: {
                    company: this.company,
                    selected_items: selected_list,
                    warehouse_override: warehouse_override || null,
                },
                freeze: true,
                freeze_message: __("正在生成采购入库单草稿…"),
                callback: (r) => {
                    if (r.message && r.message.success) {
                        this.show_generation_success_dialog("采购入库单", r.message.receipts || []);
                        this.load_all();
                    }
                }
            });
        });
    }

    generate_pi(selected_list) {
        const bill_no = this.$wrapper.find(".extra-bill-no").val();
        const bill_date = this.$wrapper.find(".extra-bill-date").val();
        frappe.confirm(__("确定将选中的 {0} 行采购入库明细生成采购发票？", [selected_list.length]), () => {
            frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_invoices_from_pr_items",
                args: {
                    company: this.company,
                    selected_items: selected_list,
                    bill_no: bill_no || null,
                    bill_date: bill_date || null,
                },
                freeze: true,
                freeze_message: __("正在生成采购发票草稿…"),
                callback: (r) => {
                    if (r.message && r.message.success) {
                        this.show_generation_success_dialog("采购发票", r.message.invoices || []);
                        this.load_all();
                    }
                }
            });
        });
    }

    generate_rr(selected_list) {
        const applicant = this.$wrapper.find(".extra-applicant").val();
        const pi_names = selected_list.map((r) => r.pi_name);
        frappe.confirm(__("确定将选中的 {0} 张采购发票生成报销申请单？", [pi_names.length]), () => {
            frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.make_reimbursement_from_invoices",
                args: {
                    company: this.company,
                    selected_invoices: pi_names,
                    applicant: applicant || null,
                },
                freeze: true,
                freeze_message: __("正在生成报销申请单草稿…"),
                callback: (r) => {
                    if (r.message && r.message.success) {
                        const d = new frappe.ui.Dialog({
                            title: __("🎉 生单成功"),
                            fields: [{
                                fieldtype: "HTML",
                                fieldname: "html",
                                options: `
                                    <div class="picker-dialog-body">
                                        <p>已成功生成报销申请单草稿：</p>
                                        <div class="picker-dialog-highlight">
                                            <a href="/app/reimbursement-request/${encodeURIComponent(r.message.reimbursement_name)}">
                                                ${r.message.reimbursement_name} (金额: ${format_currency(r.message.total_amount, "CNY")})
                                            </a>
                                        </div>
                                    </div>
                                `
                            }],
                            primary_action_label: __("立即打开"),
                            primary_action: () => {
                                d.hide();
                                frappe.set_route("reimbursement-request", r.message.reimbursement_name);
                            }
                        });
                        d.show();
                        this.load_all();
                    }
                }
            });
        });
    }

    show_generation_success_dialog(docTypeLabel, docs) {
        const doctype_routes = {
            "采购订单": "purchase-order",
            "采购入库单": "purchase-receipt",
            "采购发票": "purchase-invoice",
        };
        const route_name = doctype_routes[docTypeLabel] || "purchase-order";

        const itemsHtml = docs.map((doc) => `
            <div class="picker-result-item">
                <div>
                    <span class="picker-result-link" data-route="${route_name}" data-name="${doc.name}">
                        ${doc.name}
                    </span>
                    <span class="text-muted">（供应商: ${doc.supplier || "-"} ｜ 共 ${doc.item_count || 0} 行明细）</span>
                </div>
                <div class="ashan-money-cell">
                    <strong>${format_currency(doc.grand_total || 0, "CNY")}</strong>
                </div>
            </div>
        `).join("");

        const d = new frappe.ui.Dialog({
            title: __("🎉 批量生单成功 (共 {0} 张{1})", [docs.length, docTypeLabel]),
            fields: [{
                fieldtype: "HTML",
                fieldname: "html",
                options: `
                    <div class="picker-dialog-body">
                        <p class="picker-dialog-success-tip">已成功在系统中建立草稿单据，可直接点击单号进入查看并审核：</p>
                        <div class="picker-dialog-scroll-list">
                            ${itemsHtml}
                        </div>
                    </div>
                `
            }],
            primary_action_label: __("完成"),
            primary_action: () => d.hide(),
        });

        d.$wrapper.on("click", ".picker-result-link", function () {
            const dt = $(this).data("route");
            const nm = $(this).data("name");
            d.hide();
            frappe.set_route(dt, nm);
        });

        d.show();
    }
}
