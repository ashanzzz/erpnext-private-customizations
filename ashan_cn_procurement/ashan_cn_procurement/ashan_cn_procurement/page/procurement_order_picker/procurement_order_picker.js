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
        this.active_company = "All"; // "All" or specific company name
        this.companies = [];
        this.locked_company = null; // Dynamically set when first row is checked in "All" mode
        this.kpis = {};
        this.table_data = [];
        this.selected_map = new Map(); // key -> row object
        this.filters = {
            item_to_mr: { item_code: "", item_group: "", supplier: "" },
            mr_to_po: { supplier: "", department: "", item_code: "", from_date: "", to_date: "" },
            po_to_pr: { supplier: "", warehouse: "", po_name: "", item_code: "" },
            pr_to_pi: { supplier: "", pr_name: "", item_code: "" },
            pi_to_rr: { supplier: "", bill_no: "", owner: "" },
        };

        this.stages_config = {
            item_to_mr: {
                id: "item_to_mr",
                name: "采购申请",
                banner_title: "当前：采购申请 (从物料主数据提报采购需求)",
                banner_desc: "勾选物料明细，行内录入本次申请数量，一键下推生成采购申请单草稿 (Material Request)。",
                sub_label: "可提报物料主数据",
                icon: "📋",
                btn_label: "⚡ 生成采购申请草稿",
            },
            mr_to_po: {
                id: "mr_to_po",
                name: "采购订货",
                banner_title: "当前：采购订货 (从采购需求选单下达订单)",
                banner_desc: "勾选待订需求明细，系统自动按建议供应商智能拆单合并生成采购订单草稿 (Purchase Order)。",
                sub_label: "待订货需求明细",
                icon: "🛒",
                btn_label: "⚡ 生成采购订单草稿",
            },
            po_to_pr: {
                id: "po_to_pr",
                name: "采购入库",
                banner_title: "当前：采购入库 (从采购订单选单收货入库)",
                banner_desc: "勾选待收货明细，录入本次到货数量与目的入库仓库，生成采购入库单草稿 (Purchase Receipt)。",
                sub_label: "待收货订单明细",
                icon: "📦",
                btn_label: "⚡ 生成采购入库单草稿",
            },
            pr_to_pi: {
                id: "pr_to_pi",
                name: "采购开票",
                banner_title: "当前：采购开票 (从采购入库选单开票结算)",
                banner_desc: "勾选已入库物料明细，录入纸质/金税发票号码与日期，生成采购发票草稿 (Purchase Invoice)。",
                sub_label: "待开票入库明细",
                icon: "🧾",
                btn_label: "⚡ 生成采购发票草稿",
            },
            pi_to_rr: {
                id: "pi_to_rr",
                name: "报销付款",
                banner_title: "当前：报销付款 (从采购发票选单报销/付款)",
                banner_desc: "勾选待报销发票，自动创建报销申请单并写入行级排他预占 (Reimbursement Request)。",
                sub_label: "待报销付款发票",
                icon: "💰",
                btn_label: "⚡ 生成报销申请单草稿",
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

                <!-- Company Exclusive Lock Notice Banner -->
                <div class="picker-company-lock-banner" id="picker-company-lock-banner">
                    <div class="picker-company-lock-text">
                        <span>💡</span>
                        <span id="picker-lock-banner-text">已锁定公司范围，其他公司明细已自动隐藏</span>
                    </div>
                    <button class="picker-unlock-btn" id="picker-unlock-btn">清空已选并恢复全量</button>
                </div>

                <!-- 5-Step KPI Cards Grid (Master Navigation) -->
                <div class="picker-kpi-grid" id="picker-kpi-grid"></div>

                <!-- Section Context Banner (Replaces redundant Tab Bar) -->
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
                    self.update_company_lock_ui();
                }

                // If locked and row is from another company, ignore
                if (self.locked_company && row.company !== self.locked_company) {
                    $(this).prop("checked", false);
                    return;
                }

                const $tr = $(this).closest("tr");
                const input_qty = flt($tr.find(".picker-input-qty").val()) || row.pending_qty || row.this_qty || 1;
                row.this_qty = input_qty;
                self.selected_map.set(key, row);
                $tr.addClass("row-selected");
            } else {
                self.selected_map.delete(key);
                $(this).closest("tr").removeClass("row-selected");

                // If no rows selected, release lock
                if (self.selected_map.size === 0) {
                    self.locked_company = null;
                    self.update_company_lock_ui();
                }
            }

            self.update_table_visibility_by_lock();
            self.update_action_summary();
        });

        // Row Qty Input Change
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

        // Select All / Clear Selection
        $(this.page.body).on("click", "#picker-select-all-btn", () => this.select_all_visible());
        $(this.page.body).on("click", "#picker-clear-sel-btn", () => this.clear_selection());
        $(this.page.body).on("click", "#picker-fill-max-btn", () => this.fill_max_quantities());

        // Primary Action Submit
        $(this.page.body).on("click", "#picker-submit-btn", () => this.execute_primary_action());
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
                待办统计: ${data.count || 0} 笔
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
            filters_html = `
                <div class="picker-filter-group">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-filter-input" data-filter="item_code" placeholder="搜索物料..." value="${this.filters[stage].item_code || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>物料分组:</label>
                    <input type="text" class="picker-filter-input" data-filter="item_group" placeholder="物料分类..." value="${this.filters[stage].item_group || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>供应商:</label>
                    <input type="text" class="picker-filter-input" data-filter="supplier" placeholder="供应商..." value="${this.filters[stage].supplier || ''}">
                </div>
            `;
        } else if (stage === "mr_to_po") {
            filters_html = `
                <div class="picker-filter-group">
                    <label>物料编码/名称:</label>
                    <input type="text" class="picker-filter-input" data-filter="item_code" placeholder="搜索物料..." value="${this.filters[stage].item_code || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>建议供应商:</label>
                    <input type="text" class="picker-filter-input" data-filter="supplier" placeholder="供应商名称..." value="${this.filters[stage].supplier || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>申请部门:</label>
                    <input type="text" class="picker-filter-input" data-filter="department" placeholder="部门..." value="${this.filters[stage].department || ''}">
                </div>
                <div class="picker-filter-group">
                    <label>申请日期:</label>
                    <input type="date" class="picker-filter-input" data-filter="from_date" value="${this.filters[stage].from_date || ''}">
                    <span>至</span>
                    <input type="date" class="picker-filter-input" data-filter="to_date" value="${this.filters[stage].to_date || ''}">
                </div>
            `;
        } else if (stage === "po_to_pr") {
            filters_html = `
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
                <div class="picker-filter-group">
                    <label>收货仓库:</label>
                    <input type="text" class="picker-filter-input" data-filter="warehouse" placeholder="仓库名称..." value="${this.filters[stage].warehouse || ''}">
                </div>
            `;
        } else if (stage === "pr_to_pi") {
            filters_html = `
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
            filters_html = `
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

        // Bind filter change
        const self = this;
        $bar.find(".picker-filter-input").on("change input", function () {
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
        let method = "";
        if (stage === "item_to_mr") {
            method = "ashan_cn_procurement.services.procurement_picker_service.get_item_master_picker_rows";
        } else if (stage === "mr_to_po") {
            method = "ashan_cn_procurement.services.procurement_picker_service.get_pending_material_request_items";
        } else if (stage === "po_to_pr") {
            method = "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_order_items";
        } else if (stage === "pr_to_pi") {
            method = "ashan_cn_procurement.services.procurement_picker_service.get_pending_purchase_receipt_items";
        } else if (stage === "pi_to_rr") {
            method = "ashan_cn_procurement.services.procurement_picker_service.get_pending_reimbursement_invoices";
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
        if (this.active_stage === "item_to_mr") return `${row.item_code}::${row.company}`;
        if (this.active_stage === "mr_to_po") return row.mri_name;
        if (this.active_stage === "po_to_pr") return row.poi_name;
        if (this.active_stage === "pr_to_pi") return row.pri_name;
        if (this.active_stage === "pi_to_rr") return row.pi_name;
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
        let ths = `
            <th class="picker-col-sticky-1"><span class="picker-th-badge">序号</span><span class="picker-th-title">#</span></th>
            <th class="picker-col-sticky-2"><span class="picker-th-badge">选择</span><span class="picker-th-title">勾选</span></th>
        `;

        if (this.active_company === "All") {
            ths += `<th class="picker-col-sticky-3"><span class="picker-th-badge">主体</span><span class="picker-th-title">所属公司</span></th>`;
        }

        if (stage === "item_to_mr") {
            ths += `
                <th><span class="picker-th-badge">物料编码</span><span class="picker-th-title">物料代码</span></th>
                <th><span class="picker-th-badge">物料名称/规格</span><span class="picker-th-title">物料描述</span></th>
                <th><span class="picker-th-badge">分类</span><span class="picker-th-title">物料分组</span></th>
                <th><span class="picker-th-badge">单位</span><span class="picker-th-title">单位</span></th>
                <th><span class="picker-th-badge">结存</span><span class="picker-th-title">当前库存</span></th>
                <th><span class="picker-th-badge">申请数</span><span class="picker-th-title">本次申请</span></th>
                <th><span class="picker-th-badge">建议供应商</span><span class="picker-th-title">默认供应商</span></th>
                <th><span class="picker-th-badge">参考单价</span><span class="picker-th-title">标准进价</span></th>
            `;
        } else if (stage === "mr_to_po") {
            ths += `
                <th><span class="picker-th-badge">申请单号</span><span class="picker-th-title">采购需求单</span></th>
                <th><span class="picker-th-badge">需求交期</span><span class="picker-th-title">期望到货</span></th>
                <th><span class="picker-th-badge">部门/申请人</span><span class="picker-th-title">需求部门</span></th>
                <th><span class="picker-th-badge">物料编码</span><span class="picker-th-title">物料代码</span></th>
                <th><span class="picker-th-badge">物料名称/规格</span><span class="picker-th-title">名称规格</span></th>
                <th><span class="picker-th-badge">单位</span><span class="picker-th-title">单位</span></th>
                <th><span class="picker-th-badge">申请数</span><span class="picker-th-title">总数量</span></th>
                <th><span class="picker-th-badge">已订数</span><span class="picker-th-title">已订</span></th>
                <th><span class="picker-th-badge">待订数</span><span class="picker-th-title">未订数量</span></th>
                <th><span class="picker-th-badge">本次订购</span><span class="picker-th-title">本次下单数</span></th>
                <th><span class="picker-th-badge">参考单价</span><span class="picker-th-title">单价</span></th>
                <th><span class="picker-th-badge">预估金额</span><span class="picker-th-title">金额</span></th>
                <th><span class="picker-th-badge">建议供应商</span><span class="picker-th-title">供应商</span></th>
            `;
        } else if (stage === "po_to_pr") {
            ths += `
                <th><span class="picker-th-badge">供应商</span><span class="picker-th-title">供应商</span></th>
                <th><span class="picker-th-badge">采购订单</span><span class="picker-th-title">订单单号</span></th>
                <th><span class="picker-th-badge">下单日期</span><span class="picker-th-title">订单日期</span></th>
                <th><span class="picker-th-badge">交期状态</span><span class="picker-th-title">承诺交期</span></th>
                <th><span class="picker-th-badge">物料编码/名称</span><span class="picker-th-title">物料描述</span></th>
                <th><span class="picker-th-badge">目的仓库</span><span class="picker-th-title">默认仓库</span></th>
                <th><span class="picker-th-badge">订单数量</span><span class="picker-th-title">订购总数</span></th>
                <th><span class="picker-th-badge">已收数量</span><span class="picker-th-title">已收</span></th>
                <th><span class="picker-th-badge">待收数量</span><span class="picker-th-title">未收数量</span></th>
                <th><span class="picker-th-badge">本次实收</span><span class="picker-th-title">本次到货数</span></th>
                <th><span class="picker-th-badge">单价</span><span class="picker-th-title">采购单价</span></th>
                <th><span class="picker-th-badge">待收金额</span><span class="picker-th-title">未收金额</span></th>
            `;
        } else if (stage === "pr_to_pi") {
            ths += `
                <th><span class="picker-th-badge">供应商</span><span class="picker-th-title">供应商</span></th>
                <th><span class="picker-th-badge">采购入库单</span><span class="picker-th-title">入库单号</span></th>
                <th><span class="picker-th-badge">入库日期</span><span class="picker-th-title">过账日期</span></th>
                <th><span class="picker-th-badge">物料编码/名称</span><span class="picker-th-title">物料描述</span></th>
                <th><span class="picker-th-badge">单位</span><span class="picker-th-title">单位</span></th>
                <th><span class="picker-th-badge">入库数</span><span class="picker-th-title">实收总数</span></th>
                <th><span class="picker-th-badge">已开票数</span><span class="picker-th-title">已结数</span></th>
                <th><span class="picker-th-badge">待开票数</span><span class="picker-th-title">未结数量</span></th>
                <th><span class="picker-th-badge">本次开票</span><span class="picker-th-title">本次结算数</span></th>
                <th><span class="picker-th-badge">单价</span><span class="picker-th-title">入库单价</span></th>
                <th><span class="picker-th-badge">待开票金额</span><span class="picker-th-title">待结金额</span></th>
                <th><span class="picker-th-badge">关联订单</span><span class="picker-th-title">源采购订单</span></th>
            `;
        } else if (stage === "pi_to_rr") {
            ths += `
                <th><span class="picker-th-badge">发票单号</span><span class="picker-th-title">ERP发票号</span></th>
                <th><span class="picker-th-badge">供应商/销售方</span><span class="picker-th-title">供应商</span></th>
                <th><span class="picker-th-badge">纸质/金税发票号</span><span class="picker-th-title">发票号码</span></th>
                <th><span class="picker-th-badge">发票类型</span><span class="picker-th-title">票据类别</span></th>
                <th><span class="picker-th-badge">开票日期</span><span class="picker-th-title">开票日期</span></th>
                <th><span class="picker-th-badge">经办人</span><span class="picker-th-title">录单人</span></th>
                <th><span class="picker-th-badge">发票总额</span><span class="picker-th-title">含税总额</span></th>
                <th><span class="picker-th-badge">已付/已报额</span><span class="picker-th-title">已核销</span></th>
                <th><span class="picker-th-badge">待报销余额</span><span class="picker-th-title">可报销应付</span></th>
            `;
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
                            <div>当前没有待处理的明细记录</div>
                        </div>
                    </td>
                </tr>
            `);
            return;
        }

        const stage = this.active_stage;
        const is_all_company = this.active_company === "All";

        this.table_data.forEach((r, idx) => {
            const key = this.get_row_key(r);
            const is_selected = this.selected_map.has(key);
            const is_hidden_by_lock = this.locked_company && r.company !== this.locked_company;

            let tr_html = `
                <tr class="${is_selected ? 'row-selected' : ''} ${is_hidden_by_lock ? 'picker-row-company-hidden' : ''}" data-key="${key}" data-company="${frappe.utils.escape_html(r.company || '')}">
                    <td class="picker-col-sticky-1">${idx + 1}</td>
                    <td class="picker-col-sticky-2">
                        <input type="checkbox" class="picker-row-checkbox" data-key="${key}" ${is_selected ? 'checked' : ''}>
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

            if (stage === "item_to_mr") {
                tr_html += `
                    <td><strong>${frappe.utils.escape_html(r.item_code)}</strong></td>
                    <td>${frappe.utils.escape_html(r.item_name || r.item_code)}</td>
                    <td>${frappe.utils.escape_html(r.item_group || "")}</td>
                    <td>${frappe.utils.escape_html(r.uom || "")}</td>
                    <td class="picker-qty-cell">${r.current_stock || 0}</td>
                    <td>
                        <input type="number" class="picker-input-qty" step="1" min="1" value="${r.this_qty || 1}">
                    </td>
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                    <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                `;
            } else if (stage === "mr_to_po") {
                const urgent_tag = r.is_overdue ? `<span class="picker-badge-urgent">逾期</span>` : (r.is_urgent ? `<span class="picker-badge-urgent">紧急</span>` : "");
                tr_html += `
                    <td><a href="/desk/material-request/${r.mr_name}">${frappe.utils.escape_html(r.mr_name)}</a></td>
                    <td>${r.schedule_date || "-"} ${urgent_tag}</td>
                    <td>${frappe.utils.escape_html(r.department || r.requested_by || "-")}</td>
                    <td><strong>${frappe.utils.escape_html(r.item_code)}</strong></td>
                    <td>${frappe.utils.escape_html(r.item_name || "")}</td>
                    <td>${frappe.utils.escape_html(r.uom || "")}</td>
                    <td class="picker-qty-cell">${r.qty}</td>
                    <td class="picker-qty-cell">${r.ordered_qty}</td>
                    <td class="picker-qty-cell"><strong>${r.pending_qty}</strong></td>
                    <td>
                        <input type="number" class="picker-input-qty" step="0.01" min="0.01" max="${r.pending_qty}" value="${r.this_qty}">
                    </td>
                    <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                    <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.estimated_amount)}</td>
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                `;
            } else if (stage === "po_to_pr") {
                tr_html += `
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                    <td><a href="/desk/purchase-order/${r.po_name}">${frappe.utils.escape_html(r.po_name)}</a></td>
                    <td>${r.po_date || "-"}</td>
                    <td>${r.schedule_date || "-"}</td>
                    <td><span class="ashan-tag-badge">${frappe.utils.escape_html(r.item_code)}</span> ${frappe.utils.escape_html(r.item_name || "")}</td>
                    <td>${frappe.utils.escape_html(r.warehouse || "-")}</td>
                    <td class="picker-qty-cell">${r.qty}</td>
                    <td class="picker-qty-cell">${r.received_qty}</td>
                    <td class="picker-qty-cell"><strong>${r.pending_qty}</strong></td>
                    <td>
                        <input type="number" class="picker-input-qty" step="0.01" min="0.01" max="${r.pending_qty}" value="${r.this_qty}">
                    </td>
                    <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                    <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.pending_amount)}</td>
                `;
            } else if (stage === "pr_to_pi") {
                tr_html += `
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                    <td><a href="/desk/purchase-receipt/${r.pr_name}">${frappe.utils.escape_html(r.pr_name)}</a></td>
                    <td>${r.pr_date || "-"}</td>
                    <td><span class="ashan-tag-badge">${frappe.utils.escape_html(r.item_code)}</span> ${frappe.utils.escape_html(r.item_name || "")}</td>
                    <td>${frappe.utils.escape_html(r.uom || "")}</td>
                    <td class="picker-qty-cell">${r.qty}</td>
                    <td class="picker-qty-cell">${r.billed_qty}</td>
                    <td class="picker-qty-cell"><strong>${r.pending_qty}</strong></td>
                    <td>
                        <input type="number" class="picker-input-qty" step="0.01" min="0.01" max="${r.pending_qty}" value="${r.this_qty}">
                    </td>
                    <td class="picker-money-cell">${this.fmt_money(r.rate)}</td>
                    <td class="picker-money-cell cell-row-amt">${this.fmt_money(r.pending_amount)}</td>
                    <td>${frappe.utils.escape_html(r.purchase_order || "-")}</td>
                `;
            } else if (stage === "pi_to_rr") {
                tr_html += `
                    <td><a href="/desk/purchase-invoice/${r.pi_name}">${frappe.utils.escape_html(r.pi_name)}</a></td>
                    <td>${frappe.utils.escape_html(r.supplier || "-")}</td>
                    <td><span class="picker-badge-invoice-type">${frappe.utils.escape_html(r.bill_no || "未填")}</span></td>
                    <td><span class="ashan-status-badge ashan-status-blue">${frappe.utils.escape_html(r.invoice_type || "普通发票")}</span></td>
                    <td>${r.bill_date || r.posting_date || "-"}</td>
                    <td>${frappe.utils.escape_html(r.owner || "-")}</td>
                    <td class="picker-money-cell">${this.fmt_money(r.grand_total)}</td>
                    <td class="picker-money-cell">${this.fmt_money(r.grand_total - r.outstanding_amount)}</td>
                    <td class="picker-money-cell cell-row-amt"><strong>${this.fmt_money(r.net_available_amount)}</strong></td>
                `;
            }

            tr_html += `</tr>`;
            $tbody.append(tr_html);
        });
    }

    render_table_footer() {
        const stage = this.active_stage;
        const is_all_company = this.active_company === "All";
        let total_qty = 0;
        let total_amt = 0;

        this.table_data.forEach((r) => {
            if (this.locked_company && r.company !== this.locked_company) return;
            total_qty += flt(r.pending_qty || r.qty || 0);
            total_amt += flt(r.estimated_amount || r.pending_amount || r.net_available_amount || 0);
        });

        let prefix_cols = is_all_company ? 3 : 2;
        let foot_html = `
            <tr>
                <td colspan="${prefix_cols}" class="picker-col-sticky-foot">
                    合计 (共 ${this.table_data.length} 条)
                </td>
        `;

        if (stage === "item_to_mr") {
            foot_html += `<td colspan="8"></td>`;
        } else if (stage === "mr_to_po") {
            foot_html += `
                <td colspan="6"></td>
                <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                <td colspan="2"></td>
                <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                <td></td>
            `;
        } else if (stage === "po_to_pr") {
            foot_html += `
                <td colspan="6"></td>
                <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                <td colspan="2"></td>
                <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
            `;
        } else if (stage === "pr_to_pi") {
            foot_html += `
                <td colspan="5"></td>
                <td class="picker-qty-cell">${total_qty.toFixed(2)}</td>
                <td colspan="2"></td>
                <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
                <td></td>
            `;
        } else if (stage === "pi_to_rr") {
            foot_html += `
                <td colspan="5"></td>
                <td colspan="2"></td>
                <td class="picker-money-cell">${this.fmt_money(total_amt)}</td>
            `;
        }

        foot_html += `</tr>`;
        $("#picker-table-tfoot").html(foot_html);
    }

    update_company_lock_ui() {
        const $banner = $("#picker-company-lock-banner");
        const $text = $("#picker-lock-banner-text");

        if (this.locked_company && this.active_company === "All") {
            $banner.addClass("is-active");
            $text.html(`当前已按【<strong>${frappe.utils.escape_html(this.locked_company)}</strong>】锁定选单生单范围（已自动隐藏其他公司明细，取消勾选后恢复全量视图）`);
        } else {
            $banner.removeClass("is-active");
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
        const cfg = this.stages_config[stage];
        const sel_count = this.selected_map.size;

        let total_sel_amt = 0;
        this.selected_map.forEach((item) => {
            const rate = flt(item.rate);
            const qty = flt(item.this_qty || item.pending_qty || 1);
            if (item.net_available_amount !== undefined) {
                total_sel_amt += flt(item.net_available_amount);
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

        let stage_inputs = "";
        if (stage === "item_to_mr") {
            stage_inputs = `
                <div class="picker-filter-group">
                    <input type="text" class="picker-filter-input" id="picker-opt-dept" placeholder="需求部门/用途(可选)">
                </div>
            `;
        } else if (stage === "mr_to_po") {
            stage_inputs = `
                <div class="picker-filter-group">
                    <input type="text" class="picker-filter-input" id="picker-opt-supplier" placeholder="统一指定供应商(可选)">
                </div>
            `;
        } else if (stage === "po_to_pr") {
            stage_inputs = `
                <div class="picker-filter-group">
                    <input type="text" class="picker-filter-input" id="picker-opt-warehouse" placeholder="统一指定入库仓库(可选)">
                </div>
            `;
        } else if (stage === "pr_to_pi") {
            stage_inputs = `
                <div class="picker-filter-group">
                    <input type="text" class="picker-filter-input" id="picker-opt-bill-no" placeholder="发票号码(纸质/金税)">
                </div>
            `;
        } else if (stage === "pi_to_rr") {
            stage_inputs = `
                <div class="picker-filter-group">
                    <input type="text" class="picker-filter-input" id="picker-opt-applicant" placeholder="报销申请人(邮箱/员工)">
                </div>
            `;
        }

        const html = `
            <div class="picker-summary-text">
                <span>已选 <strong class="picker-summary-highlight">${sel_count}</strong> 行明细</span>
                <span>本次总计: <strong class="picker-summary-highlight">${this.fmt_money(total_sel_amt)}</strong></span>
            </div>
            <div class="picker-btn-group">
                <button class="picker-btn-secondary" id="picker-select-all-btn">全选本页</button>
                <button class="picker-btn-secondary" id="picker-clear-sel-btn">清空选择</button>
                ${stage !== 'item_to_mr' ? '<button class="picker-btn-secondary" id="picker-fill-max-btn">填充最大待办数</button>' : ''}
                ${stage_inputs}
                <button class="picker-btn-primary" id="picker-submit-btn" ${sel_count === 0 ? 'disabled' : ''}>
                    ${cfg.btn_label}${target_comp_suffix}
                </button>
            </div>
        `;
        $bar.html(html);
    }

    select_all_visible() {
        const self = this;

        // If not locked and in All mode, check the first visible row's company
        if (this.active_company === "All" && !this.locked_company) {
            const first_visible = this.table_data.find((r) => !self.locked_company || r.company === self.locked_company);
            if (first_visible) {
                this.locked_company = first_visible.company;
                this.update_company_lock_ui();
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

    async execute_primary_action() {
        const stage = this.active_stage;
        const selected_items = Array.from(this.selected_map.values());
        if (!selected_items.length) {
            frappe.msgprint(__("请至少选择一行明细。"));
            return;
        }

        const target_comp = this.locked_company || (this.active_company !== "All" ? this.active_company : selected_items[0].company);

        if (stage === "item_to_mr") {
            const dept = $("#picker-opt-dept").val();
            frappe.confirm(__("确定将选中的 {0} 种物料生成采购申请草稿吗？", [selected_items.length]), async () => {
                try {
                    frappe.dom.freeze(__("正在生成采购申请..."));
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_material_requests_from_items",
                        args: {
                            company: target_comp,
                            selected_items: selected_items,
                            department: dept,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (r && r.message && r.message.success) {
                        this.show_generation_success_dialog("采购申请", r.message.requests, "material-request");
                        this.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成采购申请失败"));
                }
            });
        } else if (stage === "mr_to_po") {
            const sup_override = $("#picker-opt-supplier").val();
            frappe.confirm(__("确定将选中的 {0} 行需求生成采购订单草稿吗？", [selected_items.length]), async () => {
                try {
                    frappe.dom.freeze(__("正在生成采购订单..."));
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_orders_from_mr_items",
                        args: {
                            company: target_comp,
                            selected_items: selected_items,
                            supplier_override: sup_override,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (r && r.message && r.message.success) {
                        this.show_generation_success_dialog("采购订单", r.message.orders, "purchase-order");
                        this.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成采购订单失败"));
                }
            });
        } else if (stage === "po_to_pr") {
            const wh_override = $("#picker-opt-warehouse").val();
            frappe.confirm(__("确定将选中的 {0} 行订单明细生成采购入库单草稿吗？", [selected_items.length]), async () => {
                try {
                    frappe.dom.freeze(__("正在生成采购入库单..."));
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_receipts_from_po_items",
                        args: {
                            company: target_comp,
                            selected_items: selected_items,
                            warehouse_override: wh_override,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (r && r.message && r.message.success) {
                        this.show_generation_success_dialog("采购入库单", r.message.receipts, "purchase-receipt");
                        this.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成采购入库单失败"));
                }
            });
        } else if (stage === "pr_to_pi") {
            const bill_no = $("#picker-opt-bill-no").val();
            frappe.confirm(__("确定将选中的 {0} 行入库明细生成采购发票草稿吗？", [selected_items.length]), async () => {
                try {
                    frappe.dom.freeze(__("正在生成采购发票..."));
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_purchase_invoices_from_pr_items",
                        args: {
                            company: target_comp,
                            selected_items: selected_items,
                            bill_no: bill_no,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (r && r.message && r.message.success) {
                        this.show_generation_success_dialog("采购发票", r.message.invoices, "purchase-invoice");
                        this.refresh_all();
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成采购发票失败"));
                }
            });
        } else if (stage === "pi_to_rr") {
            const applicant = $("#picker-opt-applicant").val();
            const inv_names = selected_items.map((i) => i.pi_name);
            frappe.confirm(__("确定将选中的 {0} 张采购发票生成报销申请单草稿吗？", [inv_names.length]), async () => {
                try {
                    frappe.dom.freeze(__("正在生成报销申请..."));
                    const r = await frappe.call({
                        method: "ashan_cn_procurement.services.procurement_picker_service.make_reimbursement_from_invoices",
                        args: {
                            company: target_comp,
                            selected_invoices: inv_names,
                            applicant: applicant,
                            purpose: `采购发票选单报销 (${inv_names.length}张)`,
                        },
                    });
                    frappe.dom.unfreeze();
                    if (r && r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("成功生成报销申请单：{0}", [r.message.reimbursement_name]),
                            indicator: "green",
                        });
                        frappe.set_route("reimbursement-request", r.message.reimbursement_name);
                    }
                } catch (e) {
                    frappe.dom.unfreeze();
                    frappe.msgprint(e.message || __("生成报销申请单失败"));
                }
            });
        }
    }

    show_generation_success_dialog(doc_title, docs_created, route_prefix) {
        if (!docs_created || !docs_created.length) return;

        let items_html = docs_created
            .map(
                (d) => `
            <div class="picker-dialog-doc-item">
                <div class="picker-dialog-doc-main">
                    <strong><a href="/desk/${route_prefix}/${d.name}" target="_blank">${frappe.utils.escape_html(d.name)}</a></strong>
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
            title: __("🎉 成功生成 {0} 张{1}草稿", [docs_created.length, doc_title]),
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "result_html",
                    options: `
                        <div class="picker-dialog-desc">
                            已成功为您生成以下草稿单据，您可以点击单号进入查看或审批：
                        </div>
                        <div class="picker-dialog-list">
                            ${items_html}
                        </div>
                    `,
                },
            ],
            primary_action_label: __("查看第一张单据"),
            primary_action: () => {
                d.hide();
                frappe.set_route(route_prefix, docs_created[0].name);
            },
        });
        d.show();
    }
}
