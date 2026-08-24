// Copyright (c) 2026, Ashan CN Procurement and contributors
// For license information, please see license.txt

frappe.pages["reimbursement-picker"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("🧾 报销申请中心"),
        single_column: true,
    });

    wrapper.reim_picker = new ReimbursementPicker(page);
};

const REIM_API = {
    overview_kpis: "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_picker_overview_kpis",
    doc_summary: "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_picker_doc_summary_rows",
    item_rows: "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_picker_rows",
    companies: "ashan_cn_procurement.services.procurement_picker_service.get_user_procurement_companies",
    creation_defaults: "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_creation_defaults",
    candidates: "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursable_tax_invoices",
    preview: "ashan_cn_procurement.services.reimbursement_picker_service.preview_tax_invoice_reimbursement",
    create_v2: "ashan_cn_procurement.services.reimbursement_picker_service.create_tax_invoice_reimbursement",
    upload: "ashan_cn_procurement.ashan_cn_procurement.page.tax_invoice_center.tax_invoice_center.upload_tax_invoice_file",
};

class ReimbursementPicker {
    constructor(page) {
        this.page = page;
        this.active_company = "All";
        this.companies = [];
        this.view_mode = "doc"; // 默认单号视图
        this.match_status = "pending";
        this.selected_items = new Set();
        this.cached_rows = [];
        this.kpis = {};

        this.creation = {
            dialog: null,
            active_tab: "select", // select | upload
            company: null,
            employee: null,
            employee_name: null,
            posting_date: null,
            title: "",
            auto_receive_stock: 1,
            filters: {
                search: "",
                from_date: "",
                to_date: "",
                invoice_type: "",
                pi_mode: "",
            },
            candidate_rows: [],
            selected_invoices: new Map(),
            preview: null,
            resolutions: { suppliers: {}, items: {}, warehouses: {} },
            latest_request: 0,
            loading: false,
            preview_timer: null,
        };

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
                        <h2>🧾 报销申请中心</h2>
                        <div class="picker-subtitle">现金报销 · 多发票智能归集与闭环生单</div>
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
                            <span class="picker-kpi-title">待结款报销</span>
                            <span class="picker-kpi-icon">💰</span>
                        </div>
                        <div class="picker-kpi-body">
                            <div class="picker-kpi-number" id="reim-kpi-pending-rr">0</div>
                            <div class="picker-kpi-sub" id="reim-kpi-pending-sub">待结款报销单</div>
                        </div>
                    </div>
                    <div class="picker-kpi-card" data-step="pi">
                        <div class="picker-kpi-header">
                            <span class="picker-kpi-title">垫付采购发票</span>
                            <span class="picker-kpi-icon">🧾</span>
                        </div>
                        <div class="picker-kpi-body">
                            <div class="picker-kpi-number" id="reim-kpi-pi-count">0</div>
                            <div class="picker-kpi-sub">关联采购发票</div>
                        </div>
                    </div>
                    <div class="picker-kpi-card" data-step="pr">
                        <div class="picker-kpi-header">
                            <span class="picker-kpi-title">自动入库单</span>
                            <span class="picker-kpi-icon">📦</span>
                        </div>
                        <div class="picker-kpi-body">
                            <div class="picker-kpi-number" id="reim-kpi-pr-count">0</div>
                            <div class="picker-kpi-sub">库存品入库</div>
                        </div>
                    </div>
                    <div class="picker-kpi-card" data-step="outstanding_amt">
                        <div class="picker-kpi-header">
                            <span class="picker-kpi-title">待报销总额</span>
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
                        <div class="picker-section-icon">🧾</div>
                        <div class="picker-section-heading">
                            <div class="picker-section-title">
                                <span>报销申请 · 多发票智能归集与闭环生单中心</span>
                            </div>
                            <div class="picker-section-desc">支持批量选择税局发票或直接拖拽上传电子发票，全自动复用或生成采购单据链并汇入报销申请单 (RR)。</div>
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
                            <button type="button" class="picker-status-btn active" data-status="pending">🟡 仅待结款</button>
                            <button type="button" class="picker-status-btn" data-status="completed">🟢 仅已结清</button>
                            <button type="button" class="picker-status-btn" data-status="all">🌐 全部报销</button>
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

                <!-- Action Bar -->
                <div class="picker-action-bar">
                    <div class="picker-summary-text">
                        <div class="picker-view-switch-group">
                            <button type="button" class="picker-view-btn" data-mode="detail">📑 明细视图</button>
                            <button type="button" class="picker-view-btn active" data-mode="doc">📦 单号视图</button>
                        </div>
                        <span>已加载: <strong class="picker-summary-highlight" id="reim-loaded-count">0</strong> 笔</span>
                        <span>报销总额: <strong class="picker-summary-highlight" id="reim-sum-total-amt">¥ 0.00</strong></span>
                        <span>待结款: <strong class="picker-summary-highlight" id="reim-sum-outstanding-amt">¥ 0.00</strong></span>
                    </div>

                    <div class="picker-btn-group">
                        <button type="button" class="picker-btn-sub" id="reim-refresh-btn">🔄 刷新</button>
                        <button type="button" class="reim-btn-create-rr" id="reim-open-create-modal-btn">
                            <span>➕ 新建报销</span>
                        </button>
                    </div>
                </div>

                <!-- Table Container & Sticky Panes -->
                <div class="picker-table-wrapper">
                    <div class="picker-top-scrollbar-wrap" id="reim-top-scroll">
                        <div class="picker-top-scrollbar-inner" id="reim-top-scroll-inner"></div>
                    </div>
                    <div class="picker-main-table-scroll" id="reim-main-scroll">
                        <table class="picker-data-table" id="reim-data-table">
                            <thead id="reim-table-head"></thead>
                            <tbody id="reim-table-body"></tbody>
                            <tfoot id="reim-table-foot"></tfoot>
                        </table>
                    </div>
                </div>
            </div>
        `;

        this.page.main.html(html);

        // Add primary action button to Frappe Page Header
        this.page.set_primary_action(__("➕ 新建报销"), () => {
            this.open_create_reimbursement_modal();
        });
    }

    async load_companies() {
        const r = await frappe.call({ method: REIM_API.companies });
        if (r.message && r.message.companies) {
            this.companies = r.message.companies;
            const $sel = $("#reim-company-select");
            $sel.empty();
            if (this.companies.length > 1) {
                $sel.append(`<option value="All">🌐 全部公司 (汇聚视图)</option>`);
            }
            this.companies.forEach((comp) => {
                $sel.append(`<option value="${comp}">${comp}</option>`);
            });
            if (this.companies.length === 1) {
                this.active_company = this.companies[0];
                $sel.val(this.active_company);
            }
        }
    }

    bind_global_events() {
        const me = this;

        // Company filter
        $("#reim-company-select").on("change", function () {
            me.active_company = $(this).val();
            me.refresh_all();
        });

        // Status filter
        $("#reim-status-btn-group").on("click", ".picker-status-btn", function () {
            $(this).addClass("active").siblings().removeClass("active");
            me.match_status = $(this).data("status");
            me.load_rows();
        });

        // View mode
        $(".picker-view-switch-group").on("click", ".picker-view-btn", function () {
            $(this).addClass("active").siblings().removeClass("active");
            me.view_mode = $(this).data("mode");
            me.load_rows();
        });

        // Inputs debounce
        let filterTimer = null;
        $("#reim-filter-bar").on("input", "input.picker-input", function () {
            clearTimeout(filterTimer);
            filterTimer = setTimeout(() => {
                me.load_rows();
            }, 300);
        });

        // Refresh
        $("#reim-refresh-btn").on("click", () => {
            this.refresh_all();
        });

        // Open create modal
        $("#reim-open-create-modal-btn").on("click", () => {
            this.open_create_reimbursement_modal();
        });

        // Dual scrollbars & Mousewheel horizontal scroll
        this.sync_scrollbars();
    }

    sync_scrollbars() {
        const $top = $("#reim-top-scroll");
        const $main = $("#reim-main-scroll");
        const $inner = $("#reim-top-scroll-inner");
        const $table = $("#reim-data-table");

        const updateWidth = () => {
            const w = $table.outerWidth() || 1200;
            $inner.width(w);
        };

        $top.on("scroll", function () {
            $main.scrollLeft($(this).scrollLeft());
        });
        $main.on("scroll", function () {
            $top.scrollLeft($(this).scrollLeft());
        });

        // Mousewheel on thead & table converts to horizontal scroll
        $("#reim-table-head, #reim-main-scroll").on("wheel", function (e) {
            if (e.originalEvent.deltaY !== 0) {
                const delta = e.originalEvent.deltaY;
                $main.scrollLeft($main.scrollLeft() + delta);
                e.preventDefault();
            }
        });

        $(window).on("resize", updateWidth);
        setTimeout(updateWidth, 300);
    }

    async refresh_all() {
        await Promise.all([this.load_kpis(), this.load_rows()]);
    }

    async load_kpis() {
        const r = await frappe.call({
            method: REIM_API.overview_kpis,
            args: { company: this.active_company },
        });
        if (r.message) {
            this.kpis = r.message;
            $("#reim-kpi-pending-rr").text(this.kpis.pending_rr_count || 0);
            $("#reim-kpi-pi-count").text(this.kpis.pi_count || 0);
            $("#reim-kpi-pr-count").text(this.kpis.pr_count || 0);
            $("#reim-kpi-outstanding-amt").text(format_currency(this.kpis.rr_outstanding || 0));
        }
    }

    get_filter_params() {
        const p = { match_status: this.match_status };
        $("#reim-filter-bar input.picker-input").each(function () {
            const key = $(this).data("filter");
            const val = $(this).val().trim();
            if (val) p[key] = val;
        });
        return p;
    }

    async load_rows() {
        const filters = this.get_filter_params();
        const method = this.view_mode === "doc" ? REIM_API.doc_summary : REIM_API.item_rows;

        const r = await frappe.call({
            method: method,
            args: {
                company: this.active_company,
                filters: filters,
            },
        });

        const data = r.message || { rows: [], total_count: 0, total_amount: 0, total_outstanding: 0 };
        this.cached_rows = data.rows || [];

        $("#reim-loaded-count").text(data.total_count || 0);
        $("#reim-total-summary-badge").text(`统计: ${data.total_count || 0} 笔`);
        $("#reim-sum-total-amt").text(format_currency(data.total_amount || 0));
        $("#reim-sum-outstanding-amt").text(format_currency(data.total_outstanding || 0));

        if (this.view_mode === "doc") {
            this.render_doc_view(this.cached_rows);
        } else {
            this.render_detail_view(this.cached_rows);
        }

        setTimeout(() => {
            const w = $("#reim-data-table").outerWidth() || 1200;
            $("#reim-top-scroll-inner").width(w);
        }, 100);
    }

    render_doc_view(rows) {
        const thead = `
            <tr>
                <th class="text-center ashan-col-w40">#</th>
                <th class="ashan-col-w140">报销单号</th>
                <th class="ashan-col-w160">所属公司</th>
                <th class="ashan-col-w100">报销人员</th>
                <th class="ashan-col-w90 text-center">报销日期</th>
                <th class="ashan-col-w140">发票信息</th>
                <th class="ashan-col-w140">涉及商户</th>
                <th class="ashan-col-w110 text-right">报销总额</th>
                <th class="ashan-col-w110 text-right">待结款金额</th>
                <th class="ashan-col-w90 text-center">状态</th>
                <th class="ashan-col-w160">关联采购单据</th>
            </tr>
        `;
        $("#reim-table-head").html(thead);

        if (!rows.length) {
            $("#reim-table-body").html(`
                <tr>
                    <td colspan="11" class="picker-empty-state">
                        <div class="picker-empty-icon">📂</div>
                        <div class="picker-empty-text">当前筛选条件下暂无报销单数据</div>
                    </td>
                </tr>
            `);
            $("#reim-table-foot").empty();
            return;
        }

        let totalAmt = 0;
        let totalOut = 0;

        const bodyHtml = rows.map((r, idx) => {
            totalAmt += flt(r.total_amount);
            totalOut += flt(r.outstanding_amount);

            return `
                <tr>
                    <td class="text-center font-bold text-muted">${idx + 1}</td>
                    <td>
                        <span class="picker-clickable-doc" onclick="frappe.set_route('Form', 'Reimbursement Request', '${r.rr_name}')">${r.rr_name}</span>
                    </td>
                    <td>${r.company}</td>
                    <td><span class="font-bold">${r.employee_name || r.employee || '-'}</span></td>
                    <td class="text-center font-mono">${r.posting_date}</td>
                    <td>
                        <span class="font-bold">${r.invoice_count || 1} 张</span>
                        <div class="text-muted text-xs font-mono">${r.invoice_preview || r.invoice_nos}</div>
                    </td>
                    <td>
                        <span class="font-bold">${r.supplier_count || 1} 个商户</span>
                        <div class="text-muted text-xs">${r.supplier_preview || r.suppliers}</div>
                    </td>
                    <td class="text-right font-mono font-bold text-primary">${format_currency(r.total_amount)}</td>
                    <td class="text-right font-mono font-bold ${flt(r.outstanding_amount) > 0 ? 'text-amber-600' : 'text-green-600'}">${format_currency(r.outstanding_amount)}</td>
                    <td class="text-center">
                        <span class="picker-status-tag">${r.status_label}</span>
                    </td>
                    <td><span class="text-muted text-xs font-mono">${r.doc_details || r.linked_pis || '-'}</span></td>
                </tr>
            `;
        }).join("");

        $("#reim-table-body").html(bodyHtml);

        const footHtml = `
            <tr>
                <td colspan="7" class="text-right font-bold">合计 (${rows.length} 笔):</td>
                <td class="text-right font-mono font-bold text-primary">${format_currency(totalAmt)}</td>
                <td class="text-right font-mono font-bold text-amber-600">${format_currency(totalOut)}</td>
                <td colspan="2"></td>
            </tr>
        `;
        $("#reim-table-foot").html(footHtml);
    }

    render_detail_view(rows) {
        const thead = `
            <tr>
                <th class="text-center ashan-col-w40">#</th>
                <th class="ashan-col-w140">报销单号</th>
                <th class="ashan-col-w160">所属公司</th>
                <th class="ashan-col-w100">报销人员</th>
                <th class="ashan-col-w140">商户/供应商</th>
                <th class="ashan-col-w120">发票号码</th>
                <th class="ashan-col-w90 text-center">发票类型</th>
                <th class="ashan-col-w140">物料/费用项目</th>
                <th class="ashan-col-w120">规格型号</th>
                <th class="ashan-col-w80 text-right">数量</th>
                <th class="ashan-col-w90 text-right">单价</th>
                <th class="ashan-col-w100 text-right">报销金额</th>
                <th class="ashan-col-w90 text-center">状态</th>
                <th class="ashan-col-w140">来源采购发票</th>
            </tr>
        `;
        $("#reim-table-head").html(thead);

        if (!rows.length) {
            $("#reim-table-body").html(`
                <tr>
                    <td colspan="14" class="picker-empty-state">
                        <div class="picker-empty-icon">📂</div>
                        <div class="picker-empty-text">当前筛选条件下暂无报销明细数据</div>
                    </td>
                </tr>
            `);
            $("#reim-table-foot").empty();
            return;
        }

        let totalQty = 0;
        let totalAmt = 0;

        const bodyHtml = rows.map((r, idx) => {
            totalQty += flt(r.qty);
            totalAmt += flt(r.amount);

            return `
                <tr>
                    <td class="text-center font-bold text-muted">${idx + 1}</td>
                    <td>
                        <span class="picker-clickable-doc" onclick="frappe.set_route('Form', 'Reimbursement Request', '${r.rr_name}')">${r.rr_name}</span>
                    </td>
                    <td>${r.company}</td>
                    <td><span class="font-bold">${r.employee_name || r.employee || '-'}</span></td>
                    <td>${r.supplier || '-'}</td>
                    <td><span class="font-mono text-muted font-bold">${r.invoice_no || '-'}</span></td>
                    <td class="text-center"><span class="picker-status-tag">${r.invoice_type || '专用发票'}</span></td>
                    <td><span class="font-bold">${r.item_name}</span></td>
                    <td>${r.spec || '-'}</td>
                    <td class="text-right font-mono">${r.qty}</td>
                    <td class="text-right font-mono">${format_currency(r.rate)}</td>
                    <td class="text-right font-mono font-bold text-primary">${format_currency(r.amount)}</td>
                    <td class="text-center"><span class="picker-status-tag">${r.status_label}</span></td>
                    <td><span class="text-muted font-mono text-xs">${r.source_pi}</span></td>
                </tr>
            `;
        }).join("");

        $("#reim-table-body").html(bodyHtml);

        const footHtml = `
            <tr>
                <td colspan="9" class="text-right font-bold">合计:</td>
                <td class="text-right font-mono font-bold">${totalQty.toFixed(2)}</td>
                <td></td>
                <td class="text-right font-mono font-bold text-primary">${format_currency(totalAmt)}</td>
                <td colspan="2"></td>
            </tr>
        `;
        $("#reim-table-foot").html(footHtml);
    }

    // =========================================================================
    // Multi-Tax-Invoice Reimbursement Dialog (V2 Smart Entry)
    // =========================================================================

    open_create_reimbursement_modal() {
        this.reset_creation_state();

        const d = new frappe.ui.Dialog({
            title: __("🧾 新建现金报销 · 多发票智能归集"),
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "root_html",
                },
            ],
            primary_action_label: __("🚀 确认创建报销"),
            primary_action: () => this.submit_create_reimbursement_v2(),
        });

        this.creation.dialog = d;
        d.show();

        const $wrapper = d.fields_dict.root_html.$wrapper;
        $wrapper.html(this.get_creation_dialog_html());

        this.bind_creation_dialog_events($wrapper);
        this.load_creation_defaults();
    }

    reset_creation_state() {
        this.creation.active_tab = "select";
        this.creation.company = this.active_company !== "All" ? this.active_company : (this.companies[0] || null);
        this.creation.employee = null;
        this.creation.employee_name = null;
        this.creation.posting_date = frappe.datetime.get_today();
        this.creation.title = "";
        this.creation.auto_receive_stock = 1;
        this.creation.candidate_rows = [];
        this.creation.selected_invoices = new Map();
        this.creation.preview = null;
        this.creation.resolutions = { suppliers: {}, items: {}, warehouses: {} };
        this.creation.latest_request = 0;
        this.creation.loading = false;
        this.creation.upload_files = [];
    }

    get_creation_dialog_html() {
        return `
            <div class="reim-v2-modal-container">
                <!-- Section 1: Business Context & Employee -->
                <div class="reim-v2-section-card">
                    <div class="reim-v2-section-header">
                        <div class="reim-v2-section-title">🏢 1. 报销业务上下文与基本信息</div>
                    </div>
                    <div class="reim-v2-grid-4">
                        <div class="reim-v2-field-group">
                            <label>所属公司<span class="req">*</span></label>
                            <select id="modal-reim-company" class="reim-v2-input-control"></select>
                        </div>
                        <div class="reim-v2-field-group">
                            <label>报销人员 (员工)<span class="req">*</span></label>
                            <input type="text" id="modal-reim-employee" class="reim-v2-input-control" placeholder="输入员工工号/姓名..." />
                        </div>
                        <div class="reim-v2-field-group">
                            <label>报销申请日期<span class="req">*</span></label>
                            <input type="date" id="modal-reim-date" class="reim-v2-input-control" value="${frappe.datetime.get_today()}" />
                        </div>
                        <div class="reim-v2-field-group">
                            <label>报销用途 / 标题</label>
                            <input type="text" id="modal-reim-title" class="reim-v2-input-control" placeholder="例: 8月差旅与零星采购报销..." />
                        </div>
                    </div>
                    <label class="reim-v2-toggle-box">
                        <input type="checkbox" id="modal-reim-auto-stock" checked />
                        <span>📦 包含允许维护库存的物料时，系统全自动生成采购入库单并完成过账 (默认开启)</span>
                    </label>
                </div>

                <!-- Section 2: Invoice Source Workspace -->
                <div class="reim-v2-section-card">
                    <div class="reim-v2-tab-nav">
                        <button type="button" class="reim-v2-tab-btn active" data-tab="select">📑 从税局发票库选择</button>
                        <button type="button" class="reim-v2-tab-btn" data-tab="upload">📤 上传新发票 (PDF/XML/OFD/ZIP)</button>
                    </div>

                    <!-- Tab A: Select From Tax Invoice Library -->
                    <div id="reim-tab-select-content">
                        <div class="reim-v2-filter-toolbar">
                            <div class="reim-v2-filter-inputs">
                                <input type="text" id="modal-reim-search" class="reim-v2-input-control reim-v2-search-input" placeholder="搜索发票号 / 销售方 / 明细摘要..." />
                                <input type="date" id="modal-reim-from-date" class="reim-v2-input-control reim-v2-date-input" title="开票日期起" />
                                <input type="date" id="modal-reim-to-date" class="reim-v2-input-control reim-v2-date-input" title="开票日期止" />
                                <select id="modal-reim-pi-mode" class="reim-v2-input-control reim-v2-select-input">
                                    <option value="">全部发票状态</option>
                                    <option value="need_pi">待生成采购发票</option>
                                    <option value="has_pi">已有采购发票(复用)</option>
                                </select>
                            </div>
                            <div class="reim-v2-tool-btns">
                                <button type="button" class="reim-v2-btn-sm" id="modal-reim-select-all-btn">全选当前</button>
                                <button type="button" class="reim-v2-btn-sm" id="modal-reim-clear-btn">清空选择</button>
                                <button type="button" class="reim-v2-btn-sm" id="modal-reim-refresh-candidates-btn">🔄 刷新</button>
                            </div>
                        </div>

                        <!-- Candidates Table -->
                        <div class="reim-v2-table-container">
                            <table class="reim-v2-table">
                                <thead>
                                    <tr>
                                        <th class="ashan-col-w40 text-center"><input type="checkbox" id="modal-reim-th-checkbox" /></th>
                                        <th class="ashan-col-w90 text-center">开票日期</th>
                                        <th class="ashan-col-w160">销售方名称</th>
                                        <th class="ashan-col-w90 text-center">发票类型</th>
                                        <th class="ashan-col-w140">发票内容摘要</th>
                                        <th class="ashan-col-w110">发票号码</th>
                                        <th class="ashan-col-w100 text-right">发票金额</th>
                                        <th class="ashan-col-w90 text-center">ERP状态</th>
                                        <th class="ashan-col-w100 text-center">处理状态</th>
                                    </tr>
                                </thead>
                                <tbody id="modal-reim-candidates-body">
                                    <tr>
                                        <td colspan="9" class="picker-empty-state">
                                            <div class="picker-empty-icon">⏳</div>
                                            <div class="picker-empty-text">正在查询可用税局发票...</div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Tab B: Upload New Invoices -->
                    <div id="reim-tab-upload-content" class="reim-v2-hidden">
                        <div class="reim-v2-dropzone" id="reim-upload-dropzone">
                            <div class="reim-v2-dropzone-icon">📤</div>
                            <div class="reim-v2-dropzone-text">点击或拖拽发票文件至此处上传 (支持 PDF, XML, OFD, ZIP)</div>
                            <div class="reim-v2-dropzone-sub">系统将自动调用税局发票智能解析引擎，解析成功后自动加入当前报销发票集合</div>
                            <input type="file" id="modal-reim-file-input" multiple accept=".pdf,.xml,.ofd,.zip" class="reim-v2-hidden" />
                        </div>
                        <div class="reim-v2-upload-list" id="modal-reim-upload-list"></div>
                    </div>

                    <!-- Issues Box -->
                    <div class="reim-v2-issues-container reim-v2-hidden" id="modal-reim-issues-box">
                        <div class="font-bold mb-1">⚠️ 报销单据预检提醒：</div>
                        <div id="modal-reim-issues-list"></div>
                    </div>
                </div>

                <!-- Section 3: Summary Dashboard & Submit -->
                <div class="reim-v2-summary-bar">
                    <div class="reim-v2-summary-left">
                        <div class="reim-v2-discipline-badge">
                            <span>🛡️ 财务纪律</span>
                            <span>系统严格执行 1张发票对应1张采购发票，并自动关联报销申请单</span>
                        </div>
                    </div>
                    <div class="reim-v2-summary-stats">
                        <div class="reim-v2-stat-item">
                            <span class="reim-v2-stat-label">已选发票</span>
                            <span class="reim-v2-stat-val" id="modal-reim-sum-inv-count">0 张</span>
                        </div>
                        <div class="reim-v2-stat-item">
                            <span class="reim-v2-stat-label">涉及商户</span>
                            <span class="reim-v2-stat-val" id="modal-reim-sum-supp-count">0 个</span>
                        </div>
                        <div class="reim-v2-stat-item">
                            <span class="reim-v2-stat-label">复用采购发票</span>
                            <span class="reim-v2-stat-val" id="modal-reim-sum-reuse-count">0 张</span>
                        </div>
                        <div class="reim-v2-stat-item">
                            <span class="reim-v2-stat-label">待生成采购发票</span>
                            <span class="reim-v2-stat-val" id="modal-reim-sum-new-count">0 张</span>
                        </div>
                        <div class="reim-v2-stat-item">
                            <span class="reim-v2-stat-label">本次报销总额 (应付)</span>
                            <span class="reim-v2-stat-val primary" id="modal-reim-sum-grand-total">¥ 0.00</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async load_creation_defaults() {
        const r = await frappe.call({
            method: REIM_API.creation_defaults,
            args: { company: this.creation.company },
        });

        if (r.message) {
            const defs = r.message;
            const $compSel = $("#modal-reim-company");
            $compSel.empty();
            defs.companies.forEach((c) => {
                $compSel.append(`<option value="${c}" ${c === defs.company ? "selected" : ""}>${c}</option>`);
            });

            this.creation.company = defs.company;
            this.creation.employee = defs.employee;
            this.creation.employee_name = defs.employee_name;

            if (defs.employee) {
                $("#modal-reim-employee").val(defs.employee_name ? `${defs.employee_name} (${defs.employee})` : defs.employee);
            }

            this.load_tax_invoice_candidates();
        }
    }

    bind_creation_dialog_events($wrapper) {
        const me = this;

        // Company change
        $wrapper.on("change", "#modal-reim-company", function () {
            me.creation.company = $(this).val();
            me.creation.selected_invoices.clear();
            me.load_tax_invoice_candidates();
        });

        // Tabs
        $wrapper.on("click", ".reim-v2-tab-btn", function () {
            $(this).addClass("active").siblings().removeClass("active");
            const tab = $(this).data("tab");
            me.creation.active_tab = tab;
            if (tab === "select") {
                $("#reim-tab-select-content").show();
                $("#reim-tab-upload-content").hide();
            } else {
                $("#reim-tab-select-content").hide();
                $("#reim-tab-upload-content").show();
            }
        });

        // Filter search input
        let searchTimer = null;
        $wrapper.on("input", "#modal-reim-search, #modal-reim-from-date, #modal-reim-to-date", function () {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                me.load_tax_invoice_candidates();
            }, 300);
        });

