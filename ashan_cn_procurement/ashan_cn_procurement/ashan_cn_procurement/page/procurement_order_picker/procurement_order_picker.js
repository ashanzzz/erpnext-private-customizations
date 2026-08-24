// Copyright (c) 2026, Ashan CN Procurement and contributors
// Procurement Order Selection & Downstream Document Generation Hub

frappe.pages["procurement-order-picker"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("采购全流程选单中心"),
        single_column: true,
    });
    new ProcurementOrderPickerCenter(page);
};

class ProcurementOrderPickerCenter {
    constructor(page) {
        this.page = page;
        this.active_stage = "item_to_mr"; // item_to_mr, mr_to_po, po_to_pr, pr_to_pi, pi_to_rr
        this.view_modes = {
            item_to_mr: "detail",
            mr_to_po: "detail",
            po_to_pr: "detail",
            pr_to_pi: "detail",
            pi_to_rr: "detail",
        };
        this.active_company = "All"; // "All" or specific company name
        this.companies = [];
        this.locked_company = null; // Dynamically set when first row is checked in "All" mode
        this.kpis = {};
        this.table_data = [];
        this.selected_map = new Map(); // key -> row object
        this.filters = {
            item_to_mr: { match_status: "pending", mr_name: "", item_code: "", item_group: "", department: "" },
            mr_to_po: { match_status: "pending", linked_doc: "", supplier: "", department: "", item_code: "", from_date: "", to_date: "" },
            po_to_pr: { match_status: "pending", linked_doc: "", supplier: "", warehouse: "", po_name: "", item_code: "" },
            pr_to_pi: { match_status: "pending", linked_doc: "", supplier: "", pr_name: "", item_code: "" },
            pi_to_rr: { match_status: "pending", linked_doc: "", supplier: "", bill_no: "", owner: "" },
        };

        this.stages_config = {
            item_to_mr: {
                id: "item_to_mr",
                name: "采购申请",
                banner_title: "当前：采购申请",
                banner_desc: "查看与管理已提报的采购申请明细及单据。如需修改请点击申请单号进入单据修改，或点击【+ 新建物料申请单】快速录入。",
                sub_label: "采购申请单据",
                icon: "📋",
                btn_label: "",
            },
            mr_to_po: {
                id: "mr_to_po",
                name: "采购订货",
                banner_title: "当前：采购订货",
                banner_desc: "勾选待订需求明细或单号，系统自动按建议供应商智能拆单合并生成正式采购订单 (Purchase Order)。",
                sub_label: "待订货需求明细",
                icon: "🛒",
                btn_label: "🚀 生成采购订单",
            },
            po_to_pr: {
                id: "po_to_pr",
                name: "采购入库",
                banner_title: "当前：采购入库",
                banner_desc: "勾选待收货订单明细，弹窗核对或调整实收数量与仓库，生成并正式发布采购入库单 (Purchase Receipt)。",
                sub_label: "待收货订单明细",
                icon: "📦",
                btn_label: "🚀 生成采购入库单",
            },
            pr_to_pi: {
                id: "pr_to_pi",
                name: "采购开票",
                banner_title: "当前：采购开票",
                banner_desc: "勾选已入库物料明细，弹窗录入发票号码、日期与税额，生成并正式发布采购发票 (Purchase Invoice)。",
                sub_label: "待开票入库明细",
                icon: "🧾",
                btn_label: "🚀 生成采购发票",
            },
            pi_to_rr: {
                id: "pi_to_rr",
                name: "报销付款",
                banner_title: "当前：报销付款",
                banner_desc: "勾选待报销发票明细，弹窗核对报销人与金额，生成并正式发布报销付款申请 (Reimbursement Request)。",
                sub_label: "待报销付款发票",
                icon: "💰",
                btn_label: "🚀 生成报销申请单",
            },
        };

        this.init();
    }

    async init() {
        this.setup_ui_skeleton();
        await this.load_companies();
        this.bind_global_events();
        this.sync_route_params();
        this.refresh_all();
    }