        $wrapper.on("change", "#modal-reim-pi-mode", function () {
            me.load_tax_invoice_candidates();
        });

        $wrapper.on("click", "#modal-reim-refresh-candidates-btn", function () {
            me.load_tax_invoice_candidates();
        });

        // Select All / Clear
        $wrapper.on("click", "#modal-reim-select-all-btn", function () {
            me.creation.candidate_rows.forEach((r) => {
                if (r.eligibility !== "blocked") {
                    me.creation.selected_invoices.set(r.name, r);
                }
            });
            me.render_tax_invoice_rows();
            me.schedule_preview();
        });

        $wrapper.on("click", "#modal-reim-clear-btn", function () {
            me.creation.selected_invoices.clear();
            me.render_tax_invoice_rows();
            me.schedule_preview();
        });

        // Checkbox individual toggle
        $wrapper.on("change", ".modal-reim-row-checkbox", function () {
            const name = $(this).data("name");
            const checked = $(this).is(":checked");
            const row = me.creation.candidate_rows.find((r) => r.name === name);
            if (row) {
                me.toggle_tax_invoice(row, checked);
            }
        });

        // Header Checkbox
        $wrapper.on("change", "#modal-reim-th-checkbox", function () {
            const checked = $(this).is(":checked");
            me.creation.candidate_rows.forEach((r) => {
                if (r.eligibility !== "blocked") {
                    if (checked) {
                        me.creation.selected_invoices.set(r.name, r);
                    } else {
                        me.creation.selected_invoices.delete(r.name);
                    }
                }
            });
            me.render_tax_invoice_rows();
            me.schedule_preview();
        });

        // Upload Dropzone
        const $dropzone = $("#reim-upload-dropzone");
        const $fileInput = $("#modal-reim-file-input");

        $dropzone.on("click", () => $fileInput.click());

        $dropzone.on("dragover", (e) => {
            e.preventDefault();
            $dropzone.addClass("dragover");
        });
        $dropzone.on("dragleave", () => {
            $dropzone.removeClass("dragover");
        });
        $dropzone.on("drop", (e) => {
            e.preventDefault();
            $dropzone.removeClass("dragover");
            const files = e.originalEvent.dataTransfer.files;
            if (files && files.length) {
                me.handle_upload_files(files);
            }
        });

        $fileInput.on("change", function () {
            if (this.files && this.files.length) {
                me.handle_upload_files(this.files);
            }
        });
    }

    async load_tax_invoice_candidates() {
        const filters = {
            search: $("#modal-reim-search").val(),
            from_date: $("#modal-reim-from-date").val(),
            to_date: $("#modal-reim-to-date").val(),
            pi_mode: $("#modal-reim-pi-mode").val(),
        };

        const r = await frappe.call({
            method: REIM_API.candidates,
            args: {
                company: this.creation.company,
                filters: filters,
                start: 0,
                page_length: 100,
            },
        });

        const data = r.message || { rows: [] };
        this.creation.candidate_rows = data.rows || [];
        this.render_tax_invoice_rows();
    }

    render_tax_invoice_rows() {
        const rows = this.creation.candidate_rows;
        const $tbody = $("#modal-reim-candidates-body");

        if (!rows.length) {
            $tbody.html(`
                <tr>
                    <td colspan="9" class="picker-empty-state">
                        <div class="picker-empty-icon">📂</div>
                        <div class="picker-empty-text">未找到符合条件的可用税局发票</div>
                    </td>
                </tr>
            `);
            return;
        }

        const html = rows.map((r) => {
            const isSelected = this.creation.selected_invoices.has(r.name);
            const isBlocked = r.eligibility === "blocked";

            let badgeClass = "reim-v2-badge-ready";
            let statusText = "🟢 可直接报销";
            if (r.eligibility === "need_supplier") {
                badgeClass = "reim-v2-badge-warning";
                statusText = "🟡 待建档供应商";
            } else if (r.eligibility === "need_item") {
                badgeClass = "reim-v2-badge-warning";
                statusText = "🟡 待匹配物料";
            } else if (isBlocked) {
                badgeClass = "reim-v2-badge-blocked";
                statusText = "🔴 不可报销";
            }

            const erpStateBadge = r.matched_purchase_invoice
                ? `<span class="reim-v2-badge-pi">已有 PI (${r.matched_purchase_invoice})</span>`
                : `<span class="picker-status-tag">待生成 PI</span>`;

            return `
                <tr class="${isSelected ? 'selected' : ''} ${isBlocked ? 'blocked' : ''}">
                    <td class="text-center">
                        <input type="checkbox" class="modal-reim-row-checkbox" data-name="${r.name}" ${isSelected ? 'checked' : ''} ${isBlocked ? 'disabled' : ''} />
                    </td>
                    <td class="text-center font-mono">${r.issue_date}</td>
                    <td><span class="font-bold">${r.seller_name}</span></td>
                    <td class="text-center"><span class="picker-status-tag">${r.invoice_type}</span></td>
                    <td>${r.display_summary}</td>
                    <td><span class="font-mono font-bold text-muted" title="${r.invoice_no}">${r.masked_invoice_no}</span></td>
                    <td class="text-right font-mono font-bold text-primary">${format_currency(r.payable_total)}</td>
                    <td class="text-center">${erpStateBadge}</td>
                    <td class="text-center"><span class="${badgeClass}">${statusText}</span></td>
                </tr>
            `;
        }).join("");

        $tbody.html(html);
        this.render_selection_summary();
    }

    toggle_tax_invoice(row, checked) {
        if (checked) {
            if (row.eligibility === "blocked") {
                frappe.show_alert({ message: __("该发票当前不可报销"), indicator: "red" });
                return;
            }
            this.creation.selected_invoices.set(row.name, row);
        } else {
            this.creation.selected_invoices.delete(row.name);
        }
        this.render_tax_invoice_rows();
        this.schedule_preview();
    }

    schedule_preview() {
        clearTimeout(this.creation.preview_timer);
        this.creation.preview_timer = setTimeout(() => {
            this.refresh_creation_preview();
        }, 300);
    }

    async refresh_creation_preview() {
        const names = [...this.creation.selected_invoices.keys()];
        if (!names.length) {
            this.creation.preview = null;
            this.render_selection_summary();
            $("#modal-reim-issues-box").hide();
            return;
        }

        const requestNo = ++this.creation.latest_request;
        const r = await frappe.call({
            method: REIM_API.preview,
            args: {
                company: this.creation.company,
                employee: this.creation.employee || "EMP-PREVIEW",
                tax_invoice_names: names,
                resolutions: this.creation.resolutions,
                auto_receive_stock: this.creation.auto_receive_stock ? 1 : 0,
            },
        });

        if (requestNo !== this.creation.latest_request) return;

        this.creation.preview = r.message || null;
        this.render_selection_summary();
        this.render_preview_issues();
    }

    render_selection_summary() {
        const map = this.creation.selected_invoices;
        const invCount = map.size;
        let grandTotal = 0;
        const suppliers = new Set();
        let reuseCount = 0;
        let newCount = 0;

        map.forEach((row) => {
            grandTotal += flt(row.payable_total);
            if (row.seller_name) suppliers.add(row.seller_name);
            if (row.matched_purchase_invoice) {
                reuseCount++;
            } else {
                newCount++;
            }
        });

        if (this.creation.preview && this.creation.preview.summary) {
            const s = this.creation.preview.summary;
            $("#modal-reim-sum-inv-count").text(`${s.invoice_count} 张`);
            $("#modal-reim-sum-supp-count").text(`${s.supplier_count} 个`);
            $("#modal-reim-sum-reuse-count").text(`${s.existing_pi_count} 张`);
            $("#modal-reim-sum-new-count").text(`${s.new_pi_count} 张`);
            $("#modal-reim-sum-grand-total").text(format_currency(s.grand_total));
        } else {
            $("#modal-reim-sum-inv-count").text(`${invCount} 张`);
            $("#modal-reim-sum-supp-count").text(`${suppliers.size} 个`);
            $("#modal-reim-sum-reuse-count").text(`${reuseCount} 张`);
            $("#modal-reim-sum-new-count").text(`${newCount} 张`);
            $("#modal-reim-sum-grand-total").text(format_currency(grandTotal));
        }

        this.sync_create_button();
    }

    render_preview_issues() {
        if (!this.creation.preview) return;
        const issues = [];
        this.creation.preview.invoices.forEach((inv) => {
            (inv.issues || []).forEach((iss) => {
                issues.push(`发票 ${inv.invoice_no}: ${iss.message}`);
            });
        });

        if (issues.length) {
            const html = issues.map((msg) => `<div class="reim-v2-issue-item"><span>•</span><span>${msg}</span></div>`).join("");
            $("#modal-reim-issues-list").html(html);
            $("#modal-reim-issues-box").show();
        } else {
            $("#modal-reim-issues-box").hide();
        }
    }

    sync_create_button(isSubmitting = false) {
        if (!this.creation.dialog) return;
        const $btn = this.creation.dialog.get_primary_btn();
        const hasSelection = this.creation.selected_invoices.size > 0;
        const blockingCount = this.creation.preview ? this.creation.preview.blocking_count : 0;

        if (isSubmitting) {
            $btn.prop("disabled", true).text(__("🚀 正在创建全链路单据..."));
        } else if (!hasSelection) {
            $btn.prop("disabled", true).text(__("请先选择发票"));
        } else if (blockingCount > 0) {
            $btn.prop("disabled", true).text(__(`请先处理 ${blockingCount} 项问题`));
        } else {
            $btn.prop("disabled", false).text(__("🚀 确认创建报销"));
        }
    }

    async handle_upload_files(files) {
        const me = this;
        const $list = $("#modal-reim-upload-list");
        $list.empty();

        for (let i = 0; i < files.length; i++) {
            const f = files[i];
            const $item = $(`
                <div class="reim-v2-upload-item">
                    <span>📄 ${f.name} (${(f.size / 1024).toFixed(1)} KB)</span>
                    <span class="text-muted">正在上传解析...</span>
                </div>
            `);
            $list.append($item);

            const formData = new FormData();
            formData.append("file", f);

            try {
                const resp = await fetch("/api/method/" + REIM_API.upload, {
                    method: "POST",
                    headers: {
                        "X-Frappe-CSRF-Token": frappe.csrf_token,
                    },
                    body: formData,
                });
                const res = await resp.json();
                const msg = res.message || {};

                if (msg.ok) {
                    $item.find(".text-muted").removeClass("text-muted").addClass("text-green-600 font-bold").text("✓ 解析成功");
                    if (msg.invoice_names && msg.invoice_names.length) {
                        msg.invoice_names.forEach((invName) => {
                            me.creation.selected_invoices.set(invName, {
                                name: invName,
                                invoice_no: invName,
                                payable_total: 0,
                                eligibility: "ready",
                            });
                        });
                    }
                } else {
                    $item.find(".text-muted").removeClass("text-muted").addClass("text-red-600 font-bold").text("✕ " + (msg.current_message || "解析失败"));
                }
            } catch (err) {
                $item.find(".text-muted").removeClass("text-muted").addClass("text-red-600 font-bold").text("✕ 上传异常");
            }
        }

        // 重新加载候选并更新选择
        await me.load_tax_invoice_candidates();
        me.schedule_preview();
    }

    async submit_create_reimbursement_v2() {
        if (!this.creation.selected_invoices.size) {
            frappe.msgprint(__("请至少选择一张税局发票。"));
            return;
        }

        const empVal = $("#modal-reim-employee").val().trim();
        if (!empVal) {
            frappe.msgprint(__("请填写报销人员。"));
            return;
        }

        // Extract employee code if format is "Name (Code)"
        let employeeCode = empVal;
        const match = empVal.match(/\(([^)]+)\)$/);
        if (match) {
            employeeCode = match[1];
        }

        const dateVal = $("#modal-reim-date").val() || frappe.datetime.get_today();
        const titleVal = $("#modal-reim-title").val().trim();
        const autoStock = $("#modal-reim-auto-stock").is(":checked") ? 1 : 0;
        const names = [...this.creation.selected_invoices.keys()];

        this.sync_create_button(true);

        try {
            const r = await frappe.call({
                method: REIM_API.create_v2,
                type: "POST",
                freeze: true,
                freeze_message: __("正在全自动生成采购与报销单据，请稍候..."),
                args: {
                    company: this.creation.company,
                    employee: employeeCode,
                    posting_date: dateVal,
                    title: titleVal,
                    tax_invoice_names: names,
                    resolutions: this.creation.resolutions,
                    auto_receive_stock: autoStock,
                },
            });

            if (r.message && r.message.success) {
                this.creation.dialog.hide();
                frappe.show_alert({
                    message: __(`🎉 报销申请 ${r.message.rr_name} 创建并过账成功！`),
                    indicator: "green",
                });
                await this.refresh_all();
                frappe.set_route("Form", "Reimbursement Request", r.message.rr_name);
            }
        } catch (err) {
            console.error(err);
        } finally {
            this.sync_create_button(false);
        }
    }
}