    setup_ui_skeleton() {
        const html = `
            <div class="picker-page-container">
                <!-- Top Header & Company Dropdown -->
                <div class="picker-top-bar">
                    <div class="picker-title-group">
                        <h2>🛒 采购全流程选单生单中心</h2>
                        <div class="picker-subtitle">普通采购流程</div>
                    </div>
                    <div class="picker-company-group">
                        <label class="picker-company-label" for="picker-company-select">所属公司:</label>
                        <select class="picker-company-select" id="picker-company-select">
                            <option value="All">🌐 全部公司 (汇聚视图)</option>
                        </select>
                    </div>
                </div>

                <!-- 5-Step KPI Cards Grid (Master Navigation) -->
                <div class="picker-kpi-grid" id="picker-kpi-grid"></div>

                <!-- Section Context Banner -->
                <div class="picker-section-banner" id="picker-section-banner"></div>

                <!-- Dynamic Filter Bar -->
                <div class="picker-filter-bar" id="picker-filter-bar"></div>

                <!-- Action Bar -->
                <div class="picker-action-bar" id="picker-action-bar"></div>

                <!-- Table Wrapper with Dual Scrollbars -->
                <div class="picker-table-wrapper">
                    <div class="picker-top-scrollbar-wrap" id="picker-top-scrollbar">
                        <div class="picker-top-scrollbar-inner" id="picker-top-scrollbar-inner"></div>
                    </div>
                    <div class="picker-main-table-scroll" id="picker-main-table-scroll">
                        <table class="picker-data-table" id="picker-data-table">
                            <thead id="picker-table-thead"></thead>
                            <tbody id="picker-table-tbody"></tbody>
                            <tfoot id="picker-table-tfoot"></tfoot>
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
            if (r && r.message) {
                this.companies = r.message.companies || [];
                this.render_company_select();
            }
        } catch (e) {
            console.error("Failed to load user companies", e);
        }
    }

    render_company_select() {
        const $select = $("#picker-company-select");
        $select.empty();

        $select.append(`<option value="All" ${this.active_company === 'All' ? 'selected' : ''}>🌐 全部公司 (汇聚视图)</option>`);

        this.companies.forEach((comp) => {
            const is_selected = this.active_company === comp;
            $select.append(`<option value="${frappe.utils.escape_html(comp)}" ${is_selected ? 'selected' : ''}>${frappe.utils.escape_html(comp)}</option>`);
        });
    }

    bind_global_events() {
        const self = this;

        // Company Select Change
        $(this.page.body).on("change", "#picker-company-select", function () {
            const comp = $(this).val();
            if (self.active_company === comp) return;
            self.active_company = comp;
            self.locked_company = null;
            self.selected_map.clear();
            self.refresh_all();
        });

        // Unlock Button Click
        $(this.page.body).on("click", "#picker-unlock-btn", function () {
            self.locked_company = null;
            self.selected_map.clear();
            self.update_company_lock_ui();
            self.render_table_rows();
            self.update_action_summary();
        });

        // KPI Card Click (Master Flow Navigation)
        $(this.page.body).on("click", ".picker-kpi-card", function () {
            const stage = $(this).attr("data-stage");
            if (stage && self.active_stage !== stage) {
                self.switch_stage(stage);
            }
        });

        // View Mode Switcher (明细视图 vs 单号视图 for all stages)
        $(this.page.body).on("click", ".picker-view-btn", function () {
            const mode = $(this).attr("data-mode");
            const stage = self.active_stage;
            if (mode && self.view_modes[stage] !== mode) {
                self.view_modes[stage] = mode;
                $(".picker-view-btn").removeClass("active");
                $(this).addClass("active");
                self.selected_map.clear();
                self.locked_company = null;
                self.load_table_data();
            }
        });

        // Quick Create Material Request Button
        $(this.page.body).on("click", "#picker-create-mr-btn", function () {
            self.open_create_mr_dialog();
        });

        // Dual Scrollbar Sync
        const $top_scroll = $("#picker-top-scrollbar");
        const $table_scroll = $("#picker-main-table-scroll");
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

        // Row Checkbox Click
        $(this.page.body).on("change", ".picker-row-checkbox", function () {
            const key = $(this).attr("data-key");
            const is_checked = $(this).is(":checked");
            const row = self.table_data.find((r) => self.get_row_key(r) === key);
            if (!row) return;

            if (is_checked) {
                // If in "All" mode and not locked yet, lock to this company
                if (self.active_company === "All" && !self.locked_company) {
                    self.locked_company = row.company;
                    self.update_company_lock_ui(true);
                }

                // If locked and row is from another company, ignore
                if (self.locked_company && row.company !== self.locked_company) {
                    $(this).prop("checked", false);
                    return;
                }

                const $tr = $(this).closest("tr");
                const input_qty = flt($tr.find(".picker-input-qty").val()) || row.pending_qty || row.qty || 1;
                row.this_qty = input_qty;
                self.selected_map.set(key, row);
                $tr.addClass("row-selected");
            } else {
                self.selected_map.delete(key);
                $(this).closest("tr").removeClass("row-selected");

                // If no rows selected, release lock
                if (self.selected_map.size === 0) {
                    self.locked_company = null;
                    self.update_company_lock_ui(false);
                }
            }

            self.update_table_visibility_by_lock();
            self.update_action_summary();
        });

        // Row Qty Input Change (Only in detail views for stages 2..4)
        $(this.page.body).on("input change", ".picker-input-qty", function () {
            const $tr = $(this).closest("tr");
            const key = $tr.attr("data-key");
            const val = flt($(this).val());
            const row = self.table_data.find((r) => self.get_row_key(r) === key);
            if (row) {
                row.this_qty = val;
                if (self.selected_map.has(key)) {
                    self.selected_map.get(key).this_qty = val;
                }
            }
            self.update_row_amount_display($tr, row);
            self.update_action_summary();
        });

        // Select All / Clear Selection / Fill Max
        $(this.page.body).on("change", "#picker-select-all-header", function () {
            const is_checked = $(this).prop("checked");
            if (is_checked) {
                self.select_all_visible();
            } else {
                self.clear_selection();
            }
        });
        $(this.page.body).on("click", "#picker-select-all-btn", () => this.select_all_visible());
        $(this.page.body).on("click", "#picker-clear-sel-btn", () => this.clear_selection());
        $(this.page.body).on("click", "#picker-fill-max-btn", () => this.fill_max_quantities());
        $(this.page.body).on("click", "#picker-batch-delete-btn", () => this.batch_delete_selected());

        // Primary Action Submit
        $(this.page.body).on("click", "#picker-submit-btn", () => this.execute_primary_action());

        // Click on document link / badge to open Doc Detail Modal
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

    sync_route_params() {
        const route = frappe.get_route();
        if (route && route.length > 1) {
            const param = route[1];
            if (this.stages_config[param]) {
                this.active_stage = param;
            }
        }
    }

    switch_stage(stage) {
        this.active_stage = stage;
        this.locked_company = null;
        this.selected_map.clear();
        this.update_company_lock_ui();
        frappe.set_route("procurement-order-picker", stage);
        this.render_kpis();
        this.render_section_banner();
        this.render_filter_bar();
        this.load_table_data();
    }

    async refresh_all() {
        await this.load_kpis();
        this.render_kpis();
        this.render_section_banner();
        this.render_filter_bar();
        await this.load_table_data();
    }

    async load_kpis() {
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.get_procurement_picker_overview_kpis",
                args: { company: this.active_company },
            });
            if (r && r.message) {
                this.kpis = r.message.kpis || {};
            }
        } catch (e) {
            console.error("Failed to load KPIs", e);
        }
    }

    render_kpis() {
        const $container = $("#picker-kpi-grid");
        $container.empty();

        const stage_keys = ["item_to_mr", "mr_to_po", "po_to_pr", "pr_to_pi", "pi_to_rr"];
        stage_keys.forEach((key) => {
            const cfg = this.stages_config[key];
            const data = this.kpis[key] || { count: 0 };
            const is_active = this.active_stage === key;

            let num_text = data.count || 0;
            let sub_text = cfg.sub_label;
            if (key === "pi_to_rr" && data.amount !== undefined) {
                sub_text = `待报销: ${this.fmt_money(data.amount)}`;
            }

            const html = `
                <div class="picker-kpi-card ${is_active ? 'active' : ''}" data-stage="${key}">
                    <div class="picker-kpi-header">
                        <div class="picker-kpi-title">${cfg.name}</div>
                        <div class="picker-kpi-icon">${cfg.icon}</div>
                    </div>
                    <div class="picker-kpi-body">
                        <div class="picker-kpi-number">${num_text}</div>
                        <div class="picker-kpi-sub">${sub_text}</div>
                    </div>
                </div>
            `;
            $container.append(html);
        });
    }

    render_section_banner() {
        const $container = $("#picker-section-banner");
        const cfg = this.stages_config[this.active_stage];
        const data = this.kpis[this.active_stage] || { count: 0 };

        const html = `
            <div class="picker-section-main">
                <div class="picker-section-icon">${cfg.icon}</div>
                <div class="picker-section-heading">
                    <div class="picker-section-title">
                        <span>${cfg.banner_title}</span>
                    </div>
                    <div class="picker-section-desc">${cfg.banner_desc}</div>
                </div>
            </div>
            <div class="picker-section-badge">
                统计: ${data.count || 0} 笔
            </div>
        `;
        $container.html(html);
    }

    render_filter_bar() {
        const $bar = $("#picker-filter-bar");
        $bar.empty();
        const stage = this.active_stage;

        let filters_html = "";
        if (stage === "item_to_mr") {
            const ms = this.filters[stage].match_status || "pending";
            filters_html = `
                <div class="picker-filter-group">
                    <label>采购状态:</label>
                    <select class="picker-filter-select" data-filter="match_status">
                        <option value="pending" ${ms === 'pending' ? 'selected' : ''}>🟡 仅待订购需求 (未生成订单/未订完)</option>
                        <option value="completed" ${ms === 'completed' ? 'selected' : ''}>🟢 仅已全部订购 (已生成订单)</option>
                        <option value="all" ${ms === 'all' ? 'selected' : ''}>🌐 全部申请单据 (全量追溯)</option>
                    </select>
                </div>
                <div class="picker-filter-group">
                    <label>申请单号:</label>
                    <input type="text" class="picker-filter-input" data-filter="mr_name" placeholder="搜索单号..." value="${this.filters[stage].mr_name || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-filter-input" data-filter="item_code" placeholder="物料代码/名称..." value="${this.filters[stage].item_code || ''}">
                </div>
            `;
        } else if (stage === "mr_to_po") {
            const ms = this.filters[stage].match_status || "pending";
            filters_html = `
                <div class="picker-filter-group">
                    <label>关联状态:</label>
                    <select class="picker-filter-select" data-filter="match_status">
                        <option value="pending" ${ms === 'pending' ? 'selected' : ''}>🟡 仅待订需求 (未关联/待订)</option>
                        <option value="linked" ${ms === 'linked' ? 'selected' : ''}>🟢 仅已订需求 (已关联PO)</option>
                        <option value="all" ${ms === 'all' ? 'selected' : ''}>🌐 全部需求单据 (全量追溯)</option>
                    </select>
                </div>
                <div class="picker-filter-group">
                    <label>关联订单号:</label>
                    <input type="text" class="picker-filter-input" data-filter="linked_doc" placeholder="搜索关联PO单号..." value="${this.filters[stage].linked_doc || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-filter-input" data-filter="item_code" placeholder="搜索物料..." value="${this.filters[stage].item_code || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>建议供应商:</label>
                    <input type="text" class="picker-filter-input" data-filter="supplier" placeholder="供应商名称..." value="${this.filters[stage].supplier || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>申请日期:</label>
                    <input type="date" class="picker-filter-input" data-filter="from_date" value="${this.filters[stage].from_date || ''}">
                    <span>至</span>
                    <input type="date" class="picker-filter-input" data-filter="to_date" value="${this.filters[stage].to_date || ''}">
                </div>
            `;
        } else if (stage === "po_to_pr") {
            const ms = this.filters[stage].match_status || "pending";
            filters_html = `
                <div class="picker-filter-group">
                    <label>关联状态:</label>
                    <select class="picker-filter-select" data-filter="match_status">
                        <option value="pending" ${ms === 'pending' ? 'selected' : ''}>🟡 仅待收订单 (未关联/待收)</option>
                        <option value="linked" ${ms === 'linked' ? 'selected' : ''}>🟢 仅已收订单 (已关联PR)</option>
                        <option value="all" ${ms === 'all' ? 'selected' : ''}>🌐 全部采购订单 (全量追溯)</option>
                    </select>
                </div>
                <div class="picker-filter-group">
                    <label>关联入库单:</label>
                    <input type="text" class="picker-filter-input" data-filter="linked_doc" placeholder="搜索关联PR单号..." value="${this.filters[stage].linked_doc || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>供应商:</label>
                    <input type="text" class="picker-filter-input" data-filter="supplier" placeholder="搜索供应商..." value="${this.filters[stage].supplier || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>采购订单号:</label>
                    <input type="text" class="picker-filter-input" data-filter="po_name" placeholder="PO-..." value="${this.filters[stage].po_name || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-filter-input" data-filter="item_code" placeholder="物料..." value="${this.filters[stage].item_code || ''}">
                </div>
            `;
        } else if (stage === "pr_to_pi") {
            const ms = this.filters[stage].match_status || "pending";
            filters_html = `
                <div class="picker-filter-group">
                    <label>关联状态:</label>
                    <select class="picker-filter-select" data-filter="match_status">
                        <option value="pending" ${ms === 'pending' ? 'selected' : ''}>🟡 仅待开票 (未关联/待开)</option>
                        <option value="linked" ${ms === 'linked' ? 'selected' : ''}>🟢 仅已开票 (已关联PI)</option>
                        <option value="all" ${ms === 'all' ? 'selected' : ''}>🌐 全部入库单据 (全量追溯)</option>
                    </select>
                </div>
                <div class="picker-filter-group">
                    <label>关联发票号:</label>
                    <input type="text" class="picker-filter-input" data-filter="linked_doc" placeholder="搜索关联PI发票号..." value="${this.filters[stage].linked_doc || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>供应商:</label>
                    <input type="text" class="picker-filter-input" data-filter="supplier" placeholder="搜索供应商..." value="${this.filters[stage].supplier || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>采购入库单号:</label>
                    <input type="text" class="picker-filter-input" data-filter="pr_name" placeholder="PR-..." value="${this.filters[stage].pr_name || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-filter-input" data-filter="item_code" placeholder="物料..." value="${this.filters[stage].item_code || ''}">
                </div>
            `;
        } else if (stage === "pi_to_rr") {
            const ms = this.filters[stage].match_status || "pending";
            filters_html = `
                <div class="picker-filter-group">
                    <label>关联状态:</label>
                    <select class="picker-filter-select" data-filter="match_status">
                        <option value="pending" ${ms === 'pending' ? 'selected' : ''}>🟡 仅待报销发票 (未关联/未付清)</option>
                        <option value="linked" ${ms === 'linked' ? 'selected' : ''}>🟢 仅已报销发票 (已关联RR)</option>
                        <option value="all" ${ms === 'all' ? 'selected' : ''}>🌐 全部发票单据 (全量追溯)</option>
                    </select>
                </div>
                <div class="picker-filter-group">
                    <label>关联报销单:</label>
                    <input type="text" class="picker-filter-input" data-filter="linked_doc" placeholder="搜索关联RR报销单号..." value="${this.filters[stage].linked_doc || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>供应商:</label>
                    <input type="text" class="picker-filter-input" data-filter="supplier" placeholder="搜索供应商..." value="${this.filters[stage].supplier || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>发票号码:</label>
                    <input type="text" class="picker-filter-input" data-filter="bill_no" placeholder="发票代码/号码..." value="${this.filters[stage].bill_no || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>经手人:</label>
                    <input type="text" class="picker-filter-input" data-filter="owner" placeholder="录单人..." value="${this.filters[stage].owner || ''}">
                </div>
            `;
        }

        $bar.html(filters_html);

        const self = this;
        $bar.find(".picker-filter-input, .picker-filter-select").on("change input", function () {
            const key = $(this).attr("data-filter");
            self.filters[stage][key] = $(this).val();
            self.debounce_reload();
        });
    }

    debounce_reload() {
        clearTimeout(this._debounce_timer);
        this._debounce_timer = setTimeout(() => {
            this.load_table_data();
        }, 300);
    }

    async load_table_data() {
        const stage = this.active_stage;
        const mode = this.view_modes[stage] || "detail";
        let method = "";

        if (stage === "item_to_mr") {
            method = mode === "doc"
                ? "ashan_cn_procurement.services.procurement_picker_service.get_material_request_doc_rows"
                : "ashan_cn_procurement.services.procurement_picker_service.get_material_request_picker_rows";
        } else if (stage === "mr_to_po") {
            method = mode === "doc"
                ? "ashan_cn_procurement.services.procurement_picker_service.get_pending_material_request_docs"
                : "ashan_cn_procurement.services.procurement_picker_service.get_pending_material_request_items";
        } else if (stage === "po_to_pr") {
            method = mode === "doc"
                ? "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_order_docs"
                : "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_order_items";
        } else if (stage === "pr_to_pi") {
            method = mode === "doc"
                ? "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_receipt_docs"
                : "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_receipt_items";
        } else if (stage === "pi_to_rr") {
            method = mode === "detail"
                ? "ashan_cn_procurement.services.procurement_picker_service.get_pending_reimbursement_invoice_items"
                : "ashan_cn_procurement.services.procurement_picker_service.get_pending_reimbursement_invoices";
        }

        try {
            const r = await frappe.call({
                method: method,
                args: {
                    company: this.active_company,
                    filters: this.filters[stage],
                },
            });
            if (r && r.message) {
                this.table_data = r.message.rows || [];
                this.selected_map.clear();
                this.locked_company = null;
                this.update_company_lock_ui();
                this.render_table();
                this.update_action_summary();
            }
        } catch (e) {
            console.error("Failed to load picker rows", e);
        }
    }

    get_row_key(row) {
        const stage = this.active_stage;
        const mode = this.view_modes[stage] || "detail";

        if (stage === "item_to_mr") {
            return mode === "doc" ? row.mr_name : row.mri_name;
        }
        if (stage === "mr_to_po") {
            return mode === "doc" ? row.mr_name : row.mri_name;
        }
        if (stage === "po_to_pr") {
            return mode === "doc" ? row.po_name : row.poi_name;
        }
        if (stage === "pr_to_pi") {
            return mode === "doc" ? row.pr_name : row.pri_name;
        }
        if (stage === "pi_to_rr") {
            return mode === "detail" ? row.pii_name : row.pi_name;
        }
        return row.name || String(Math.random());
    }

    render_table() {
        this.render_table_header();
        this.render_table_rows();
        this.render_table_footer();
        this.sync_scroll_widths();
    }

    render_table_header() {
        const stage = this.active_stage;
        const mode = this.view_modes[stage] || "detail";

        let ths = `
            <th class="picker-col-sticky-1">#</th>
            <th class="picker-col-sticky-2 picker-col-checkbox-th">
                <input type="checkbox" id="picker-select-all-header" class="picker-header-checkbox" title="全选 / 全不选当前页">
            </th>
        `;

        if (this.active_company === "All") {
            ths += `<th class="picker-col-sticky-3">所属公司</th>`;
        }

        if (stage === "item_to_mr") {
            if (mode === "doc") {
                ths += `
                    <th>申请单号</th>
                    <th>申请日期</th>
                    <th>需求部门</th>
                    <th>单据明细</th>
                    <th>物料项数</th>
                    <th>申请总数</th>
                    <th>单据状态</th>
                    <th>制单人</th>
                `;
            } else {
                ths += `
                    <th>申请单号</th>
                    <th>物料代码</th>
                    <th>物料名称/规格</th>
                    <th>物料分组</th>
                    <th>单位</th>
                    <th>申请数</th>
                    <th>参考单价</th>
                    <th>用途/规格备注</th>
                `;
            }
        } else if (stage === "mr_to_po") {
            if (mode === "doc") {
                ths += `
                    <th>采购申请单号</th>
                    <th>申请日期</th>
                    <th>期望到货日</th>
                    <th>单据明细</th>
                    <th>待订项数</th>
                    <th>待订总数</th>
                    <th>预估金额</th>
                    <th>建议供应商</th>
                    <th>🔗 关联采购订单</th>
                    <th>制单人</th>
                `;
            } else {
                ths += `
                    <th>采购申请单号</th>
                    <th>期望到货日</th>
                    <th>物料代码</th>
                    <th>物料名称/规格</th>
                    <th>单位</th>
                    <th>申请总数</th>
                    <th>已订数</th>
                    <th>未订数量</th>
                    <th>参考单价</th>
                    <th>金额</th>
                    <th>税额</th>
                    <th>含税总价</th>
                    <th>备注</th>
                    <th>建议供应商</th>
                    <th>🔗 关联采购订单</th>
                `;
            }
        } else if (stage === "po_to_pr") {
            if (mode === "doc") {
                ths += `
                    <th>供应商</th>
                    <th>采购订单号</th>
                    <th>订单日期</th>
                    <th>承诺交期</th>
                    <th>收货仓库</th>
                    <th>单据明细</th>
                    <th>待收项数</th>
                    <th>待收总数</th>
                    <th>待收金额</th>
                    <th>订单总额</th>
                    <th>🔗 关联入库单</th>
                    <th>订单状态</th>
                `;
            } else {
                ths += `
                    <th>供应商</th>
                    <th>采购订单号</th>
                    <th>订单日期</th>
                    <th>承诺交期</th>
                    <th>物料代码/名称</th>
                    <th>收货仓库</th>
                    <th>订购总数</th>
                    <th>已收数</th>
                    <th>未收数量</th>
                    <th>采购单价</th>
                    <th>待收金额</th>
                    <th>🔗 关联入库单</th>
                `;
            }
        } else if (stage === "pr_to_pi") {
            if (mode === "doc") {
                ths += `
                    <th>供应商</th>
                    <th>采购入库单号</th>
                    <th>过账日期</th>
                    <th>单据明细</th>
                    <th>未结项数</th>
                    <th>待开票总数</th>
                    <th>待开票金额</th>
                    <th>入库单总额</th>
                    <th>关联订单</th>
                    <th>🔗 关联采购发票</th>
                `;
            } else {
                ths += `
                    <th>供应商</th>
                    <th>采购入库单号</th>
                    <th>过账日期</th>
                    <th>物料代码/名称</th>
                    <th>单位</th>
                    <th>实收总数</th>
                    <th>已开票数</th>
                    <th>未结数量</th>
                    <th>入库单价</th>
                    <th>待开票金额</th>
                    <th>关联订单</th>
                    <th>🔗 关联采购发票</th>
                `;
            }
        } else if (stage === "pi_to_rr") {
            if (mode === "doc") {
                ths += `
                    <th>采购发票号</th>
                    <th>供应商</th>
                    <th>发票代码/号码</th>
                    <th>票据类型</th>
                    <th>单据明细</th>
                    <th>开票日期</th>
                    <th>录单人</th>
                    <th>发票总额</th>
                    <th>已付金额</th>
                    <th>待报销余额</th>
                    <th>🔗 关联报销单</th>
                `;
            } else {
                ths += `
                    <th>采购发票号</th>
                    <th>供应商</th>
                    <th>发票代码/号码</th>
                    <th>物料/费用项目</th>
                    <th>单位</th>
                    <th>数量</th>
                    <th>单价</th>
                    <th>明细金额</th>
                    <th>开票日期</th>
                    <th>待报销余额</th>
                    <th>🔗 关联报销单</th>
                `;
            }
        }

        $("#picker-table-thead").html(`<tr>${ths}</tr>`);
    }

    render_table_rows() {
        const $tbody = $("#picker-table-tbody");
        $tbody.empty();

        if (!this.table_data || this.table_data.length === 0) {
            const col_span = 14;
            $tbody.html(`
                <tr>
                    <td colspan="${col_span}">
                        <div class="picker-empty-state">
                            <div class="picker-empty-icon">🎉</div>
                            <div>当前没有符合条件的记录</div>
                        </div>
                    </td>
                </tr>
            `);
            return;
        }

        const stage = this.active_stage;
        const mode = this.view_modes[stage] || "detail";
        const is_all_company = this.active_company === "All";

        const slug_map = {
            "material-request": "Material Request",
            "purchase-order": "Purchase Order",
            "purchase-receipt": "Purchase Receipt",
            "purchase-invoice": "Purchase Invoice",
            "reimbursement-request": "Reimbursement Request",
        };

        const render_linked_badges = (names_str, slug) => {
            if (!names_str || !names_str.trim()) {
                return `<span class="picker-no-link">-</span>`;
            }
            const dt = slug_map[slug] || "Purchase Order";
            const names = names_str.split(/[、,]/).map(s => s.trim()).filter(Boolean);
            if (!names.length) return `<span class="picker-no-link">-</span>`;
            return names.map(n => `<span class="picker-linked-badge picker-doc-clickable-link" data-doctype="${dt}" data-name="${frappe.utils.escape_html(n)}" title="点击弹窗查看单据详情与操作">🔗 ${frappe.utils.escape_html(n)}</span>`).join(" ");
        };

        this.table_data.forEach((r, idx) => {
            const key = this.get_row_key(r);
            const is_selected = this.selected_map.has(key);
            const is_hidden_by_lock = this.locked_company && r.company !== this.locked_company;

            let is_completed = false;
            if (stage === "mr_to_po" || stage === "po_to_pr" || stage === "pr_to_pi") {
                is_completed = flt(r.pending_qty) <= 0.0001;
            } else if (stage === "pi_to_rr") {
                is_completed = flt(r.net_available_amount) <= 0.0001;
            }

            const checkbox_attr = is_completed
                ? `disabled title="该单据/明细已全部处理完成"`
                : `${is_selected ? 'checked' : ''}`;

            let tr_html = `
                <tr class="${is_selected ? 'row-selected' : ''} ${is_completed ? 'picker-row-completed' : ''} ${is_hidden_by_lock ? 'picker-row-company-hidden' : ''}" data-key="${key}" data-company="${frappe.utils.escape_html(r.company || '')}">
                    <td class="picker-col-sticky-1">${idx + 1}</td>
                    <td class="picker-col-sticky-2">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${key}" ${checkbox_attr}>
                    </td>
            `;

            if (is_all_company) {
                const comp_short = (r.company || "").includes("祺富") ? "祺富" : ((r.company || "").includes("吉众") ? "吉众" : (r.company || ""));
                const comp_cls = (r.company || "").includes("祺富") ? "picker-company-badge-qifu" : "picker-company-badge-jizhong";
                tr_html += `
                    <td class="picker-col-sticky-3">
                        <span class="picker-company-badge ${comp_cls}">${frappe.utils.escape_html(comp_short)}</span>
                    </td>
                `;
            }

            const doc_badges = (val) => {
                if (window.ashan && window.ashan.doc_details && typeof window.ashan.doc_details.render_badges === "function") {
                    return window.ashan.doc_details.render_badges(val || "");
                }
                return frappe.utils.escape_html(val || "-");
            };

            if (stage === "item_to_mr") {
                if (mode === "doc") {
                    tr_html += `
                        <td><span class="picker-linked-badge picker-doc-clickable-link" data-doctype="Material Request" data-name="${r.mr_name}" title="点击弹窗查看单据详情与操作">📋 ${frappe.utils.escape_html(r.mr_name)}</span></td>
                        <td>${r.transaction_date || "-"}</td>
                        <td>${frappe.utils.escape_html(r.department || "-")}</td>
                        <td>${doc_badges(r.custom_doc_details)}</td>
                        <td class="picker-qty-cell">${r.item_count || 0}</td>
                        <td class="picker-qty-cell"><strong>${flt(r.total_qty).toFixed(2)}</strong></td>
                        <td><span class="ashan-status-badge ashan-status-blue">${frappe.utils.escape_html(r.status || "Draft")}</span></td>
                        <td>${frappe.utils.escape_html(r.owner || "-")}</td>
                    `;
                } else {
                    tr_html += `
                        <td><span class="picker-linked-badge picker-doc-clickable-link" data-doctype="Material Request" data-name="${r.mr_name}" title="点击弹窗查看单据详情与操作">📋 ${frappe.utils.escape_html(r.mr_name)}</span></td>
                        <td><strong>${frappe.utils.escape_html(r.item_code)}</strong></td>
                        <td>${frappe.utils.escape_html(r.item_name || r.item_code)}</td>
                        <td>${frappe.utils.escape_html(r.item_group || "")}</td>
                        <td>${frappe.utils.escape_html(r.uom || "")}</td>
                        <td class="picker-qty-cell"><strong>${r.qty}</strong></td>
                        <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                        <td>${frappe.utils.escape_html(r.description || "-")}</td>
                    `;
                }
            } else if (stage === "mr_to_po") {
                if (mode === "doc") {
                    tr_html += `
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Material Request" data-name="${r.mr_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.mr_name)}</span></td>
                        <td>${r.transaction_date || "-"}</td>
                        <td>${r.schedule_date || "-"}</td>
                        <td>${doc_badges(r.custom_doc_details)}</td>
                        <td class="picker-qty-cell">${r.pending_item_count || 0}</td>
                        <td class="picker-qty-cell"><strong>${flt(r.pending_qty).toFixed(2)}</strong></td>
                        <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.estimated_amount)}</td>
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td>${render_linked_badges(r.linked_po_names, "purchase-order")}</td>
                        <td>${frappe.utils.escape_html(r.owner || "-")}</td>
                    `;
                } else {
                    const urgent_tag = r.is_overdue ? `<span class="picker-badge-urgent">逾期</span>` : (r.is_urgent ? `<span class="picker-badge-urgent">紧急</span>` : "");
                    const name_spec_str = r.spec ? `${frappe.utils.escape_html(r.item_name || "")} (${frappe.utils.escape_html(r.spec)})` : frappe.utils.escape_html(r.item_name || "");
                    const row_amt = flt(r.amount || (r.pending_qty * r.rate));
                    const row_tax = flt(r.tax_amount || (row_amt * (flt(r.tax_rate || 13) / 100.0)));
                    const row_total = flt(r.total_amount || (row_amt + row_tax));
                    tr_html += `
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Material Request" data-name="${r.mr_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.mr_name)}</span></td>
                        <td>${r.schedule_date || "-"} ${urgent_tag}</td>
                        <td><strong>${frappe.utils.escape_html(r.item_code)}</strong></td>
                        <td>${name_spec_str}</td>
                        <td>${frappe.utils.escape_html(r.uom || "")}</td>
                        <td class="picker-qty-cell">${r.qty}</td>
                        <td class="picker-qty-cell">${r.ordered_qty}</td>
                        <td class="picker-qty-cell"><strong>${r.pending_qty}</strong></td>
                        <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                        <td class="picker-money-cell cell-row-amt">${this.fmt_money(row_amt)}</td>
                        <td class="picker-money-cell">${this.fmt_money(row_tax)}</td>
                        <td class="picker-money-cell">${this.fmt_money(row_total)}</td>
                        <td>${frappe.utils.escape_html(r.remarks || r.description || "-")}</td>
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td>${render_linked_badges(r.linked_po_names, "purchase-order")}</td>
                    `;
                }
            } else if (stage === "po_to_pr") {
                if (mode === "doc") {
                    tr_html += `
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Order" data-name="${r.po_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.po_name)}</span></td>
                        <td>${r.po_date || "-"}</td>
                        <td>${r.schedule_date || "-"}</td>
                        <td>${frappe.utils.escape_html(r.warehouse || "-")}</td>
                        <td>${doc_badges(r.custom_doc_details)}</td>
                        <td class="picker-qty-cell">${r.pending_item_count || 0}</td>
                        <td class="picker-qty-cell"><strong>${flt(r.pending_qty).toFixed(2)}</strong></td>
                        <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.pending_amount)}</td>
                        <td class="picker-money-cell">${this.fmt_money(r.grand_total)}</td>
                        <td>${render_linked_badges(r.linked_pr_names, "purchase-receipt")}</td>
                        <td><span class="ashan-status-badge ashan-status-blue">${frappe.utils.escape_html(r.status || "")}</span></td>
                    `;
                } else {
                    tr_html += `
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Order" data-name="${r.po_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.po_name)}</span></td>
                        <td>${r.po_date || "-"}</td>
                        <td>${r.schedule_date || "-"}</td>
                        <td><span class="ashan-tag-badge">${frappe.utils.escape_html(r.item_code)}</span> ${frappe.utils.escape_html(r.item_name || "")}</td>
                        <td>${frappe.utils.escape_html(r.warehouse || "-")}</td>
                        <td class="picker-qty-cell">${r.qty}</td>
                        <td class="picker-qty-cell">${r.received_qty}</td>
                        <td class="picker-qty-cell"><strong>${r.pending_qty}</strong></td>
                        <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                        <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.pending_amount)}</td>
                        <td>${render_linked_badges(r.linked_pr_names, "purchase-receipt")}</td>
                    `;
                }
            } else if (stage === "pr_to_pi") {
                if (mode === "doc") {
                    tr_html += `
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Receipt" data-name="${r.pr_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.pr_name)}</span></td>
                        <td>${r.pr_date || "-"}</td>
                        <td>${doc_badges(r.custom_doc_details)}</td>
                        <td class="picker-qty-cell">${r.unbilled_item_count || 0}</td>
                        <td class="picker-qty-cell"><strong>${flt(r.pending_qty).toFixed(2)}</strong></td>
                        <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.pending_amount)}</td>
                        <td class="picker-money-cell">${this.fmt_money(r.grand_total)}</td>
                        <td>${frappe.utils.escape_html(r.purchase_order || "-")}</td>
                        <td>${render_linked_badges(r.linked_pi_names, "purchase-invoice")}</td>
                    `;
                } else {
                    tr_html += `
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Receipt" data-name="${r.pr_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.pr_name)}</span></td>
                        <td>${r.pr_date || "-"}</td>
                        <td><span class="ashan-tag-badge">${frappe.utils.escape_html(r.item_code)}</span> ${frappe.utils.escape_html(r.item_name || "")}</td>
                        <td>${frappe.utils.escape_html(r.uom || "")}</td>
                        <td class="picker-qty-cell">${r.qty}</td>
                        <td class="picker-qty-cell">${r.billed_qty}</td>
                        <td class="picker-qty-cell"><strong>${r.pending_qty}</strong></td>
                        <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                        <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.pending_amount)}</td>
                        <td>${frappe.utils.escape_html(r.purchase_order || "-")}</td>
                        <td>${render_linked_badges(r.linked_pi_names, "purchase-invoice")}</td>
                    `;
                }
            } else if (stage === "pi_to_rr") {
                if (mode === "doc") {
                    tr_html += `
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Invoice" data-name="${r.pi_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.pi_name)}</span></td>
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td><span class="picker-badge-invoice-type">${frappe.utils.escape_html(r.bill_no || "未填")}</span></td>
                        <td><span class="ashan-status-badge ashan-status-blue">${frappe.utils.escape_html(r.invoice_type || "普通发票")}</span></td>
                        <td>${doc_badges(r.custom_doc_details)}</td>
                        <td>${r.bill_date || r.posting_date || "-"}</td>
                        <td>${frappe.utils.escape_html(r.owner || "-")}</td>
                        <td class="picker-money-cell">${this.fmt_money(r.grand_total)}</td>
                        <td class="picker-money-cell">${this.fmt_money(r.grand_total - r.outstanding_amount)}</td>
                        <td class="picker-money-cell cell-row-amt"><strong>${this.fmt_money(r.net_available_amount)}</strong></td>
                        <td>${render_linked_badges(r.linked_rr_names, "reimbursement-request")}</td>
                    `;
                } else {
                    tr_html += `
                        <td><span class="picker-source-docname picker-doc-clickable-link" data-doctype="Purchase Invoice" data-name="${r.pi_name}" title="点击查看详情与操作">${frappe.utils.escape_html(r.pi_name)}</span></td>
                        <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                        <td><span class="picker-badge-invoice-type">${frappe.utils.escape_html(r.bill_no || "未填")}</span></td>
                        <td><strong>${frappe.utils.escape_html(r.item_code)}</strong> ${frappe.utils.escape_html(r.item_name || "")}</td>
                        <td>${frappe.utils.escape_html(r.uom || "")}</td>
                        <td class="picker-qty-cell">${r.qty}</td>
                        <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                        <td class="picker-money-cell">${this.fmt_money(r.amount)}</td>
                        <td>${r.bill_date || r.posting_date || "-"}</td>
                        <td class="picker-money-cell cell-row-amt"><strong>${this.fmt_money(r.net_available_amount)}</strong></td>
                        <td>${render_linked_badges(r.linked_rr_names, "reimbursement-request")}</td>
                    `;
                }
            }

            tr_html += `</tr>`;
            $tbody.append(tr_html);
        });
    }

    render_table_footer() {
        const stage = this.active_stage;
        const mode = this.view_modes[stage] || "detail";
        const is_all_company = this.active_company === "All";
        let total_qty = 0;
        let total_amt = 0;

        this.table_data.forEach((r) => {
            if (this.locked_company && r.company !== this.locked_company) return;
            total_qty += flt(r.pending_qty || r.qty || r.total_qty || 0);
            total_amt += flt(r.estimated_amount || r.pending_amount || r.net_available_amount || r.amount || 0);
        });

        let prefix_cols = is_all_company ? 3 : 2;
        let foot_html = `
            <tr>
                <td colspan="${prefix_cols}" class="picker-col-sticky-foot">
                    合计 (共 ${this.table_data.length} 笔)
                </td>
        `;

        if (stage === "item_to_mr") {
            if (mode === "doc") {
                foot_html += `<td colspan="4"></td><td class="picker-qty-cell">${total_qty.toFixed(2)}</td><td colspan="2"></td>`;
            } else {
                foot_html += `<td colspan="5"></td><td class="picker-qty-cell">${total_qty.toFixed(2)}</td><td colspan="2"></td>`;
            }
        } else if (stage === "mr_to_po") {
            if (mode === "doc") {
                foot_html += `
                    <td colspan="5"></td>
                    <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                    <td colspan="2"></td>
                `;
            } else {
                foot_html += `
                    <td colspan="5"></td>
                    <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                    <td colspan="3"></td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt * 0.13)}</td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt * 1.13)}</td>
                    <td colspan="3"></td>
                `;
            }
        } else if (stage === "po_to_pr") {
            if (mode === "doc") {
                foot_html += `
                    <td colspan="6"></td>
                    <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                    <td colspan="2"></td>
                `;
            } else {
                foot_html += `
                    <td colspan="5"></td>
                    <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                    <td colspan="2"></td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                `;
            }
        } else if (stage === "pr_to_pi") {
            if (mode === "doc") {
                foot_html += `
                    <td colspan="4"></td>
                    <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                    <td colspan="2"></td>
                `;
            } else {
                foot_html += `
                    <td colspan="4"></td>
                    <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                    <td colspan="2"></td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                    <td></td>
                `;
            }
        } else if (stage === "pi_to_rr") {
            if (mode === "doc") {
                foot_html += `
                    <td colspan="6"></td>
                    <td colspan="2"></td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                `;
            } else {
                foot_html += `
                    <td colspan="4"></td>
                    <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                    <td colspan="2"></td>
                    <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                `;
            }
        }

        foot_html += `</tr>`;
        $("#picker-table-tfoot").html(foot_html);
    }

    update_company_lock_ui(is_locking = false) {
        if (is_locking && this.locked_company && this.active_company === "All") {
            frappe.show_alert({
                message: __("💡 已按【{0}】锁定选单生单范围（已自动隐藏其他公司明细，取消勾选后恢复全量视图）", [frappe.utils.escape_html(this.locked_company)]),
                indicator: "orange"
            }, 5);
        }
    }

    update_table_visibility_by_lock() {
        const self = this;
        $("#picker-table-tbody tr").each(function () {
            const comp = $(this).attr("data-company");
            if (self.locked_company && comp !== self.locked_company) {
                $(this).addClass("picker-row-company-hidden");
            } else {
                $(this).removeClass("picker-row-company-hidden");
            }
        });
        this.render_table_footer();
    }

    update_row_amount_display($tr, row) {
        if (!row) return;
        const rate = flt(row.rate);
        const this_qty = flt(row.this_qty);
        const new_amt = flt(rate * this_qty, 2);
        if (row.estimated_amount !== undefined) row.estimated_amount = new_amt;
        if (row.pending_amount !== undefined) row.pending_amount = new_amt;
        $tr.find(".cell-row-amt").text(this.fmt_money(new_amt));
    }

    update_action_summary() {
        const $bar = $("#picker-action-bar");
        const stage = this.active_stage;
        const mode = this.view_modes[stage] || "detail";
        const cfg = this.stages_config[stage];
        const sel_count = this.selected_map.size;

        let total_sel_amt = 0;
        this.selected_map.forEach((item) => {
            const rate = flt(item.rate);
            const qty = flt(item.this_qty || item.pending_qty || 1);
            if (item.net_available_amount !== undefined) {
                total_sel_amt += flt(item.net_available_amount);
            } else if (item.estimated_amount !== undefined && mode === "doc") {
                total_sel_amt += flt(item.estimated_amount);
            } else if (item.pending_amount !== undefined && mode === "doc") {
                total_sel_amt += flt(item.pending_amount);
            } else {
                total_sel_amt += flt(rate * qty, 2);
            }
        });

        let target_comp_suffix = "";
        if (this.locked_company) {
            target_comp_suffix = `【${this.locked_company}】`;
        } else if (this.active_company !== "All") {
            target_comp_suffix = `【${this.active_company}】`;
        }

        const view_switch_html = `
            <div class="picker-view-switch-group">
                <button class="picker-view-btn ${mode === 'detail' ? 'active' : ''}" data-mode="detail">📑 明细视图</button>
                <button class="picker-view-btn ${mode === 'doc' ? 'active' : ''}" data-mode="doc">📦 单号视图</button>
            </div>
        `;

        if (stage === "item_to_mr") {
            const html = `
                <div class="picker-summary-text">
                    ${view_switch_html}
                    <span>已选 <strong class="picker-summary-highlight">${sel_count}</strong> 项</span>
                </div>
                <div class="picker-btn-group">
                    <button class="picker-btn-secondary" id="picker-select-all-btn">全选本页</button>
                    <button class="picker-btn-secondary" id="picker-clear-sel-btn">清空选择</button>
                    <button class="picker-btn-secondary" id="picker-batch-delete-btn" ${sel_count === 0 ? 'disabled' : ''}>🗑️ 删除所选</button>
                    <button class="picker-btn-create-mr" id="picker-create-mr-btn">
                        <span>➕</span>
                        <span>新建物料申请单</span>
                    </button>
                </div>
            `;
            $bar.html(html);
            this.update_header_checkbox_state();
            return;
        }

        const count_unit = mode === "doc" ? "单" : "行";

        const html = `
            <div class="picker-summary-text">
                ${view_switch_html}
                <span>已选 <strong class="picker-summary-highlight">${sel_count}</strong> ${count_unit}</span>
                <span>本次总计: <strong class="picker-summary-highlight">${this.fmt_money(total_sel_amt)}</strong></span>
            </div>
            <div class="picker-btn-group">
                <button class="picker-btn-secondary" id="picker-select-all-btn">全选本页</button>
                <button class="picker-btn-secondary" id="picker-clear-sel-btn">清空选择</button>
                <button class="picker-btn-secondary" id="picker-batch-delete-btn" ${sel_count === 0 ? 'disabled' : ''}>🗑️ 删除所选</button>
                <button class="picker-btn-primary" id="picker-submit-btn" ${sel_count === 0 ? 'disabled' : ''}>
                    ${cfg.btn_label}${target_comp_suffix}
                </button>
            </div>
        `;
        $bar.html(html);
        this.update_header_checkbox_state();
    }

    update_header_checkbox_state() {
        const $hdr_cb = $("#picker-select-all-header");
        if (!$hdr_cb.length) return;
        const visible_rows = (this.table_data || []).filter(r => !this.locked_company || r.company === this.locked_company);
        const total_visible = visible_rows.length;
        const sel_count = this.selected_map.size;
        const el = $hdr_cb[0];

        if (total_visible > 0 && sel_count >= total_visible) {
            el.checked = true;
            el.indeterminate = false;
        } else if (sel_count > 0) {
            el.checked = false;
            el.indeterminate = true;
        } else {
            el.checked = false;
            el.indeterminate = false;
        }
    }

    select_all_visible() {
        const self = this;

        if (this.active_company === "All" && !this.locked_company) {
            const first_visible = this.table_data.find((r) => !self.locked_company || r.company === self.locked_company);
            if (first_visible) {
                this.locked_company = first_visible.company;
                this.update_company_lock_ui(true);
            }
        }

        this.table_data.forEach((r) => {
            if (self.locked_company && r.company !== self.locked_company) return;
            const key = self.get_row_key(r);
            self.selected_map.set(key, r);
        });

        this.render_table_rows();
        this.update_table_visibility_by_lock();
        this.update_action_summary();
    }

    clear_selection() {
        this.selected_map.clear();
        this.locked_company = null;
        this.update_company_lock_ui();
        this.render_table_rows();
        this.update_table_visibility_by_lock();
        this.update_action_summary();
    }

    fill_max_quantities() {
        const self = this;
        this.table_data.forEach((r) => {
            if (self.locked_company && r.company !== self.locked_company) return;
            const max_qty = flt(r.pending_qty || r.qty);
            r.this_qty = max_qty;
            const key = self.get_row_key(r);
            if (self.selected_map.has(key)) {
                self.selected_map.get(key).this_qty = max_qty;
            }
        });
        this.render_table_rows();
        this.update_action_summary();
    }

    sync_scroll_widths() {
        const table_width = $("#picker-data-table").outerWidth() || 1200;
        $("#picker-top-scrollbar-inner").width(table_width);
    }

    fmt_money(val) {
        return `¥ ${flt(val || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    open_create_mr_dialog() {
        const default_company = this.active_company !== "All" ? this.active_company : (this.companies[0] || "");
        const default_schedule_date = (typeof frappe !== "undefined" && frappe.datetime && frappe.datetime.add_months)
            ? frappe.datetime.add_months(frappe.datetime.nowdate(), 1)
            : "";
        let rows_data = [
            { item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" }
        ];

        const recalculate_row_state = (r) => {
            const qty = flt(r.qty) || 0.0;
            const rate = flt(r.rate) || 0.0;
            r.amount = Math.round(qty * rate * 100) / 100;
            const tax_pct = flt(r.tax_rate) || 0.0;
            r.tax_amount = Math.round(r.amount * (tax_pct / 100.0) * 100) / 100;
            r.total_amount = Math.round((r.amount + r.tax_amount) * 100) / 100;
        };

        const update_bottom_summary = ($wrapper) => {
            let sum_qty = 0;
            let sum_amount = 0;
            let sum_tax = 0;
            let sum_total = 0;
            rows_data.forEach((r) => {
                sum_qty += flt(r.qty);
                sum_amount += flt(r.amount);
                sum_tax += flt(r.tax_amount);
                sum_total += flt(r.total_amount);
            });
            $wrapper.find("#modal-sum-qty").text(sum_qty.toFixed(2));
            $wrapper.find("#modal-sum-amt").text(this.fmt_money(sum_amount));
            $wrapper.find("#modal-sum-tax").text(this.fmt_money(sum_tax));
            $wrapper.find("#modal-sum-total").text(this.fmt_money(sum_total));
        };

        const recalculate_and_sync_row = ($tr, field_changed, $wrap) => {
            const idx = parseInt($tr.attr("data-idx"));
            const r = rows_data[idx];
            if (!r) return;

            let qty = flt($tr.find(".modal-input-qty").val());
            if (isNaN(qty) || qty < 0) qty = 0;

            let rate = flt($tr.find(".modal-input-rate").val());
            if (isNaN(rate) || rate < 0) rate = 0;

            let amount = flt($tr.find(".modal-input-amount").val());
            if (isNaN(amount) || amount < 0) amount = 0;

            let tax_rate = flt($tr.find(".modal-input-tax-rate").val());
            if (isNaN(tax_rate) || tax_rate < 0) tax_rate = 0;

            let tax_amount = flt($tr.find(".modal-input-tax-amount").val());
            if (isNaN(tax_amount) || tax_amount < 0) tax_amount = 0;

            let total_amount = flt($tr.find(".modal-input-total-amount").val());
            if (isNaN(total_amount) || total_amount < 0) total_amount = 0;

            if (field_changed === "qty" || field_changed === "rate") {
                amount = Math.round(qty * rate * 100) / 100;
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tr.find(".modal-input-amount").val(amount.toFixed(2));
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "tax_rate") {
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "amount") {
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $tr.find(".modal-input-rate").val(rate);
                }
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "tax_amount") {
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                if (amount > 0) {
                    tax_rate = Math.round((tax_amount / amount) * 10000) / 100;
                    $tr.find(".modal-input-tax-rate").val(tax_rate);
                }
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "total_amount") {
                amount = Math.round((total_amount / (1 + tax_rate / 100.0)) * 100) / 100;
                tax_amount = Math.round((total_amount - amount) * 100) / 100;
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $tr.find(".modal-input-rate").val(rate);
                }
                $tr.find(".modal-input-amount").val(amount.toFixed(2));
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
            }

            r.qty = qty;
            r.rate = rate;
            r.amount = amount;
            r.tax_rate = tax_rate;
            r.tax_amount = tax_amount;
            r.total_amount = total_amount;

            update_bottom_summary($wrap);
        };

        const render_rows = (dialog) => {
            const $wrapper = dialog.get_field("items_html").$wrapper;
            const $tbody = $wrapper.find("#picker-modal-item-tbody");
            $tbody.empty();

            rows_data.forEach((row, idx) => {
                recalculate_row_state(row);

                const tr = $(`
                    <tr data-idx="${idx}">
                        <td class="picker-modal-cell-center">${idx + 1}</td>
                        <td>
                            <div class="picker-suggest-wrapper">
                                <input type="text" class="modal-input-code" placeholder="输入物料代码..." value="${frappe.utils.escape_html(row.item_code || '')}">
                                <div class="picker-suggest-dropdown" id="suggest-dd-${idx}"></div>
                            </div>
                        </td>
                        <td>
                            <input type="text" class="modal-input-name modal-input-readonly" readonly tabindex="-1" placeholder="自动带出物料名称..." value="${frappe.utils.escape_html(row.item_name || '')}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-spec modal-input-readonly" readonly tabindex="-1" placeholder="自动带出规格型号..." value="${frappe.utils.escape_html(row.spec || '')}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-qty" value="${row.qty}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-rate" value="${row.rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-amount" value="${flt(row.amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" max="100" class="modal-input-tax-rate" value="${row.tax_rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-tax-amount" value="${flt(row.tax_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-total-amount" value="${flt(row.total_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-remarks" placeholder="备注说明..." value="${frappe.utils.escape_html(row.description || '')}">
                        </td>
                        <td class="picker-modal-cell-center">
                            <button class="picker-modal-del-btn" data-idx="${idx}">删除</button>
                        </td>
                    </tr>
                `);
                $tbody.append(tr);
            });

            update_bottom_summary($wrapper);
        };

        const d = new frappe.ui.Dialog({
            title: __("➕ 新建物料申请单 (Material Request)"),
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "company",
                    label: __("所属公司"),
                    options: this.companies.join("\n"),
                    default: default_company,
                    reqd: 1,
                },
                {
                    fieldtype: "Date",
                    fieldname: "schedule_date",
                    label: __("期望到货日期"),
                    default: default_schedule_date,
                    reqd: 1,
                },
                {
                    fieldtype: "Section Break",
                    label: __("申请物料明细与税额核算"),
                },
                {
                    fieldtype: "HTML",
                    fieldname: "items_html",
                    options: `
                        <div>
                            <table class="picker-modal-item-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>物料代码</th>
                                        <th>物料名称</th>
                                        <th>规格</th>
                                        <th>数量</th>
                                        <th>参考单价</th>
                                        <th>不含税金额</th>
                                        <th>税率 %</th>
                                        <th>税额</th>
                                        <th>含税总价</th>
                                        <th>备注</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="picker-modal-item-tbody"></tbody>
                            </table>
                            <button class="picker-modal-add-btn" id="picker-modal-add-row-btn">➕ 添加一行物料</button>

                            <div class="picker-modal-summary-bar">
                                <span>合计汇总:</span>
                                <div class="picker-modal-summary-items">
                                    <span>申请总数: <strong id="modal-sum-qty" class="picker-summary-highlight">0</strong></span>
                                    <span>不含税金额: <strong id="modal-sum-amt" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>税额: <strong id="modal-sum-tax" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>含税总额: <strong id="modal-sum-total" class="picker-summary-highlight">¥ 0.00</strong></span>
                                </div>
                            </div>
                        </div>
                    `,
                },
            ],
            primary_action_label: __("🚀 正式提交物料申请单"),
            primary_action: async () => {
                const vals = d.get_values();
                if (!vals) return;

                const valid_items = rows_data.filter((r) => (r.item_code || "").trim().length > 0);
                if (!valid_items.length) {
                    frappe.msgprint(__("请至少填写一行有效的物料代码。"));
                    return;
                }

                try {
                    frappe.dom.freeze(__("正在创建并正式提交采购申请单..."));
                    const res = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.quick_create_material_request",
                        args: {
                            company: vals.company,
                            schedule_date: vals.schedule_date,
                            items: valid_items,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (res && res.message && res.message.success) {
                        d.hide();
                        frappe.show_alert({
                            message: __("🎉 成功创建并正式发布采购申请单：{0}", [res.message.name]),
                            indicator: "green",
                        });
                        this.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("创建采购申请单失败"));
                }
            },
        });

        d.$wrapper.addClass("picker-create-mr-modal");
        d.show();
        render_rows(d);

        const $wrap = d.get_field("items_html").$wrapper;

        $wrap.on("click", "#picker-modal-add-row-btn", () => {
            rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("click", ".picker-modal-del-btn", function () {
            const idx = parseInt($(this).attr("data-idx"));
            rows_data.splice(idx, 1);
            if (!rows_data.length) rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        // Autocomplete Search on item input
        let search_timeout = null;
        $wrap.on("input focus", ".modal-input-code", function () {
            const $input = $(this);
            const idx = parseInt($input.closest("tr").attr("data-idx"));
            const $dd = $wrap.find(`#suggest-dd-${idx}`);
            const query = $input.val();

            clearTimeout(search_timeout);
            search_timeout = setTimeout(async () => {
                const comp = d.get_value("company") || default_company;
                try {
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.search_picker_items",
                        args: { query: query, company: comp },
                    });
                    const items = (r && r.message && r.message.items) || [];
                    let dd_html = "";
                    items.forEach((it) => {
                        dd_html += `
                            <div class="picker-suggest-item" data-code="${frappe.utils.escape_html(it.item_code)}" data-name="${frappe.utils.escape_html(it.item_name)}" data-rate="${it.rate}" data-uom="${it.uom}" data-tax="${it.tax_rate}">
                                <div class="picker-suggest-main">
                                    <span class="picker-suggest-code">${frappe.utils.escape_html(it.item_code)}</span>
                                    <span class="picker-suggest-name">${frappe.utils.escape_html(it.item_name)} (${it.uom})</span>
                                </div>
                                <div class="picker-suggest-price">¥ ${flt(it.rate).toFixed(2)}</div>
                            </div>
                        `;
                    });

                    dd_html += `
                        <div class="picker-suggest-create-btn" id="modal-create-new-item-btn">
                            <span>➕</span>
                            <span>新建物料 (Create Item)</span>
                        </div>
                    `;

                    $dd.html(dd_html).addClass("is-open");

                    // Direct Fixed positioning on top of the viewport
                    const input_el = $input[0];
                    if (input_el) {
                        const rect = input_el.getBoundingClientRect();
                        $dd.css({
                            top: (rect.bottom + 2) + "px",
                            left: rect.left + "px",
                            width: Math.max(rect.width, 380) + "px",
                        });
                    }
                } catch (err) {
                    console.error("Autocomplete search error", err);
                }
            }, 250);
        });

        // Close dropdown when scrolling modal body
        $wrap.closest(".modal-body").off("scroll.picker_suggest").on("scroll.picker_suggest", () => {
            $wrap.find(".picker-suggest-dropdown.is-open").removeClass("is-open");
        });

        // Select an item from dropdown
        $wrap.on("click", ".picker-suggest-item", function () {
            const $tr = $(this).closest("tr");
            const idx = parseInt($tr.attr("data-idx"));
            const code = $(this).attr("data-code");
            const name = $(this).attr("data-name");
            const uom = $(this).attr("data-uom");
            const rate = flt($(this).attr("data-rate"));
            const tax = flt($(this).attr("data-tax")) || 13.0;

            rows_data[idx].item_code = code;
            rows_data[idx].item_name = name;
            rows_data[idx].spec = uom || "";
            rows_data[idx].rate = rate;
            rows_data[idx].tax_rate = tax;

            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            render_rows(d);
        });

        // Quick create item click
        $wrap.on("click", "#modal-create-new-item-btn", function () {
            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            frappe.new_doc("Item");
        });

        // Close dropdown when clicking outside
        $(document).off("click.picker_suggest").on("click.picker_suggest", (e) => {
            if (!$(e.target).closest(".picker-suggest-wrapper").length && !$(e.target).closest(".picker-suggest-dropdown").length) {
                $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            }
        });

        // Live text and calculation event bindings
        $wrap.on("input change", ".modal-input-code", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            if (rows_data[idx]) {
                rows_data[idx].item_code = $(this).val().trim();
            }
        });

        $wrap.on("input change", ".modal-input-name", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].item_name = $(this).val();
        });

        $wrap.on("input change", ".modal-input-spec", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].spec = $(this).val();
        });

        $wrap.on("input change", ".modal-input-remarks", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].description = $(this).val();
        });

        $wrap.on("input change", ".modal-input-qty", function () {
            recalculate_and_sync_row($(this).closest("tr"), "qty", $wrap);
        });

        $wrap.on("input change", ".modal-input-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-total-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "total_amount", $wrap);
        });
    }

    async execute_primary_action() {
        const stage = this.active_stage;
        const mode = this.view_modes[stage] || "detail";
        const selected_items = Array.from(this.selected_map.values());
        if (!selected_items.length) {
            frappe.msgprint(__("请至少选择一项记录。"));
            return;
        }

        const target_comp = this.locked_company || (this.active_company !== "All" ? this.active_company : selected_items[0].company);

        if (stage === "mr_to_po") {
            this.open_create_po_from_mr_dialog(selected_items, target_comp);
        } else if (stage === "po_to_pr") {
            this.open_create_pr_from_po_dialog(selected_items, target_comp);
        } else if (stage === "pr_to_pi") {
            this.open_create_pi_from_pr_dialog(selected_items, target_comp);
        } else if (stage === "pi_to_rr") {
            this.open_create_rr_from_pi_dialog(selected_items, target_comp);
        }
    }

    show_generation_success_dialog(doc_title, docs_created, route_prefix) {
        if (!docs_created || !docs_created.length) return;
        const self = this;

        const dt_map = {
            "purchase-order": "Purchase Order",
            "purchase-receipt": "Purchase Receipt",
            "purchase-invoice": "Purchase Invoice",
            "reimbursement-request": "Reimbursement Request",
        };
        const dt_name = dt_map[route_prefix] || "Purchase Order";

        let items_html = docs_created
            .map(
                (d) => `
            <div class="picker-dialog-doc-item">
                <div class="picker-dialog-doc-main">
                    <span class="picker-source-docname picker-doc-clickable-link" data-doctype="${dt_name}" data-name="${frappe.utils.escape_html(d.name)}" title="点击就地弹窗查看与修改">
                        <strong>${frappe.utils.escape_html(d.name)}</strong>
                    </span>
                    ${d.supplier ? `<span class="picker-summary-highlight">(${frappe.utils.escape_html(d.supplier)})</span>` : ''}
                    ${d.company ? `<span class="picker-company-badge">[${frappe.utils.escape_html(d.company)}]</span>` : ''}
                </div>
                <div class="picker-dialog-doc-stats">
                    <span>数量: <strong>${d.total_qty || d.item_count}</strong></span>
                    ${d.grand_total ? `<span>金额: <strong>${this.fmt_money(d.grand_total)}</strong></span>` : ''}
                </div>
            </div>
        `
            )
            .join("");

        const d = new frappe.ui.Dialog({
            title: __("🎉 成功生成 {0} 张{1}", [docs_created.length, doc_title]),
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "result_html",
                    options: `
                        <div class="picker-dialog-desc">
                            已成功为您生成以下单据，您可以点击单号就地弹窗查看与修改：
                        </div>
                        <div class="picker-dialog-list">
                            ${items_html}
                        </div>
                    `,
                },
            ],
            primary_action_label: __("🔍 就地查看第一张单据"),
            primary_action: () => {
                d.hide();
                self.show_doc_detail_modal(dt_name, docs_created[0].name);
            },
        });

        d.show();

        d.$wrapper.on("click", ".picker-doc-clickable-link", function (e) {
            e.preventDefault();
            const dt = $(this).attr("data-doctype");
            const nm = $(this).attr("data-name");
            d.hide();
            self.show_doc_detail_modal(dt, nm);
        });
    }

    async show_doc_detail_modal(doctype, name) {
        if (!doctype || !name) return;
        frappe.dom.freeze(__("正在加载单据详情..."));
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.get_document_details",
                args: { doctype: doctype, name: name },
            });
            frappe.dom.unfreeze();
            if (!r || !r.message) return;
            const doc = r.message;
            this.render_doc_detail_dialog(doc);
        } catch (e) {
            frappe.dom.unfreeze();
            frappe.msgprint(e.message || __("加载单据失败"));
        }
    }

    render_doc_detail_dialog(doc) {
        const self = this;
        const doctype_labels = {
            "Material Request": "采购申请单",
            "Purchase Order": "采购订单",
            "Purchase Receipt": "采购入库单",
            "Purchase Invoice": "采购发票",
            "Reimbursement Request": "报销申请单",
        };
        const dt_label = doctype_labels[doc.doctype] || doc.doctype;

        // Build item rows
        let items_tbody_html = "";
        (doc.items || []).forEach((it) => {
            items_tbody_html += `
                <tr>
                    <td class="picker-cell-center">${it.idx}</td>
                    <td><strong>${frappe.utils.escape_html(it.item_code)}</strong></td>
                    <td>${frappe.utils.escape_html(it.item_name)}</td>
                    <td>${frappe.utils.escape_html(it.spec || "-")}</td>
                    <td>${frappe.utils.escape_html(it.uom || "-")}</td>
                    <td class="picker-qty-cell"><strong>${flt(it.qty).toFixed(2)}</strong></td>
                    <td class="picker-money-cell">${self.fmt_money(it.rate)}</td>
                    <td class="picker-money-cell">${self.fmt_money(it.amount)}</td>
                    <td class="picker-cell-right">${it.tax_rate ? (it.tax_rate + '%') : '-'}</td>
                    <td class="picker-money-cell">${self.fmt_money(it.tax_amount)}</td>
                    <td class="picker-money-cell"><strong>${self.fmt_money(it.total_amount)}</strong></td>
                    <td>${frappe.utils.escape_html(it.description || "-")}</td>
                </tr>
            `;
        });

        if (!items_tbody_html) {
            items_tbody_html = `<tr><td colspan="12" class="picker-doc-empty-state">无物料明细数据</td></tr>`;
        }

        // Build upstream flow items
        let upstream_html = "";
        (doc.linked_upstream || []).forEach((u) => {
            upstream_html += `
                <span class="picker-doc-flow-item upstream picker-doc-modal-link" data-doctype="${u.doctype}" data-name="${u.name}" title="点击查看详情">
                    <span>⬆️ ${u.doctype_label}:</span>
                    <strong>${frappe.utils.escape_html(u.name)}</strong>
                    <span class="ashan-status-badge ashan-status-blue">${frappe.utils.escape_html(u.status || "")}</span>
                </span>
            `;
        });

        // Build downstream flow items
        let downstream_html = "";
        (doc.linked_downstream || []).forEach((d) => {
            downstream_html += `
                <span class="picker-doc-flow-item downstream picker-doc-modal-link" data-doctype="${d.doctype}" data-name="${d.name}" title="点击查看详情">
                    <span>⬇️ ${d.doctype_label}:</span>
                    <strong>${frappe.utils.escape_html(d.name)}</strong>
                    <span class="ashan-status-badge ashan-status-green">${frappe.utils.escape_html(d.status || "")}</span>
                </span>
            `;
        });

        const flow_section_html = (upstream_html || downstream_html) ? `
            <div class="picker-doc-flow-card">
                <div class="picker-doc-flow-title">🔗 上下游业务全链路追溯</div>
                <div class="picker-doc-flow-list">
                    ${upstream_html}
                    ${downstream_html}
                </div>
            </div>
        ` : `
            <div class="picker-doc-flow-card">
                <div class="picker-doc-flow-title picker-flow-empty-hint">🔗 当前单据无关联上下游单据（独立单据）</div>
            </div>
        `;

        const comp_badge_cls = (doc.company || "").includes("祺富") ? "picker-company-badge-qifu" : "picker-company-badge-jizhong";

        const modal_content = `
            <div class="picker-doc-modal-container">
                <!-- Meta Info Card -->
                <div class="picker-doc-meta-card">
                    <div class="picker-doc-meta-header">
                        <div class="picker-doc-title-box">
                            <span class="picker-doc-title-text">${dt_label}: ${frappe.utils.escape_html(doc.name)}</span>
                            <span class="picker-company-badge ${comp_badge_cls}">${frappe.utils.escape_html(doc.company)}</span>
                            <span class="ashan-status-badge ashan-status-blue">${frappe.utils.escape_html(doc.status)}</span>
                        </div>
                        <div>
                            <span class="picker-meta-owner-text">录单人: ${frappe.utils.escape_html(doc.owner || "-")}</span>
                        </div>
                    </div>
                    <div class="picker-doc-meta-grid">
                        <div class="picker-doc-meta-item">
                            <span class="picker-doc-meta-label">单据日期</span>
                            <span class="picker-doc-meta-val">${doc.date || "-"}</span>
                        </div>
                        <div class="picker-doc-meta-item">
                            <span class="picker-doc-meta-label">${doc.supplier ? '供应商' : '需求部门'}</span>
                            <span class="picker-doc-meta-val">${frappe.utils.escape_html(doc.supplier || doc.department || "-")}</span>
                        </div>
                        <div class="picker-doc-meta-item">
                            <span class="picker-doc-meta-label">物料总数量</span>
                            <span class="picker-doc-meta-val">${doc.total_qty}</span>
                        </div>
                        <div class="picker-doc-meta-item">
                            <span class="picker-doc-meta-label">单据总金额</span>
                            <span class="picker-doc-meta-val picker-meta-val-highlight">${self.fmt_money(doc.grand_total)}</span>
                        </div>
                    </div>
                </div>

                <!-- Items Table -->
                <div class="picker-doc-table-box">
                    <table class="picker-doc-modal-table">
                        <thead>
                            <tr>
                                <th class="picker-cell-col-idx">#</th>
                                <th>物料代码</th>
                                <th>物料名称</th>
                                <th>规格</th>
                                <th>单位</th>
                                <th class="picker-cell-right">数量</th>
                                <th class="picker-cell-right">单价</th>
                                <th class="picker-cell-right">金额</th>
                                <th class="picker-cell-right">税率</th>
                                <th class="picker-cell-right">税额</th>
                                <th class="picker-cell-right">价税合计</th>
                                <th>备注</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${items_tbody_html}
                        </tbody>
                    </table>
                </div>

                <!-- Flow Traceability -->
                ${flow_section_html}

                <!-- Action Toolbar -->
                <div class="picker-modal-footer-bar">
                    <div>
                        ${doc.can_delete ? `
                            <button class="picker-btn-danger-del" id="picker-modal-del-btn">
                                🗑️ 删除单据
                            </button>
                        ` : `
                            <span class="picker-no-delete-perm-hint">(当前账号无删除权限)</span>
                        `}
                    </div>
                    <div class="picker-modal-actions-right">
                        ${doc.can_quick_edit ? `
                            <button class="picker-btn-action-view" id="picker-modal-edit-btn">
                                ✏️ 修改${dt_label}
                            </button>
                        ` : ''}
                        <button class="picker-btn-action-view" id="picker-modal-print-btn">
                            🖨️ 打印单据
                        </button>
                        <button class="picker-btn-action-view" id="picker-modal-goto-form-btn">
                            ✏️ 完整编辑页面
                        </button>
                    </div>
                </div>
            </div>
        `;

        const d = new frappe.ui.Dialog({
            title: __("🔍 单据详情与操作 · {0} {1}", [dt_label, doc.name]),
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "detail_html",
                    options: modal_content,
                }
            ],
            size: "large",
        });

        d.$wrapper.addClass("picker-doc-detail-modal");
        d.show();

        const $w = d.$wrapper;

        // Goto Form page button
        $w.on("click", "#picker-modal-goto-form-btn", function () {
            d.hide();
            frappe.set_route("Form", doc.doctype, doc.name);
        });

        // Edit button inside modal
        $w.on("click", "#picker-modal-edit-btn", function () {
            if (doc.doctype === "Material Request") {
                self.open_edit_mr_dialog(doc, d);
            } else if (doc.doctype === "Purchase Order") {
                self.open_edit_po_dialog(doc, d);
            }
        });

        // Flow link clicks inside modal
        $w.on("click", ".picker-doc-modal-link", function () {
            const dt = $(this).attr("data-doctype");
            const nm = $(this).attr("data-name");
            d.hide();
            self.show_doc_detail_modal(dt, nm);
        });

        // Print button
        $w.on("click", "#picker-modal-print-btn", function () {
            const print_url = `/printview?doctype=${encodeURIComponent(doc.doctype)}&name=${encodeURIComponent(doc.name)}&trigger_print=1`;
            window.open(print_url, "_blank");
        });

        // Delete button
        $w.on("click", "#picker-modal-del-btn", function () {
            self.handle_document_deletion(doc.doctype, doc.name, d);
        });
    }

    open_edit_mr_dialog(doc, parent_dialog) {
        const default_company = doc.company || this.companies[0] || "";
        const default_schedule_date = doc.schedule_date || frappe.datetime.add_months(frappe.datetime.nowdate(), 1);
        let rows_data = [];

        (doc.items || []).forEach((it) => {
            rows_data.push({
                item_code: it.item_code || "",
                item_name: it.item_name || "",
                spec: it.custom_item_spec || it.spec || "",
                qty: flt(it.qty) || 1.0,
                rate: flt(it.rate) || 0.0,
                amount: flt(it.amount) || 0.0,
                tax_rate: flt(it.custom_tax_rate !== undefined ? it.custom_tax_rate : (it.tax_rate !== undefined ? it.tax_rate : 13.0)),
                tax_amount: flt(it.custom_tax_amount !== undefined ? it.custom_tax_amount : (it.tax_amount || 0.0)),
                total_amount: flt(it.custom_total_amount !== undefined ? it.custom_total_amount : (it.total_amount || 0.0)),
                description: it.description || "",
            });
        });

        if (!rows_data.length) {
            rows_data.push({
                item_code: "",
                item_name: "",
                spec: "",
                qty: 1.0,
                rate: 0.0,
                amount: 0.0,
                tax_rate: 13.0,
                tax_amount: 0.0,
                total_amount: 0.0,
                description: "",
            });
        }

        const recalculate_row_state = (r) => {
            const qty = flt(r.qty) || 0.0;
            const rate = flt(r.rate) || 0.0;
            r.amount = Math.round(qty * rate * 100) / 100;
            const tax_pct = flt(r.tax_rate) || 0.0;
            r.tax_amount = Math.round(r.amount * (tax_pct / 100.0) * 100) / 100;
            r.total_amount = Math.round((r.amount + r.tax_amount) * 100) / 100;
        };

        const update_bottom_summary = ($wrapper) => {
            let sum_qty = 0;
            let sum_amount = 0;
            let sum_tax = 0;
            let sum_total = 0;
            rows_data.forEach((r) => {
                sum_qty += flt(r.qty);
                sum_amount += flt(r.amount);
                sum_tax += flt(r.tax_amount);
                sum_total += flt(r.total_amount);
            });
            $wrapper.find("#modal-sum-qty").text(sum_qty.toFixed(2));
            $wrapper.find("#modal-sum-amt").text(this.fmt_money(sum_amount));
            $wrapper.find("#modal-sum-tax").text(this.fmt_money(sum_tax));
            $wrapper.find("#modal-sum-total").text(this.fmt_money(sum_total));
        };

        const recalculate_and_sync_row = ($tr, field_changed, $wrap) => {
            const idx = parseInt($tr.attr("data-idx"));
            const r = rows_data[idx];
            if (!r) return;

            let qty = flt($tr.find(".modal-input-qty").val());
            if (isNaN(qty) || qty < 0) qty = 0;

            let rate = flt($tr.find(".modal-input-rate").val());
            if (isNaN(rate) || rate < 0) rate = 0;

            let amount = flt($tr.find(".modal-input-amount").val());
            if (isNaN(amount) || amount < 0) amount = 0;

            let tax_rate = flt($tr.find(".modal-input-tax-rate").val());
            if (isNaN(tax_rate) || tax_rate < 0) tax_rate = 0;

            let tax_amount = flt($tr.find(".modal-input-tax-amount").val());
            if (isNaN(tax_amount) || tax_amount < 0) tax_amount = 0;

            let total_amount = flt($tr.find(".modal-input-total-amount").val());
            if (isNaN(total_amount) || total_amount < 0) total_amount = 0;

            if (field_changed === "qty" || field_changed === "rate") {
                amount = Math.round(qty * rate * 100) / 100;
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tr.find(".modal-input-amount").val(amount.toFixed(2));
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "tax_rate") {
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "amount") {
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $tr.find(".modal-input-rate").val(rate);
                }
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "tax_amount") {
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                if (amount > 0) {
                    tax_rate = Math.round((tax_amount / amount) * 10000) / 100;
                    $tr.find(".modal-input-tax-rate").val(tax_rate);
                }
                $tr.find(".modal-input-total-amount").val(total_amount.toFixed(2));
            } else if (field_changed === "total_amount") {
                amount = Math.round((total_amount / (1 + tax_rate / 100.0)) * 100) / 100;
                tax_amount = Math.round((total_amount - amount) * 100) / 100;
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $tr.find(".modal-input-rate").val(rate);
                }
                $tr.find(".modal-input-amount").val(amount.toFixed(2));
                $tr.find(".modal-input-tax-amount").val(tax_amount.toFixed(2));
            }

            r.qty = qty;
            r.rate = rate;
            r.amount = amount;
            r.tax_rate = tax_rate;
            r.tax_amount = tax_amount;
            r.total_amount = total_amount;

            update_bottom_summary($wrap);
        };

        const render_rows = (dialog) => {
            const $wrapper = dialog.get_field("items_html").$wrapper;
            const $tbody = $wrapper.find("#picker-modal-item-tbody");
            $tbody.empty();

            rows_data.forEach((r, idx) => {
                recalculate_row_state(r);

                const tr = `
                    <tr data-idx="${idx}">
                        <td class="picker-cell-col-idx">${idx + 1}</td>
                        <td>
                            <div class="picker-suggest-wrapper">
                                <input type="text" class="modal-input-code" placeholder="输入物料代码..." value="${frappe.utils.escape_html(r.item_code || '')}">
                                <div class="picker-suggest-dropdown" id="suggest-dd-${idx}"></div>
                            </div>
                        </td>
                        <td>
                            <input type="text" class="modal-input-name modal-input-readonly" readonly tabindex="-1" placeholder="自动带出物料名称..." value="${frappe.utils.escape_html(r.item_name || '')}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-spec modal-input-readonly" readonly tabindex="-1" placeholder="自动带出规格型号..." value="${frappe.utils.escape_html(r.spec || '')}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-qty" value="${r.qty}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-rate" value="${r.rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-amount" value="${flt(r.amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" max="100" class="modal-input-tax-rate" value="${r.tax_rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-tax-amount" value="${flt(r.tax_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-total-amount" value="${flt(r.total_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-remarks" placeholder="备注说明..." value="${frappe.utils.escape_html(r.description || '')}">
                        </td>
                        <td class="picker-modal-cell-center">
                            <button class="picker-modal-del-btn" data-idx="${idx}">删除</button>
                        </td>
                    </tr>
                `;
                $tbody.append(tr);
            });

            update_bottom_summary($wrapper);
        };

        const d = new frappe.ui.Dialog({
            title: __("✏️ 修改物料申请单 · {0}", [doc.name]),
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "company",
                    label: __("所属公司"),
                    options: this.companies.join("\n"),
                    default: default_company,
                    reqd: 1,
                },
                {
                    fieldtype: "Date",
                    fieldname: "schedule_date",
                    label: __("期望到货日期"),
                    default: default_schedule_date,
                    reqd: 1,
                },
                {
                    fieldtype: "Section Break",
                    label: __("申请物料明细与税额核算 (任意修改)"),
                },
                {
                    fieldtype: "HTML",
                    fieldname: "items_html",
                    options: `
                        <div>
                            <table class="picker-modal-item-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>物料代码</th>
                                        <th>物料名称</th>
                                        <th>规格</th>
                                        <th>数量</th>
                                        <th>参考单价</th>
                                        <th>不含税金额</th>
                                        <th>税率 %</th>
                                        <th>税额</th>
                                        <th>含税总价</th>
                                        <th>备注</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="picker-modal-item-tbody"></tbody>
                            </table>
                            <button class="picker-modal-add-btn" id="picker-modal-add-row-btn">➕ 添加一行物料</button>

                            <div class="picker-modal-summary-bar">
                                <span>合计汇总:</span>
                                <div class="picker-modal-summary-items">
                                    <span>申请总数: <strong id="modal-sum-qty" class="picker-summary-highlight">0</strong></span>
                                    <span>不含税金额: <strong id="modal-sum-amt" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>税额: <strong id="modal-sum-tax" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>含税总额: <strong id="modal-sum-total" class="picker-summary-highlight">¥ 0.00</strong></span>
                                </div>
                            </div>
                        </div>
                    `,
                },
            ],
            primary_action_label: __("💾 保存修改并正式发布"),
            primary_action: async () => {
                const vals = d.get_values();
                if (!vals) return;

                const valid_items = rows_data.filter((r) => (r.item_code || "").trim().length > 0);
                if (!valid_items.length) {
                    frappe.msgprint(__("请至少保留一行有效的物料代码。"));
                    return;
                }

                try {
                    frappe.dom.freeze(__("正在更新采购申请单..."));
                    const res = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.update_quick_material_request",
                        args: {
                            name: doc.name,
                            company: vals.company,
                            schedule_date: vals.schedule_date,
                            items: valid_items,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (res && res.message && res.message.success) {
                        d.hide();
                        if (parent_dialog) parent_dialog.hide();
                        frappe.show_alert({
                            message: __("🎉 成功更新并正式发布采购申请单：{0}", [doc.name]),
                            indicator: "green",
                        });
                        this.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("更新采购申请单失败"));
                }
            },
        });

        d.$wrapper.addClass("picker-create-mr-modal");
        d.show();
        render_rows(d);

        const $wrap = d.get_field("items_html").$wrapper;

        $wrap.on("click", "#picker-modal-add-row-btn", () => {
            rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("click", ".picker-modal-del-btn", function () {
            const idx = parseInt($(this).attr("data-idx"));
            rows_data.splice(idx, 1);
            if (!rows_data.length) rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        // Autocomplete Search on item input
        let search_timeout = null;
        $wrap.on("input focus", ".modal-input-code", function () {
            const $input = $(this);
            const idx = parseInt($input.closest("tr").attr("data-idx"));
            const $dd = $wrap.find(`#suggest-dd-${idx}`);
            const query = $input.val();

            clearTimeout(search_timeout);
            search_timeout = setTimeout(async () => {
                const comp = d.get_value("company") || default_company;
                try {
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.search_picker_items",
                        args: { query: query, company: comp },
                    });
                    const items = (r && r.message && r.message.items) || [];
                    let dd_html = "";
                    items.forEach((it) => {
                        dd_html += `
                            <div class="picker-suggest-item" data-code="${frappe.utils.escape_html(it.item_code)}" data-name="${frappe.utils.escape_html(it.item_name)}" data-rate="${it.rate}" data-uom="${it.uom}" data-tax="${it.tax_rate}">
                                <div class="picker-suggest-main">
                                    <span class="picker-suggest-code">${frappe.utils.escape_html(it.item_code)}</span>
                                    <span class="picker-suggest-name">${frappe.utils.escape_html(it.item_name)} (${it.uom})</span>
                                </div>
                                <div class="picker-suggest-price">¥ ${flt(it.rate).toFixed(2)}</div>
                            </div>
                        `;
                    });

                    dd_html += `
                        <div class="picker-suggest-create-btn" id="modal-create-new-item-btn">
                            <span>➕</span>
                            <span>新建物料 (Create Item)</span>
                        </div>
                    `;

                    $dd.html(dd_html).addClass("is-open");

                    // Direct Fixed positioning on top of the viewport
                    const input_el = $input[0];
                    if (input_el) {
                        const rect = input_el.getBoundingClientRect();
                        $dd.css({
                            top: (rect.bottom + 2) + "px",
                            left: rect.left + "px",
                            width: Math.max(rect.width, 380) + "px",
                        });
                    }
                } catch (err) {
                    console.error("Autocomplete search error", err);
                }
            }, 250);
        });

        // Close dropdown when scrolling modal body
        $wrap.closest(".modal-body").off("scroll.picker_suggest_edit").on("scroll.picker_suggest_edit", () => {
            $wrap.find(".picker-suggest-dropdown.is-open").removeClass("is-open");
        });

        // Select an item from dropdown
        $wrap.on("click", ".picker-suggest-item", function () {
            const $tr = $(this).closest("tr");
            const idx = parseInt($tr.attr("data-idx"));
            const code = $(this).attr("data-code");
            const name = $(this).attr("data-name");
            const uom = $(this).attr("data-uom");
            const rate = flt($(this).attr("data-rate"));
            const tax = flt($(this).attr("data-tax")) || 13.0;

            rows_data[idx].item_code = code;
            rows_data[idx].item_name = name;
            rows_data[idx].spec = uom || "";
            rows_data[idx].rate = rate;
            rows_data[idx].tax_rate = tax;

            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            render_rows(d);
        });

        // Quick create item click
        $wrap.on("click", "#modal-create-new-item-btn", function () {
            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            frappe.new_doc("Item");
        });

        // Close dropdown when clicking outside
        $(document).off("click.picker_suggest_edit").on("click.picker_suggest_edit", (e) => {
            if (!$(e.target).closest(".picker-suggest-wrapper").length && !$(e.target).closest(".picker-suggest-dropdown").length) {
                $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            }
        });

        // Live text and calculation event bindings
        $wrap.on("input change", ".modal-input-code", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            if (rows_data[idx]) {
                rows_data[idx].item_code = $(this).val().trim();
            }
        });

        $wrap.on("input change", ".modal-input-name", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].item_name = $(this).val();
        });

        $wrap.on("input change", ".modal-input-spec", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].spec = $(this).val();
        });

        $wrap.on("input change", ".modal-input-remarks", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].description = $(this).val();
        });

        $wrap.on("input change", ".modal-input-qty", function () {
            recalculate_and_sync_row($(this).closest("tr"), "qty", $wrap);
        });

        $wrap.on("input change", ".modal-input-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-total-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "total_amount", $wrap);
        });
    }

    open_edit_po_dialog(doc, parent_dialog) {
        const default_company = doc.company;
        const default_supplier = doc.supplier || "";
        const default_schedule_date = doc.schedule_date || doc.date || frappe.datetime.get_today();

        let rows_data = (doc.items || []).map((it) => ({
            item_code: it.item_code || "",
            item_name: it.item_name || "",
            spec: it.spec || "",
            qty: flt(it.qty) || 1.0,
            rate: flt(it.rate) || 0.0,
            amount: flt(it.amount) || flt(it.qty * it.rate) || 0.0,
            tax_rate: flt(it.tax_rate) || 13.0,
            tax_amount: flt(it.tax_amount) || 0.0,
            total_amount: flt(it.total_amount) || 0.0,
            description: it.description || "",
        }));

        if (!rows_data.length) {
            rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
        }

        const recalculate_row_state = (r) => {
            const qty = flt(r.qty) || 0.0;
            const rate = flt(r.rate) || 0.0;
            r.amount = Math.round(qty * rate * 100) / 100;
            const tax_pct = flt(r.tax_rate) || 0.0;
            r.tax_amount = Math.round(r.amount * (tax_pct / 100.0) * 100) / 100;
            r.total_amount = Math.round((r.amount + r.tax_amount) * 100) / 100;
        };

        const update_bottom_summary = ($wrapper) => {
            let total_qty = 0;
            let total_amt = 0;
            let total_tax = 0;
            let grand_total = 0;
            $wrapper.find("#picker-modal-item-tbody tr").each(function () {
                const q = flt($(this).find(".modal-input-qty").val()) || 0;
                const a = flt($(this).find(".modal-input-amount").val()) || 0;
                const tx = flt($(this).find(".modal-input-tax-amount").val()) || 0;
                const tot = flt($(this).find(".modal-input-total-amount").val()) || 0;
                total_qty += q;
                total_amt += a;
                total_tax += tx;
                grand_total += tot;
            });
            $wrapper.find("#modal-sum-qty").text(total_qty.toFixed(2));
            $wrapper.find("#modal-sum-amt").text(this.fmt_money(total_amt));
            $wrapper.find("#modal-sum-tax").text(this.fmt_money(total_tax));
            $wrapper.find("#modal-sum-total").text(this.fmt_money(grand_total));
        };

        const recalculate_and_sync_row = ($tr, field_changed, $wrapper) => {
            const idx = parseInt($tr.attr("data-idx"));
            const $qty = $tr.find(".modal-input-qty");
            const $rate = $tr.find(".modal-input-rate");
            const $amount = $tr.find(".modal-input-amount");
            const $tax_rate = $tr.find(".modal-input-tax-rate");
            const $tax_amount = $tr.find(".modal-input-tax-amount");
            const $total_amount = $tr.find(".modal-input-total-amount");

            let qty = flt($qty.val()) || 0.0;
            let rate = flt($rate.val()) || 0.0;
            let amount = flt($amount.val()) || 0.0;
            let tax_rate = flt($tax_rate.val()) || 0.0;
            let tax_amount = flt($tax_amount.val()) || 0.0;
            let total_amount = flt($total_amount.val()) || 0.0;

            if (field_changed === "qty" || field_changed === "rate") {
                amount = Math.round(qty * rate * 100) / 100;
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_rate") {
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "amount") {
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_amount") {
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $total_amount.val(total_amount.toFixed(2));
                if (amount > 0) {
                    tax_rate = Math.round((tax_amount / amount) * 10000) / 100;
                    $tax_rate.val(tax_rate);
                }
            } else if (field_changed === "total_amount") {
                amount = Math.round((total_amount / (1 + tax_rate / 100.0)) * 100) / 100;
                tax_amount = Math.round((total_amount - amount) * 100) / 100;
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
            }

            if (rows_data[idx]) {
                rows_data[idx].qty = qty;
                rows_data[idx].rate = rate;
                rows_data[idx].amount = amount;
                rows_data[idx].tax_rate = tax_rate;
                rows_data[idx].tax_amount = tax_amount;
                rows_data[idx].total_amount = total_amount;
            }

            update_bottom_summary($wrapper);
        };

        const render_rows = (dialog) => {
            const $wrapper = dialog.get_field("items_html").$wrapper;
            const $tbody = $wrapper.find("#picker-modal-item-tbody");
            $tbody.empty();

            rows_data.forEach((r, idx) => {
                recalculate_row_state(r);
                const tr = `
                    <tr data-idx="${idx}">
                        <td class="picker-modal-cell-center">${idx + 1}</td>
                        <td class="picker-suggest-wrapper">
                            <input type="text" class="modal-input-code" placeholder="物料代码/搜索..." value="${frappe.utils.escape_html(r.item_code || '')}">
                            <div class="picker-suggest-dropdown" id="suggest-dd-po-edit-${idx}"></div>
                        </td>
                        <td>
                            <input type="text" class="modal-input-name" placeholder="物料名称..." value="${frappe.utils.escape_html(r.item_name || '')}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-spec" placeholder="规格型号..." value="${frappe.utils.escape_html(r.spec || '')}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0.0001" class="modal-input-qty" value="${r.qty}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-rate" value="${r.rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-amount" value="${flt(r.amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" max="100" class="modal-input-tax-rate" value="${r.tax_rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-tax-amount" value="${flt(r.tax_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-total-amount" value="${flt(r.total_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-remarks" placeholder="备注说明..." value="${frappe.utils.escape_html(r.description || '')}">
                        </td>
                        <td class="picker-modal-cell-center">
                            <button class="picker-modal-del-btn" data-idx="${idx}">删除</button>
                        </td>
                    </tr>
                `;
                $tbody.append(tr);
            });

            update_bottom_summary($wrapper);
        };

        const d = new frappe.ui.Dialog({
            title: __("✏️ 修改采购订单 · {0}", [doc.name]),
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "company",
                    label: __("所属公司"),
                    options: this.companies.join("\n"),
                    default: default_company,
                    read_only: 1,
                },
                {
                    fieldtype: "Link",
                    options: "Supplier",
                    fieldname: "supplier",
                    label: __("供应商"),
                    default: default_supplier,
                    reqd: 1,
                },
                {
                    fieldtype: "Date",
                    fieldname: "schedule_date",
                    label: __("期望到货日期"),
                    default: default_schedule_date,
                    reqd: 1,
                },
                {
                    fieldtype: "Section Break",
                    label: __("采购订单物料明细与税额核算 (任意修改)"),
                },
                {
                    fieldtype: "HTML",
                    fieldname: "items_html",
                    options: `
                        <div>
                            <table class="picker-modal-item-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>物料代码</th>
                                        <th>物料名称</th>
                                        <th>规格</th>
                                        <th>数量</th>
                                        <th>参考单价</th>
                                        <th>不含税金额</th>
                                        <th>税率 %</th>
                                        <th>税额</th>
                                        <th>含税总价</th>
                                        <th>备注</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="picker-modal-item-tbody"></tbody>
                            </table>
                            <button class="picker-modal-add-btn" id="picker-modal-add-row-btn">➕ 添加一行物料</button>

                            <div class="picker-modal-summary-bar">
                                <span>合计汇总:</span>
                                <div class="picker-modal-summary-items">
                                    <span>采购总数: <strong id="modal-sum-qty" class="picker-summary-highlight">0</strong></span>
                                    <span>不含税金额: <strong id="modal-sum-amt" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>税额: <strong id="modal-sum-tax" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>含税总额: <strong id="modal-sum-total" class="picker-summary-highlight">¥ 0.00</strong></span>
                                </div>
                            </div>
                        </div>
                    `,
                },
            ],
            primary_action_label: __("💾 保存修改并正式发布"),
            primary_action: async () => {
                const vals = d.get_values();
                if (!vals) return;

                const valid_items = rows_data.filter((r) => (r.item_code || "").trim().length > 0);
                if (!valid_items.length) {
                    frappe.msgprint(__("请至少保留一行有效的物料代码。"));
                    return;
                }

                try {
                    frappe.dom.freeze(__("正在更新采购订单..."));
                    const res = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.update_quick_purchase_order",
                        args: {
                            name: doc.name,
                            supplier: vals.supplier,
                            schedule_date: vals.schedule_date,
                            items: valid_items,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (res && res.message && res.message.success) {
                        d.hide();
                        if (parent_dialog) parent_dialog.hide();
                        frappe.show_alert({
                            message: __("🎉 成功更新并正式发布采购订单：{0}", [doc.name]),
                            indicator: "green",
                        });
                        this.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("更新采购订单失败"));
                }
            },
        });

        d.$wrapper.addClass("picker-create-mr-modal");
        d.show();
        render_rows(d);

        const $wrap = d.get_field("items_html").$wrapper;

        $wrap.on("click", "#picker-modal-add-row-btn", () => {
            rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("click", ".picker-modal-del-btn", function () {
            const idx = parseInt($(this).attr("data-idx"));
            rows_data.splice(idx, 1);
            if (!rows_data.length) rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        // Autocomplete Search on item input
        let search_timeout = null;
        $wrap.on("input focus", ".modal-input-code", function () {
            const $input = $(this);
            const idx = parseInt($input.closest("tr").attr("data-idx"));
            const $dd = $wrap.find(`#suggest-dd-po-edit-${idx}`);
            const query = $input.val();

            clearTimeout(search_timeout);
            search_timeout = setTimeout(async () => {
                const comp = d.get_value("company") || default_company;
                try {
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.search_picker_items",
                        args: { query: query, company: comp },
                    });
                    const items = (r && r.message && r.message.items) || [];
                    let dd_html = "";
                    items.forEach((it) => {
                        dd_html += `
                            <div class="picker-suggest-item" data-code="${frappe.utils.escape_html(it.item_code)}" data-name="${frappe.utils.escape_html(it.item_name)}" data-rate="${it.rate}" data-uom="${it.uom}" data-tax="${it.tax_rate}">
                                <div class="picker-suggest-main">
                                    <span class="picker-suggest-code">${frappe.utils.escape_html(it.item_code)}</span>
                                    <span class="picker-suggest-name">${frappe.utils.escape_html(it.item_name)} (${it.uom})</span>
                                </div>
                                <div class="picker-suggest-price">¥ ${flt(it.rate).toFixed(2)}</div>
                            </div>
                        `;
                    });

                    dd_html += `
                        <div class="picker-suggest-create-btn" id="modal-create-new-item-po-btn">
                            <span>➕</span>
                            <span>新建物料 (Create Item)</span>
                        </div>
                    `;

                    $dd.html(dd_html).addClass("is-open");

                    const input_el = $input[0];
                    if (input_el) {
                        const rect = input_el.getBoundingClientRect();
                        $dd.css({
                            top: (rect.bottom + 2) + "px",
                            left: rect.left + "px",
                            width: Math.max(rect.width, 380) + "px",
                        });
                    }
                } catch (err) {
                    console.error("Autocomplete search error", err);
                }
            }, 250);
        });

        // Close dropdown when scrolling modal body
        $wrap.closest(".modal-body").off("scroll.picker_suggest_po_edit").on("scroll.picker_suggest_po_edit", () => {
            $wrap.find(".picker-suggest-dropdown.is-open").removeClass("is-open");
        });

        // Pick item from dropdown
        $wrap.on("click", ".picker-suggest-item", function () {
            const $tr = $(this).closest("tr");
            const idx = parseInt($tr.attr("data-idx"));
            const code = $(this).attr("data-code");
            const name = $(this).attr("data-name");
            const uom = $(this).attr("data-uom");
            const rate = flt($(this).attr("data-rate"));
            const tax = flt($(this).attr("data-tax")) || 13.0;

            rows_data[idx].item_code = code;
            rows_data[idx].item_name = name;
            rows_data[idx].spec = uom || "";
            rows_data[idx].rate = rate;
            rows_data[idx].tax_rate = tax;

            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            render_rows(d);
        });

        // Quick create item click
        $wrap.on("click", "#modal-create-new-item-po-btn", function () {
            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            frappe.new_doc("Item");
        });

        // Close dropdown when clicking outside
        $(document).off("click.picker_suggest_po_out").on("click.picker_suggest_po_out", (e) => {
            if (!$(e.target).closest(".picker-suggest-wrapper").length && !$(e.target).closest(".picker-suggest-dropdown").length) {
                $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            }
        });

        // Live text and calculation event bindings
        $wrap.on("input change", ".modal-input-code", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            if (rows_data[idx]) {
                rows_data[idx].item_code = $(this).val().trim();
            }
        });

        $wrap.on("input change", ".modal-input-name", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].item_name = $(this).val();
        });

        $wrap.on("input change", ".modal-input-spec", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].spec = $(this).val();
        });

        $wrap.on("input change", ".modal-input-remarks", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].description = $(this).val();
        });

        $wrap.on("input change", ".modal-input-qty", function () {
            recalculate_and_sync_row($(this).closest("tr"), "qty", $wrap);
        });

        $wrap.on("input change", ".modal-input-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-total-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "total_amount", $wrap);
        });
    }

    open_create_po_from_mr_dialog(selected_items, target_comp) {
        const self = this;
        const sup_override = $("#picker-opt-supplier").val() || "";
        const default_supplier = sup_override || selected_items[0].supplier || "";
        const default_schedule_date = selected_items[0].schedule_date || frappe.datetime.get_today();

        let rows_data = selected_items.map((it) => {
            const q = flt(it.this_qty || it.pending_qty || it.qty || 1.0);
            const r = flt(it.rate || 0.0);
            const a = Math.round(q * r * 100) / 100;
            const tx_pct = flt(it.tax_rate) || 13.0;
            const tx_amt = Math.round(a * (tx_pct / 100.0) * 100) / 100;
            const tot = Math.round((a + tx_amt) * 100) / 100;
            return {
                mri_name: it.mri_name || it.name,
                mr_name: it.mr_name || it.parent,
                item_code: it.item_code || "",
                item_name: it.item_name || "",
                spec: it.spec || "",
                qty: q,
                rate: r,
                amount: a,
                tax_rate: tx_pct,
                tax_amount: tx_amt,
                total_amount: tot,
                description: it.description || "",
            };
        });

        const recalculate_row_state = (r) => {
            const qty = flt(r.qty) || 0.0;
            const rate = flt(r.rate) || 0.0;
            r.amount = Math.round(qty * rate * 100) / 100;
            const tax_pct = flt(r.tax_rate) || 0.0;
            r.tax_amount = Math.round(r.amount * (tax_pct / 100.0) * 100) / 100;
            r.total_amount = Math.round((r.amount + r.tax_amount) * 100) / 100;
        };

        const update_bottom_summary = ($wrapper) => {
            let total_qty = 0;
            let total_amt = 0;
            let total_tax = 0;
            let grand_total = 0;
            $wrapper.find("#picker-modal-item-tbody tr").each(function () {
                const q = flt($(this).find(".modal-input-qty").val()) || 0;
                const a = flt($(this).find(".modal-input-amount").val()) || 0;
                const tx = flt($(this).find(".modal-input-tax-amount").val()) || 0;
                const tot = flt($(this).find(".modal-input-total-amount").val()) || 0;
                total_qty += q;
                total_amt += a;
                total_tax += tx;
                grand_total += tot;
            });
            $wrapper.find("#modal-sum-qty").text(total_qty.toFixed(2));
            $wrapper.find("#modal-sum-amt").text(this.fmt_money(total_amt));
            $wrapper.find("#modal-sum-tax").text(this.fmt_money(total_tax));
            $wrapper.find("#modal-sum-total").text(this.fmt_money(grand_total));
        };

        const recalculate_and_sync_row = ($tr, field_changed, $wrapper) => {
            const idx = parseInt($tr.attr("data-idx"));
            const $qty = $tr.find(".modal-input-qty");
            const $rate = $tr.find(".modal-input-rate");
            const $amount = $tr.find(".modal-input-amount");
            const $tax_rate = $tr.find(".modal-input-tax-rate");
            const $tax_amount = $tr.find(".modal-input-tax-amount");
            const $total_amount = $tr.find(".modal-input-total-amount");

            let qty = flt($qty.val()) || 0.0;
            let rate = flt($rate.val()) || 0.0;
            let amount = flt($amount.val()) || 0.0;
            let tax_rate = flt($tax_rate.val()) || 0.0;
            let tax_amount = flt($tax_amount.val()) || 0.0;
            let total_amount = flt($total_amount.val()) || 0.0;

            if (field_changed === "qty" || field_changed === "rate") {
                amount = Math.round(qty * rate * 100) / 100;
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_rate") {
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "amount") {
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_amount") {
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $total_amount.val(total_amount.toFixed(2));
                if (amount > 0) {
                    tax_rate = Math.round((tax_amount / amount) * 10000) / 100;
                    $tax_rate.val(tax_rate);
                }
            } else if (field_changed === "total_amount") {
                amount = Math.round((total_amount / (1 + tax_rate / 100.0)) * 100) / 100;
                tax_amount = Math.round((total_amount - amount) * 100) / 100;
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
            }

            if (rows_data[idx]) {
                rows_data[idx].qty = qty;
                rows_data[idx].rate = rate;
                rows_data[idx].amount = amount;
                rows_data[idx].tax_rate = tax_rate;
                rows_data[idx].tax_amount = tax_amount;
                rows_data[idx].total_amount = total_amount;
            }

            update_bottom_summary($wrapper);
        };

        const render_rows = (dialog) => {
            const $wrapper = dialog.get_field("items_html").$wrapper;
            const $tbody = $wrapper.find("#picker-modal-item-tbody");
            $tbody.empty();

            rows_data.forEach((r, idx) => {
                recalculate_row_state(r);
                const tr = `
                    <tr data-idx="${idx}">
                        <td class="picker-modal-cell-center">${idx + 1}</td>
                        <td class="picker-suggest-wrapper">
                            <input type="text" class="modal-input-code" placeholder="物料代码/搜索..." value="${frappe.utils.escape_html(r.item_code || '')}">
                            <div class="picker-suggest-dropdown" id="suggest-dd-po-create-${idx}"></div>
                        </td>
                        <td>
                            <input type="text" class="modal-input-name modal-input-readonly" readonly tabindex="-1" placeholder="物料名称..." value="${frappe.utils.escape_html(r.item_name || '')}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-spec modal-input-readonly" readonly tabindex="-1" placeholder="规格型号..." value="${frappe.utils.escape_html(r.spec || '')}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0.0001" class="modal-input-qty" value="${r.qty}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-rate" value="${r.rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-amount" value="${flt(r.amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" max="100" class="modal-input-tax-rate" value="${r.tax_rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-tax-amount" value="${flt(r.tax_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-total-amount" value="${flt(r.total_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-remarks" placeholder="备注说明..." value="${frappe.utils.escape_html(r.description || '')}">
                        </td>
                        <td class="picker-modal-cell-center">
                            <button class="picker-modal-del-btn" data-idx="${idx}">删除</button>
                        </td>
                    </tr>
                `;
                $tbody.append(tr);
            });

            update_bottom_summary($wrapper);
        };

        const d = new frappe.ui.Dialog({
            title: __("🚀 新建采购订单 · 选单创建与明细核算"),
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "company",
                    label: __("所属公司"),
                    options: this.companies.join("\n"),
                    default: target_comp,
                    read_only: 1,
                },
                {
                    fieldtype: "Link",
                    options: "Supplier",
                    fieldname: "supplier",
                    label: __("供应商"),
                    default: default_supplier,
                    reqd: 1,
                },
                {
                    fieldtype: "Date",
                    fieldname: "schedule_date",
                    label: __("期望到货日期"),
                    default: default_schedule_date,
                    reqd: 1,
                },
                {
                    fieldtype: "Section Break",
                    label: __("采购订单物料明细与税额核算 (可任意调整)"),
                },
                {
                    fieldtype: "HTML",
                    fieldname: "items_html",
                    options: `
                        <div>
                            <table class="picker-modal-item-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>物料代码</th>
                                        <th>物料名称</th>
                                        <th>规格</th>
                                        <th>数量</th>
                                        <th>参考单价</th>
                                        <th>不含税金额</th>
                                        <th>税率 %</th>
                                        <th>税额</th>
                                        <th>含税总价</th>
                                        <th>备注</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="picker-modal-item-tbody"></tbody>
                            </table>
                            <button class="picker-modal-add-btn" id="picker-modal-add-row-btn">➕ 添加一行物料</button>

                            <div class="picker-modal-summary-bar">
                                <span>合计汇总:</span>
                                <div class="picker-modal-summary-items">
                                    <span>采购总数: <strong id="modal-sum-qty" class="picker-summary-highlight">0</strong></span>
                                    <span>不含税金额: <strong id="modal-sum-amt" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>税额: <strong id="modal-sum-tax" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>含税总额: <strong id="modal-sum-total" class="picker-summary-highlight">¥ 0.00</strong></span>
                                </div>
                            </div>
                        </div>
                    `,
                },
            ],
            primary_action_label: __("🚀 立即生成并正式提交采购订单"),
            primary_action: async () => {
                const vals = d.get_values();
                if (!vals) return;

                const valid_items = rows_data.filter((r) => (r.item_code || "").trim().length > 0);
                if (!valid_items.length) {
                    frappe.msgprint(__("请至少保留一行有效的物料代码。"));
                    return;
                }

                try {
                    frappe.dom.freeze(__("正在生成采购订单..."));
                    const res = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_orders_from_mr_items",
                        args: {
                            company: target_comp,
                            selected_items: valid_items,
                            supplier_override: vals.supplier,
                            schedule_date: vals.schedule_date,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (res && res.message && res.message.success) {
                        d.hide();
                        self.show_generation_success_dialog("采购订单", res.message.orders, "purchase-order");
                        self.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成采购订单失败"));
                }
            },
        });

        d.$wrapper.addClass("picker-create-mr-modal");
        d.show();
        render_rows(d);

        const $wrap = d.get_field("items_html").$wrapper;

        $wrap.on("click", "#picker-modal-add-row-btn", () => {
            rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("click", ".picker-modal-del-btn", function () {
            const idx = parseInt($(this).attr("data-idx"));
            rows_data.splice(idx, 1);
            if (!rows_data.length) rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        // Autocomplete search on item input
        let search_timeout = null;
        $wrap.on("input focus", ".modal-input-code", function () {
            const $input = $(this);
            const idx = parseInt($input.closest("tr").attr("data-idx"));
            const $dd = $wrap.find(`#suggest-dd-po-create-${idx}`);
            const query = $input.val();

            clearTimeout(search_timeout);
            search_timeout = setTimeout(async () => {
                const comp = d.get_value("company") || target_comp;
                try {
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.search_picker_items",
                        args: { query: query, company: comp },
                    });
                    const items = (r && r.message && r.message.items) || [];
                    let dd_html = "";
                    items.forEach((it) => {
                        dd_html += `
                            <div class="picker-suggest-item" data-code="${frappe.utils.escape_html(it.item_code)}" data-name="${frappe.utils.escape_html(it.item_name)}" data-rate="${it.rate}" data-uom="${it.uom}" data-tax="${it.tax_rate}">
                                <div class="picker-suggest-main">
                                    <span class="picker-suggest-code">${frappe.utils.escape_html(it.item_code)}</span>
                                    <span class="picker-suggest-name">${frappe.utils.escape_html(it.item_name)} (${it.uom})</span>
                                </div>
                                <div class="picker-suggest-price">¥ ${flt(it.rate).toFixed(2)}</div>
                            </div>
                        `;
                    });

                    dd_html += `
                        <div class="picker-suggest-create-btn" id="modal-create-new-item-po-gen-btn">
                            <span>➕</span>
                            <span>新建物料 (Create Item)</span>
                        </div>
                    `;

                    $dd.html(dd_html).addClass("is-open");

                    const input_el = $input[0];
                    if (input_el) {
                        const rect = input_el.getBoundingClientRect();
                        $dd.css({
                            top: (rect.bottom + 2) + "px",
                            left: rect.left + "px",
                            width: Math.max(rect.width, 380) + "px",
                        });
                    }
                } catch (err) {
                    console.error("Autocomplete search error", err);
                }
            }, 250);
        });

        // Close dropdown when scrolling modal body
        $wrap.closest(".modal-body").off("scroll.picker_suggest_po_gen").on("scroll.picker_suggest_po_gen", () => {
            $wrap.find(".picker-suggest-dropdown.is-open").removeClass("is-open");
        });

        // Pick item from dropdown
        $wrap.on("click", ".picker-suggest-item", function () {
            const $tr = $(this).closest("tr");
            const idx = parseInt($tr.attr("data-idx"));
            const code = $(this).attr("data-code");
            const name = $(this).attr("data-name");
            const uom = $(this).attr("data-uom");
            const rate = flt($(this).attr("data-rate"));
            const tax = flt($(this).attr("data-tax")) || 13.0;

            rows_data[idx].item_code = code;
            rows_data[idx].item_name = name;
            rows_data[idx].spec = uom || "";
            rows_data[idx].rate = rate;
            rows_data[idx].tax_rate = tax;

            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            render_rows(d);
        });

        // Quick create item click
        $wrap.on("click", "#modal-create-new-item-po-gen-btn", function () {
            $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            frappe.new_doc("Item");
        });

        // Close dropdown when clicking outside
        $(document).off("click.picker_suggest_po_gen_out").on("click.picker_suggest_po_gen_out", (e) => {
            if (!$(e.target).closest(".picker-suggest-wrapper").length && !$(e.target).closest(".picker-suggest-dropdown").length) {
                $wrap.find(".picker-suggest-dropdown").removeClass("is-open");
            }
        });

        // Live text and calculation event bindings
        $wrap.on("input change", ".modal-input-code", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            if (rows_data[idx]) {
                rows_data[idx].item_code = $(this).val().trim();
            }
        });

        $wrap.on("input change", ".modal-input-name", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].item_name = $(this).val();
        });

        $wrap.on("input change", ".modal-input-spec", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].spec = $(this).val();
        });

        $wrap.on("input change", ".modal-input-remarks", function () {
            const idx = parseInt($(this).closest("tr").attr("data-idx"));
            rows_data[idx].description = $(this).val();
        });

        $wrap.on("input change", ".modal-input-qty", function () {
            recalculate_and_sync_row($(this).closest("tr"), "qty", $wrap);
        });

        $wrap.on("input change", ".modal-input-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_rate", $wrap);
        });

        $wrap.on("input change", ".modal-input-tax-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_amount", $wrap);
        });

        $wrap.on("input change", ".modal-input-total-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "total_amount", $wrap);
        });
    }

    open_create_pr_from_po_dialog(selected_items, target_comp) {
        const self = this;
        const wh_override = $("#picker-opt-warehouse").val() || "";
        const default_supplier = selected_items[0].supplier || "";
        const default_warehouse = wh_override || selected_items[0].warehouse || "";

        let rows_data = selected_items.map((it) => {
            const q = flt(it.this_qty || it.pending_qty || it.qty || 1.0);
            const r = flt(it.rate || 0.0);
            const a = Math.round(q * r * 100) / 100;
            const tx_pct = flt(it.tax_rate) || 13.0;
            const tx_amt = Math.round(a * (tx_pct / 100.0) * 100) / 100;
            const tot = Math.round((a + tx_amt) * 100) / 100;
            return {
                poi_name: it.poi_name || it.name,
                po_name: it.po_name || it.parent,
                item_code: it.item_code || "",
                item_name: it.item_name || "",
                spec: it.spec || "",
                qty: q,
                rate: r,
                amount: a,
                tax_rate: tx_pct,
                tax_amount: tx_amt,
                total_amount: tot,
                warehouse: it.warehouse || default_warehouse,
                description: it.remarks || it.description || "",
            };
        });

        const recalculate_row_state = (r) => {
            const qty = flt(r.qty) || 0.0;
            const rate = flt(r.rate) || 0.0;
            r.amount = Math.round(qty * rate * 100) / 100;
            const tax_pct = flt(r.tax_rate) || 0.0;
            r.tax_amount = Math.round(r.amount * (tax_pct / 100.0) * 100) / 100;
            r.total_amount = Math.round((r.amount + r.tax_amount) * 100) / 100;
        };

        const update_bottom_summary = ($wrapper) => {
            let total_qty = 0;
            let total_amt = 0;
            let total_tax = 0;
            let grand_total = 0;
            $wrapper.find("#picker-modal-item-tbody tr").each(function () {
                const q = flt($(this).find(".modal-input-qty").val()) || 0;
                const a = flt($(this).find(".modal-input-amount").val()) || 0;
                const tx = flt($(this).find(".modal-input-tax-amount").val()) || 0;
                const tot = flt($(this).find(".modal-input-total-amount").val()) || 0;
                total_qty += q;
                total_amt += a;
                total_tax += tx;
                grand_total += tot;
            });
            $wrapper.find("#modal-sum-qty").text(total_qty.toFixed(2));
            $wrapper.find("#modal-sum-amt").text(this.fmt_money(total_amt));
            $wrapper.find("#modal-sum-tax").text(this.fmt_money(total_tax));
            $wrapper.find("#modal-sum-total").text(this.fmt_money(grand_total));
        };

        const recalculate_and_sync_row = ($tr, field_changed, $wrapper) => {
            const idx = parseInt($tr.attr("data-idx"));
            const $qty = $tr.find(".modal-input-qty");
            const $rate = $tr.find(".modal-input-rate");
            const $amount = $tr.find(".modal-input-amount");
            const $tax_rate = $tr.find(".modal-input-tax-rate");
            const $tax_amount = $tr.find(".modal-input-tax-amount");
            const $total_amount = $tr.find(".modal-input-total-amount");

            let qty = flt($qty.val()) || 0.0;
            let rate = flt($rate.val()) || 0.0;
            let amount = flt($amount.val()) || 0.0;
            let tax_rate = flt($tax_rate.val()) || 0.0;
            let tax_amount = flt($tax_amount.val()) || 0.0;
            let total_amount = flt($total_amount.val()) || 0.0;

            if (field_changed === "qty" || field_changed === "rate") {
                amount = Math.round(qty * rate * 100) / 100;
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_rate") {
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "amount") {
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_amount") {
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $total_amount.val(total_amount.toFixed(2));
                if (amount > 0) {
                    tax_rate = Math.round((tax_amount / amount) * 10000) / 100;
                    $tax_rate.val(tax_rate);
                }
            } else if (field_changed === "total_amount") {
                amount = Math.round((total_amount / (1 + tax_rate / 100.0)) * 100) / 100;
                tax_amount = Math.round((total_amount - amount) * 100) / 100;
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
            }

            if (rows_data[idx]) {
                rows_data[idx].qty = qty;
                rows_data[idx].rate = rate;
                rows_data[idx].amount = amount;
                rows_data[idx].tax_rate = tax_rate;
                rows_data[idx].tax_amount = tax_amount;
                rows_data[idx].total_amount = total_amount;
            }

            update_bottom_summary($wrapper);
        };

        const render_rows = (dialog) => {
            const $wrapper = dialog.get_field("items_html").$wrapper;
            const $tbody = $wrapper.find("#picker-modal-item-tbody");
            $tbody.empty();

            rows_data.forEach((r, idx) => {
                recalculate_row_state(r);
                const tr = `
                    <tr data-idx="${idx}">
                        <td class="picker-modal-cell-center">${idx + 1}</td>
                        <td class="picker-suggest-wrapper">
                            <input type="text" class="modal-input-code" placeholder="物料代码/搜索..." value="${frappe.utils.escape_html(r.item_code || '')}">
                            <div class="picker-suggest-dropdown" id="suggest-dd-pr-create-${idx}"></div>
                        </td>
                        <td>
                            <input type="text" class="modal-input-name modal-input-readonly" readonly tabindex="-1" placeholder="物料名称..." value="${frappe.utils.escape_html(r.item_name || '')}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-spec modal-input-readonly" readonly tabindex="-1" placeholder="规格型号..." value="${frappe.utils.escape_html(r.spec || '')}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0.0001" class="modal-input-qty" value="${r.qty}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-rate" value="${r.rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-amount" value="${flt(r.amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" max="100" class="modal-input-tax-rate" value="${r.tax_rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-tax-amount" value="${flt(r.tax_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-total-amount" value="${flt(r.total_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-remarks" placeholder="备注说明..." value="${frappe.utils.escape_html(r.description || '')}">
                        </td>
                        <td class="picker-modal-cell-center">
                            <button class="picker-modal-del-btn" data-idx="${idx}">删除</button>
                        </td>
                    </tr>
                `;
                $tbody.append(tr);
            });

            update_bottom_summary($wrapper);
        };

        const d = new frappe.ui.Dialog({
            title: __("📦 新建采购入库单 · 选单创建与明细核算"),
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "company",
                    label: __("所属公司"),
                    options: this.companies.join("\n"),
                    default: target_comp,
                    read_only: 1,
                },
                {
                    fieldtype: "Link",
                    options: "Supplier",
                    fieldname: "supplier",
                    label: __("供应商"),
                    default: default_supplier,
                    read_only: 1,
                },
                {
                    fieldtype: "Link",
                    options: "Warehouse",
                    fieldname: "warehouse",
                    label: __("入库仓库"),
                    default: default_warehouse,
                    reqd: 1,
                },
                {
                    fieldtype: "Date",
                    fieldname: "posting_date",
                    label: __("过账日期"),
                    default: frappe.datetime.get_today(),
                    reqd: 1,
                },
                {
                    fieldtype: "Section Break",
                    label: __("入库物料明细与核算 (可确认实收数与金额)"),
                },
                {
                    fieldtype: "HTML",
                    fieldname: "items_html",
                    options: `
                        <div>
                            <table class="picker-modal-item-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>物料代码</th>
                                        <th>物料名称</th>
                                        <th>规格</th>
                                        <th>实收数量</th>
                                        <th>参考单价</th>
                                        <th>不含税金额</th>
                                        <th>税率 %</th>
                                        <th>税额</th>
                                        <th>含税总价</th>
                                        <th>备注</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="picker-modal-item-tbody"></tbody>
                            </table>
                            <button class="picker-modal-add-btn" id="picker-modal-add-row-btn">➕ 添加一行物料</button>

                            <div class="picker-modal-summary-bar">
                                <span>合计汇总:</span>
                                <div class="picker-modal-summary-items">
                                    <span>实收总数: <strong id="modal-sum-qty" class="picker-summary-highlight">0</strong></span>
                                    <span>不含税金额: <strong id="modal-sum-amt" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>税额: <strong id="modal-sum-tax" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>含税总额: <strong id="modal-sum-total" class="picker-summary-highlight">¥ 0.00</strong></span>
                                </div>
                            </div>
                        </div>
                    `,
                },
            ],
            primary_action_label: __("🚀 立即生成并正式提交入库单"),
            primary_action: async () => {
                const vals = d.get_values();
                if (!vals) return;

                const valid_items = rows_data.filter((r) => (r.item_code || "").trim().length > 0);
                if (!valid_items.length) {
                    frappe.msgprint(__("请至少保留一行有效的物料代码。"));
                    return;
                }

                try {
                    frappe.dom.freeze(__("正在生成采购入库单..."));
                    const res = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_receipts_from_po_items",
                        args: {
                            company: target_comp,
                            selected_items: valid_items,
                            warehouse_override: vals.warehouse,
                            posting_date: vals.posting_date,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (res && res.message && res.message.success) {
                        d.hide();
                        self.show_generation_success_dialog("采购入库单", res.message.receipts, "purchase-receipt");
                        self.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成采购入库单失败"));
                }
            },
        });

        d.$wrapper.addClass("picker-create-mr-modal");
        d.show();
        render_rows(d);

        const $wrap = d.get_field("items_html").$wrapper;

        $wrap.on("click", "#picker-modal-add-row-btn", () => {
            rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("click", ".picker-modal-del-btn", function () {
            const idx = parseInt($(this).attr("data-idx"));
            rows_data.splice(idx, 1);
            if (!rows_data.length) rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("input change", ".modal-input-qty", function () {
            recalculate_and_sync_row($(this).closest("tr"), "qty", $wrap);
        });
        $wrap.on("input change", ".modal-input-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "rate", $wrap);
        });
        $wrap.on("input change", ".modal-input-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "amount", $wrap);
        });
        $wrap.on("input change", ".modal-input-tax-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_rate", $wrap);
        });
        $wrap.on("input change", ".modal-input-tax-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_amount", $wrap);
        });
        $wrap.on("input change", ".modal-input-total-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "total_amount", $wrap);
        });
    }

    open_create_pi_from_pr_dialog(selected_items, target_comp) {
        const self = this;
        const bill_no_val = $("#picker-opt-bill-no").val() || "";
        const default_supplier = selected_items[0].supplier || "";

        let rows_data = selected_items.map((it) => {
            const q = flt(it.this_qty || it.pending_qty || it.qty || 1.0);
            const r = flt(it.rate || 0.0);
            const a = Math.round(q * r * 100) / 100;
            const tx_pct = flt(it.tax_rate) || 13.0;
            const tx_amt = Math.round(a * (tx_pct / 100.0) * 100) / 100;
            const tot = Math.round((a + tx_amt) * 100) / 100;
            return {
                pri_name: it.pri_name || it.name,
                pr_name: it.pr_name || it.parent,
                item_code: it.item_code || "",
                item_name: it.item_name || "",
                spec: it.spec || "",
                qty: q,
                rate: r,
                amount: a,
                tax_rate: tx_pct,
                tax_amount: tx_amt,
                total_amount: tot,
                description: it.remarks || it.description || "",
            };
        });

        const recalculate_row_state = (r) => {
            const qty = flt(r.qty) || 0.0;
            const rate = flt(r.rate) || 0.0;
            r.amount = Math.round(qty * rate * 100) / 100;
            const tax_pct = flt(r.tax_rate) || 0.0;
            r.tax_amount = Math.round(r.amount * (tax_pct / 100.0) * 100) / 100;
            r.total_amount = Math.round((r.amount + r.tax_amount) * 100) / 100;
        };

        const update_bottom_summary = ($wrapper) => {
            let total_qty = 0;
            let total_amt = 0;
            let total_tax = 0;
            let grand_total = 0;
            $wrapper.find("#picker-modal-item-tbody tr").each(function () {
                const q = flt($(this).find(".modal-input-qty").val()) || 0;
                const a = flt($(this).find(".modal-input-amount").val()) || 0;
                const tx = flt($(this).find(".modal-input-tax-amount").val()) || 0;
                const tot = flt($(this).find(".modal-input-total-amount").val()) || 0;
                total_qty += q;
                total_amt += a;
                total_tax += tx;
                grand_total += tot;
            });
            $wrapper.find("#modal-sum-qty").text(total_qty.toFixed(2));
            $wrapper.find("#modal-sum-amt").text(this.fmt_money(total_amt));
            $wrapper.find("#modal-sum-tax").text(this.fmt_money(total_tax));
            $wrapper.find("#modal-sum-total").text(this.fmt_money(grand_total));
        };

        const recalculate_and_sync_row = ($tr, field_changed, $wrapper) => {
            const idx = parseInt($tr.attr("data-idx"));
            const $qty = $tr.find(".modal-input-qty");
            const $rate = $tr.find(".modal-input-rate");
            const $amount = $tr.find(".modal-input-amount");
            const $tax_rate = $tr.find(".modal-input-tax-rate");
            const $tax_amount = $tr.find(".modal-input-tax-amount");
            const $total_amount = $tr.find(".modal-input-total-amount");

            let qty = flt($qty.val()) || 0.0;
            let rate = flt($rate.val()) || 0.0;
            let amount = flt($amount.val()) || 0.0;
            let tax_rate = flt($tax_rate.val()) || 0.0;
            let tax_amount = flt($tax_amount.val()) || 0.0;
            let total_amount = flt($total_amount.val()) || 0.0;

            if (field_changed === "qty" || field_changed === "rate") {
                amount = Math.round(qty * rate * 100) / 100;
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_rate") {
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "amount") {
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                tax_amount = Math.round(amount * (tax_rate / 100.0) * 100) / 100;
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $tax_amount.val(tax_amount.toFixed(2));
                $total_amount.val(total_amount.toFixed(2));
            } else if (field_changed === "tax_amount") {
                total_amount = Math.round((amount + tax_amount) * 100) / 100;
                $total_amount.val(total_amount.toFixed(2));
                if (amount > 0) {
                    tax_rate = Math.round((tax_amount / amount) * 10000) / 100;
                    $tax_rate.val(tax_rate);
                }
            } else if (field_changed === "total_amount") {
                amount = Math.round((total_amount / (1 + tax_rate / 100.0)) * 100) / 100;
                tax_amount = Math.round((total_amount - amount) * 100) / 100;
                if (qty > 0) {
                    rate = Math.round((amount / qty) * 10000) / 10000;
                    $rate.val(rate);
                }
                $amount.val(amount.toFixed(2));
                $tax_amount.val(tax_amount.toFixed(2));
            }

            if (rows_data[idx]) {
                rows_data[idx].qty = qty;
                rows_data[idx].rate = rate;
                rows_data[idx].amount = amount;
                rows_data[idx].tax_rate = tax_rate;
                rows_data[idx].tax_amount = tax_amount;
                rows_data[idx].total_amount = total_amount;
            }

            update_bottom_summary($wrapper);
        };

        const render_rows = (dialog) => {
            const $wrapper = dialog.get_field("items_html").$wrapper;
            const $tbody = $wrapper.find("#picker-modal-item-tbody");
            $tbody.empty();

            rows_data.forEach((r, idx) => {
                recalculate_row_state(r);
                const tr = `
                    <tr data-idx="${idx}">
                        <td class="picker-modal-cell-center">${idx + 1}</td>
                        <td class="picker-suggest-wrapper">
                            <input type="text" class="modal-input-code" placeholder="物料代码/搜索..." value="${frappe.utils.escape_html(r.item_code || '')}">
                            <div class="picker-suggest-dropdown" id="suggest-dd-pi-create-${idx}"></div>
                        </td>
                        <td>
                            <input type="text" class="modal-input-name modal-input-readonly" readonly tabindex="-1" placeholder="物料名称..." value="${frappe.utils.escape_html(r.item_name || '')}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-spec modal-input-readonly" readonly tabindex="-1" placeholder="规格型号..." value="${frappe.utils.escape_html(r.spec || '')}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0.0001" class="modal-input-qty" value="${r.qty}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-rate" value="${r.rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-amount" value="${flt(r.amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" max="100" class="modal-input-tax-rate" value="${r.tax_rate}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-tax-amount" value="${flt(r.tax_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="number" step="any" min="0" class="modal-input-total-amount" value="${flt(r.total_amount).toFixed(2)}">
                        </td>
                        <td>
                            <input type="text" class="modal-input-remarks" placeholder="备注说明..." value="${frappe.utils.escape_html(r.description || '')}">
                        </td>
                        <td class="picker-modal-cell-center">
                            <button class="picker-modal-del-btn" data-idx="${idx}">删除</button>
                        </td>
                    </tr>
                `;
                $tbody.append(tr);
            });

            update_bottom_summary($wrapper);
        };

        const d = new frappe.ui.Dialog({
            title: __("🧾 新建采购发票 · 选单创建与明细核算"),
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "company",
                    label: __("所属公司"),
                    options: this.companies.join("\n"),
                    default: target_comp,
                    read_only: 1,
                },
                {
                    fieldtype: "Link",
                    options: "Supplier",
                    fieldname: "supplier",
                    label: __("供应商"),
                    default: default_supplier,
                    read_only: 1,
                },
                {
                    fieldtype: "Data",
                    fieldname: "bill_no",
                    label: __("发票号码 (纸质/金税发票)"),
                    default: bill_no_val,
                },
                {
                    fieldtype: "Date",
                    fieldname: "bill_date",
                    label: __("开票日期"),
                    default: frappe.datetime.get_today(),
                    reqd: 1,
                },
                {
                    fieldtype: "Section Break",
                    label: __("发票物料明细与税额核算 (可核对开票数量与税额)"),
                },
                {
                    fieldtype: "HTML",
                    fieldname: "items_html",
                    options: `
                        <div>
                            <table class="picker-modal-item-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>物料代码</th>
                                        <th>物料名称</th>
                                        <th>规格</th>
                                        <th>开票数量</th>
                                        <th>单价</th>
                                        <th>不含税金额</th>
                                        <th>税率 %</th>
                                        <th>税额</th>
                                        <th>含税总价</th>
                                        <th>备注</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="picker-modal-item-tbody"></tbody>
                            </table>
                            <button class="picker-modal-add-btn" id="picker-modal-add-row-btn">➕ 添加一行物料</button>

                            <div class="picker-modal-summary-bar">
                                <span>合计汇总:</span>
                                <div class="picker-modal-summary-items">
                                    <span>开票总数: <strong id="modal-sum-qty" class="picker-summary-highlight">0</strong></span>
                                    <span>不含税金额: <strong id="modal-sum-amt" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>税额: <strong id="modal-sum-tax" class="picker-summary-highlight">¥ 0.00</strong></span>
                                    <span>含税总额: <strong id="modal-sum-total" class="picker-summary-highlight">¥ 0.00</strong></span>
                                </div>
                            </div>
                        </div>
                    `,
                },
            ],
            primary_action_label: __("🚀 立即生成并正式提交采购发票"),
            primary_action: async () => {
                const vals = d.get_values();
                if (!vals) return;

                const valid_items = rows_data.filter((r) => (r.item_code || "").trim().length > 0);
                if (!valid_items.length) {
                    frappe.msgprint(__("请至少保留一行有效的物料代码。"));
                    return;
                }

                try {
                    frappe.dom.freeze(__("正在生成采购发票..."));
                    const res = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_invoices_from_pr_items",
                        args: {
                            company: target_comp,
                            selected_items: valid_items,
                            bill_no: vals.bill_no,
                            bill_date: vals.bill_date,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (res && res.message && res.message.success) {
                        d.hide();
                        self.show_generation_success_dialog("采购发票", res.message.invoices, "purchase-invoice");
                        self.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成采购发票失败"));
                }
            },
        });

        d.$wrapper.addClass("picker-create-mr-modal");
        d.show();
        render_rows(d);

        const $wrap = d.get_field("items_html").$wrapper;

        $wrap.on("click", "#picker-modal-add-row-btn", () => {
            rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("click", ".picker-modal-del-btn", function () {
            const idx = parseInt($(this).attr("data-idx"));
            rows_data.splice(idx, 1);
            if (!rows_data.length) rows_data.push({ item_code: "", item_name: "", spec: "", qty: 1.0, rate: 0.0, amount: 0.0, tax_rate: 13.0, tax_amount: 0.0, total_amount: 0.0, description: "" });
            render_rows(d);
        });

        $wrap.on("input change", ".modal-input-qty", function () {
            recalculate_and_sync_row($(this).closest("tr"), "qty", $wrap);
        });
        $wrap.on("input change", ".modal-input-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "rate", $wrap);
        });
        $wrap.on("input change", ".modal-input-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "amount", $wrap);
        });
        $wrap.on("input change", ".modal-input-tax-rate", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_rate", $wrap);
        });
        $wrap.on("input change", ".modal-input-tax-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "tax_amount", $wrap);
        });
        $wrap.on("input change", ".modal-input-total-amount", function () {
            recalculate_and_sync_row($(this).closest("tr"), "total_amount", $wrap);
        });
    }

    open_create_rr_from_pi_dialog(selected_items, target_comp) {
        const self = this;
        const applicant_val = $("#picker-opt-applicant").val() || "";
        const inv_names = Array.from(new Set(selected_items.map((i) => i.pi_name).filter(Boolean)));

        let rows_html = selected_items.map((it, idx) => `
            <tr>
                <td class="picker-modal-cell-center">${idx + 1}</td>
                <td><strong>${frappe.utils.escape_html(it.pi_name)}</strong></td>
                <td>${frappe.utils.escape_html(it.supplier || "-")}</td>
                <td>${it.bill_date || it.posting_date || "-"}</td>
                <td class="picker-money-cell">${this.fmt_money(it.grand_total)}</td>
                <td class="picker-money-cell">${this.fmt_money(it.net_available_amount || it.outstanding_amount)}</td>
                <td class="picker-money-cell cell-row-amt"><strong>${this.fmt_money(it.this_amount || it.net_available_amount || it.outstanding_amount)}</strong></td>
            </tr>
        `).join("");

        const total_claim = selected_items.reduce((s, it) => s + flt(it.this_amount || it.net_available_amount || it.outstanding_amount), 0);

        const d = new frappe.ui.Dialog({
            title: __("💰 新建报销付款申请 · 选单创建与明细核算"),
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "company",
                    label: __("所属公司"),
                    options: this.companies.join("\n"),
                    default: target_comp,
                    read_only: 1,
                },
                {
                    fieldtype: "Link",
                    options: "Employee",
                    fieldname: "applicant",
                    label: __("报销申请人"),
                    default: applicant_val,
                },
                {
                    fieldtype: "Data",
                    fieldname: "purpose",
                    label: __("报销事由"),
                    default: `采购发票报销结算 (${inv_names.length}张发票)`,
                    reqd: 1,
                },
                {
                    fieldtype: "Date",
                    fieldname: "posting_date",
                    label: __("申请日期"),
                    default: frappe.datetime.get_today(),
                    reqd: 1,
                },
                {
                    fieldtype: "Section Break",
                    label: __("关联采购发票明细清单"),
                },
                {
                    fieldtype: "HTML",
                    fieldname: "invoices_html",
                    options: `
                        <div>
                            <table class="picker-modal-item-table">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>发票单号</th>
                                        <th>供应商</th>
                                        <th>开票/过账日期</th>
                                        <th>发票总额</th>
                                        <th>未付金额</th>
                                        <th>本次报销金额</th>
                                    </tr>
                                </thead>
                                <tbody>${rows_html}</tbody>
                            </table>

                            <div class="picker-modal-summary-bar">
                                <span>合计汇总:</span>
                                <div class="picker-modal-summary-items">
                                    <span>发票总数: <strong class="picker-summary-highlight">${inv_names.length} 张</strong></span>
                                    <span>报销总额: <strong class="picker-summary-highlight">${this.fmt_money(total_claim)}</strong></span>
                                </div>
                            </div>
                        </div>
                    `,
                },
            ],
            primary_action_label: __("🚀 立即生成并正式提交报销申请"),
            primary_action: async () => {
                const vals = d.get_values();
                if (!vals) return;

                try {
                    frappe.dom.freeze(__("正在生成报销申请..."));
                    const res = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_reimbursement_from_invoices",
                        args: {
                            company: target_comp,
                            selected_invoices: inv_names,
                            applicant: vals.applicant,
                            purpose: vals.purpose,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (res && res.message && res.message.success) {
                        d.hide();
                        self.show_generation_success_dialog("报销申请单", [{ name: res.message.reimbursement_name, company: target_comp, grand_total: res.message.total_amount, item_count: inv_names.length }], "reimbursement-request");
                        self.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成报销申请单失败"));
                }
            },
        });

        d.$wrapper.addClass("picker-create-mr-modal");
        d.show();
    }

    async handle_document_deletion(doctype, name, parent_dialog) {
        frappe.dom.freeze(__("正在分析单据依赖与权限..."));
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.preview_document_cascade_deletion",
                args: { doctype: doctype, name: name },
            });
            frappe.dom.unfreeze();
            if (!r || !r.message) return;
            const preview = r.message;

            if (!preview.can_delete) {
                frappe.msgprint({
                    title: __("🚨 权限不足，无法删除"),
                    indicator: "red",
                    message: __("您缺少以下关联单据的删除或撤单权限：<br><br>") + preview.missing_permissions.map(p => `• <strong>${frappe.utils.escape_html(p)}</strong>`).join("<br>")
                });
                return;
            }

            if (preview.has_downstream) {
                this.show_cascade_delete_dialog(preview, parent_dialog);
            } else {
                frappe.confirm(__("确定要删除单据 <strong>{0}</strong> ({1}) 吗？<br><br><span class='picker-danger-confirm-hint'>⚠️ 警告：删除后数据将无法恢复！</span>", [name, preview.target_doc.doctype_label]), async () => {
                    await this.execute_document_deletion(doctype, name, false, parent_dialog);
                });
            }
        } catch (e) {
            frappe.dom.unfreeze();
            frappe.msgprint(e.message || __("删除预检失败"));
        }
    }

    show_cascade_delete_dialog(preview, parent_dialog) {
        const self = this;
        let tree_items_html = "";
        preview.cascade_list.forEach((item, idx) => {
            const is_root = item.doctype === preview.target_doc.doctype && item.name === preview.target_doc.name;
            tree_items_html += `
                <li class="picker-cascade-tree-item ${is_root ? 'root-item' : ''}">
                    <div>
                        <span>${idx + 1}. </span>
                        <strong>${frappe.utils.escape_html(item.doctype_label)}</strong>: 
                        <span class="picker-cascade-item-code">${frappe.utils.escape_html(item.name)}</span>
                        <span class="picker-cascade-item-comp">(${frappe.utils.escape_html(item.company || '')})</span>
                    </div>
                    <div class="picker-cascade-tree-item-actions">
                        <span class="picker-cascade-item-status">${item.status_text}</span>
                        <span class="picker-cascade-perm-badge-ok">✓ 权限齐备</span>
                    </div>
                </li>
            `;
        });

        const cascade_dialog = new frappe.ui.Dialog({
            title: __("⚠️ 关联单据级联连带删除确认"),
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "cascade_html",
                    options: `
                        <div class="picker-cascade-box">
                            <div class="picker-cascade-warning-alert">
                                <strong>🚨 警告：检测到该单据已生成下游关联业务单据！</strong><br>
                                若继续删除，系统将按照业务依赖严格逆序（最下游 ➔ 最上游）依次执行<strong>撤销提交、还原库存/已订数量、彻底删除单据</strong>。
                            </div>
                            <div class="picker-cascade-target-heading">
                                📋 将连带逆序删除以下全部 ${preview.cascade_count} 张单据：
                            </div>
                            <ul class="picker-cascade-tree-list">
                                ${tree_items_html}
                            </ul>
                            <div class="picker-cascade-security-hint">
                                🛡️ 系统已完成全链路权限校验：当前用户对上述全部单据均拥有删除与撤单权限。
                            </div>
                        </div>
                    `,
                }
            ],
            primary_action_label: __("🚨 确认连带删除全部 {0} 张单据", [preview.cascade_count]),
            primary_action: async () => {
                cascade_dialog.hide();
                await self.execute_document_deletion(preview.target_doc.doctype, preview.target_doc.name, true, parent_dialog);
            }
        });

        cascade_dialog.show();
    }

    async execute_document_deletion(doctype, name, cascade, parent_dialog) {
        frappe.dom.freeze(__("正在执行安全删除..."));
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.delete_procurement_document",
                args: {
                    doctype: doctype,
                    name: name,
                    cascade: cascade ? 1 : 0
                }
            });
            frappe.dom.unfreeze();
            if (r && r.message && r.message.success) {
                frappe.show_alert({
                    message: r.message.message || __("删除成功"),
                    indicator: "green"
                }, 5);
                if (parent_dialog) {
                    parent_dialog.hide();
                }
                this.selected_map.clear();
                this.locked_company = null;
                this.update_company_lock_ui();
                await this.refresh_all();
            }
        } catch (e) {
            frappe.dom.unfreeze();
            frappe.msgprint(e.message || __("删除失败"));
        }
    }

    async batch_delete_selected() {
        const selected_items = Array.from(this.selected_map.values());
        if (!selected_items.length) {
            frappe.msgprint(__("请先勾选需要删除的单据/明细。"));
            return;
        }

        const stage = this.active_stage;
        let doctype = "Material Request";
        let docnames = new Set();

        if (stage === "item_to_mr" || stage === "mr_to_po") {
            doctype = "Material Request";
            selected_items.forEach(i => { if (i.mr_name) docnames.add(i.mr_name); });
        } else if (stage === "po_to_pr") {
            doctype = "Purchase Order";
            selected_items.forEach(i => { if (i.po_name) docnames.add(i.po_name); });
        } else if (stage === "pr_to_pi") {
            doctype = "Purchase Receipt";
            selected_items.forEach(i => { if (i.pr_name) docnames.add(i.pr_name); });
        } else if (stage === "pi_to_rr") {
            doctype = "Purchase Invoice";
            selected_items.forEach(i => { if (i.pi_name) docnames.add(i.pi_name); });
        }

        const docname_list = Array.from(docnames);
        if (!docname_list.length) {
            frappe.msgprint(__("未找到可删除的单据编号。"));
            return;
        }

        if (docname_list.length === 1) {
            this.handle_document_deletion(doctype, docname_list[0]);
        } else {
            frappe.confirm(__("确定要删除勾选的 <strong>{0}</strong> 张单据吗？<br><br>{1}", [docname_list.length, docname_list.map(n => `• ${frappe.utils.escape_html(n)}`).join("<br>")]), async () => {
                frappe.dom.freeze(__("正在批量删除单据..."));
                let success_count = 0;
                let fail_msgs = [];
                for (const nm of docname_list) {
                    try {
                        await frappe.call({
                            method: "ashan_cn_procurement.services.procurement_picker_service.delete_procurement_document",
                            args: { doctype: doctype, name: nm, cascade: 1 }
                        });
                        success_count++;
                    } catch (e) {
                        fail_msgs.push(`【${nm}】: ${e.message || '删除失败'}`);
                    }
                }
                frappe.dom.unfreeze();
                if (fail_msgs.length) {
                    frappe.msgprint({
                        title: __("批量删除部分完成"),
                        indicator: "orange",
                        message: __("成功删除 {0} 张单据，以下单据删除失败：<br><br>{1}", [success_count, fail_msgs.join("<br>")])
                    });
                } else {
                    frappe.show_alert({ message: __("成功批量删除 {0} 张单据", [success_count]), indicator: "green" });
                }
                this.selected_map.clear();
                this.locked_company = null;
                this.update_company_lock_ui();
                await this.refresh_all();
            });
        }
    }
}

