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
    create_manual: "ashan_cn_procurement.services.reimbursement_picker_service.create_manual_multi_invoice_reimbursement",
};

class ReimbursementPicker {
    constructor(page) {
        this.page = page;
        this.active_company = "All";
        this.companies = [];
        this.view_mode = "doc"; // 默认单号视图
        this.match_status = "pending";
        this.cached_rows = [];
        this.kpis = {};

        this.creation = {
            dialog: null,
            company: null,
            employee: null,
            employee_name: null,
            posting_date: null,
            title: "",
            auto_receive_stock: 1,
            invoices: [], // List of invoice objects
            invoice_counter: 0,
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
                        <div class="picker-subtitle">现金报销 · 多发票录单与全链路闭环生单</div>
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
                                <span>报销申请 · 多发票卡片录单与全链路闭环生单中心</span>
                            </div>
                            <div class="picker-section-desc">支持单张报销单录入多张发票（专用发票 / 普通发票 / 无发票），可选上传发票附件辅助核对，全自动生成关联采购单据链并汇入报销单 (RR)。</div>
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
    // Multi-Invoice Manual Entry Modal (V3 Smart Form)
    // =========================================================================

    open_create_reimbursement_modal() {
        this.reset_creation_state();

        const d = new frappe.ui.Dialog({
            title: __("🧾 新建现金报销 · 多发票卡片录单"),
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "root_html",
                },
            ],
            primary_action_label: __("🚀 确认创建报销"),
            primary_action: () => this.submit_manual_reimbursement(),
        });

        this.creation.dialog = d;
        d.show();

        const $wrapper = d.fields_dict.root_html.$wrapper;
        this.creation.$wrapper = $wrapper;
        $wrapper.html(this.get_creation_dialog_html());

        this.bind_creation_dialog_events($wrapper);
        this.load_creation_defaults();

        // 默认添加第 1 张发票卡片
        this.add_invoice_card();
    }

    reset_creation_state() {
        this.creation.company = this.active_company !== "All" ? this.active_company : (this.companies[0] || null);
        this.creation.employee = null;
        this.creation.employee_name = null;
        this.creation.posting_date = frappe.datetime.get_today();
        this.creation.title = "";
        this.creation.auto_receive_stock = 1;
        this.creation.invoices = [];
        this.creation.invoice_counter = 0;
        this.creation.$wrapper = null;
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

                <!-- Section 2: Invoice Cards Workspace -->
                <div class="reim-v2-section-card">
                    <div class="reim-v2-section-header">
                        <div class="reim-v2-section-title">
                            <span>🧾 2. 发票列表与录单工作区</span>
                            <span class="text-muted text-xs font-normal">（支持添加多张发票，可选上传附件辅助核对）</span>
                        </div>
                        <div>
                            <button type="button" class="reim-btn-add-inv-card" id="modal-reim-add-inv-btn">
                                <span>➕ 添加发票</span>
                            </button>
                        </div>
                    </div>

                    <!-- Invoices List Container -->
                    <div class="reim-inv-flow-container" id="modal-reim-invoices-container"></div>
                </div>

                <!-- Section 3: Summary Dashboard & Submit -->
                <div class="reim-v2-summary-bar">
                    <div class="reim-v2-summary-left">
                        <div class="reim-v2-discipline-badge">
                            <span>🛡️ 财务纪律</span>
                            <span>严格执行单价与金额大于0，1张发票对应1张采购发票并自动关联报销单</span>
                        </div>
                    </div>
                    <div class="reim-v2-summary-stats">
                        <div class="reim-v2-stat-item">
                            <span class="reim-v2-stat-label">已录发票</span>
                            <span class="reim-v2-stat-val" id="modal-reim-sum-inv-count">0 张</span>
                        </div>
                        <div class="reim-v2-stat-item">
                            <span class="reim-v2-stat-label">涉及商户</span>
                            <span class="reim-v2-stat-val" id="modal-reim-sum-supp-count">0 个</span>
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
        }
    }

    bind_creation_dialog_events($wrapper) {
        const me = this;

        // Company change
        $wrapper.on("change", "#modal-reim-company", function () {
            me.creation.company = $(this).val();
        });

        // Add Invoice Card Button
        $wrapper.on("click", "#modal-reim-add-inv-btn", function () {
            me.add_invoice_card();
        });

        // Delete Invoice Card Button
        $wrapper.on("click", ".reim-btn-delete-inv", function () {
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.remove_invoice_card(invId);
        });

        // Change Invoice Type
        $wrapper.on("change", ".modal-inv-type-select", function () {
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            const typeVal = $(this).val();
            const $card = $(`#reim-inv-card-${invId}`);
            const $noInput = $card.find(".modal-inv-no-input");

            if (typeVal === "无发票") {
                $noInput.val("").prop("placeholder", "无发票 (系统自动生成编号)");
                // 将该发票下所有行税率改为 0
                $card.find(".modal-row-tax-rate").val("0").prop("disabled", true);
            } else if (typeVal === "普通发票") {
                $noInput.prop("placeholder", "输入发票号码...");
                $card.find(".modal-row-tax-rate").val("0").prop("disabled", true);
            } else {
                // 专用发票
                $noInput.prop("placeholder", "输入发票号码...");
                $card.find(".modal-row-tax-rate").prop("disabled", false);
                $card.find(".modal-row-tax-rate").each(function () {
                    if ($(this).val() === "0") $(this).val("13");
                });
            }

            me.recalculate_invoice(invId);
        });

        // Add Row inside an Invoice Card
        $wrapper.on("click", ".reim-btn-add-item-row", function () {
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.add_item_row(invId);
        });

        // Delete Row inside an Invoice Card
        $wrapper.on("click", ".reim-btn-delete-row", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            $row.remove();
            me.recalculate_invoice(invId);
        });

        // Input change on Row (qty, rate, tax_rate)
        $wrapper.on("input", ".modal-row-qty, .modal-row-rate, .modal-row-tax-rate", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");

            const qty = flt($row.find(".modal-row-qty").val() || 0);
            const rate = flt($row.find(".modal-row-rate").val() || 0);
            const taxRate = flt($row.find(".modal-row-tax-rate").val() || 0);

            const amount = flt(qty * rate, 2);
            const taxAmount = flt(amount * (taxRate / 100.0), 2);
            const lineTotal = flt(amount + taxAmount, 2);

            $row.find(".modal-row-amount").text(format_currency(amount));
            $row.find(".modal-row-tax-amount").text(format_currency(taxAmount));
            $row.find(".modal-row-line-total").text(format_currency(lineTotal));

            me.recalculate_invoice(invId);
        });

        // Optional Upload Attachment per Invoice
        $wrapper.on("click", ".reim-btn-upload-attach", function () {
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            const $fileInput = $(`#reim-inv-file-${invId}`);
            $fileInput.click();
        });

        $wrapper.on("change", ".modal-inv-file-input", function () {
            const invId = $(this).data("inv-id");
            const files = this.files;
            if (files && files.length) {
                const file = files[0];
                const $tagWrap = $(`#reim-inv-attach-wrap-${invId}`);
                $tagWrap.html(`
                    <span class="reim-inv-attach-tag" title="${file.name}">
                        📎 ${file.name}
                    </span>
                `);
            }
        });
    }

    add_invoice_card() {
        this.creation.invoice_counter++;
        const invId = this.creation.invoice_counter;

        const cardHtml = `
            <div class="reim-inv-card" id="reim-inv-card-${invId}" data-inv-id="${invId}">
                <!-- Invoice Header -->
                <div class="reim-inv-card-header">
                    <div class="reim-inv-card-title-group">
                        <span class="reim-inv-badge">发票 #${invId}</span>
                        <span class="font-bold text-slate-800 text-sm">录入发票信息与采购明细</span>
                    </div>
                    <div class="reim-v2-tool-btns">
                        <button type="button" class="reim-btn-upload-attach">
                            <span>📎 上传附件 (可选)</span>
                        </button>
                        <input type="file" id="reim-inv-file-${invId}" class="modal-inv-file-input reim-v2-hidden" data-inv-id="${invId}" accept=".pdf,.png,.jpg,.jpeg,.xml,.ofd,.zip" />
                        <span id="reim-inv-attach-wrap-${invId}"></span>
                        <button type="button" class="reim-btn-delete-inv" title="删除该张发票">
                            <span>🗑️ 删除发票</span>
                        </button>
                    </div>
                </div>

                <!-- Invoice Fields -->
                <div class="reim-inv-fields-grid">
                    <div class="reim-v2-field-group">
                        <label>发票类型<span class="req">*</span></label>
                        <select class="reim-v2-input-control modal-inv-type-select">
                            <option value="专用发票">💎 专用发票</option>
                            <option value="普通发票">📄 普通发票</option>
                            <option value="无发票">🚫 无发票</option>
                        </select>
                    </div>
                    <div class="reim-v2-field-group">
                        <label>商户 / 供应商名称<span class="req">*</span></label>
                        <input type="text" class="reim-v2-input-control modal-inv-supplier-input" placeholder="输入商户/供应商名称..." />
                    </div>
                    <div class="reim-v2-field-group">
                        <label>发票号码</label>
                        <input type="text" class="reim-v2-input-control modal-inv-no-input" placeholder="输入发票号码..." />
                    </div>
                    <div class="reim-v2-field-group">
                        <label>开票日期<span class="req">*</span></label>
                        <input type="date" class="reim-v2-input-control modal-inv-date-input" value="${frappe.datetime.get_today()}" />
                    </div>
                </div>

                <!-- Item Rows Table -->
                <div class="reim-inv-table-wrap">
                    <table class="reim-inv-table">
                        <thead>
                            <tr>
                                <th class="ashan-col-w40 text-center">#</th>
                                <th class="ashan-col-w160">物料名称 / 费用项<span class="req">*</span></th>
                                <th class="ashan-col-w120">规格型号</th>
                                <th class="ashan-col-w70 text-center">单位</th>
                                <th class="ashan-col-w70 text-right">数量<span class="req">*</span></th>
                                <th class="ashan-col-w90 text-right">单价(元)<span class="req">*</span></th>
                                <th class="ashan-col-w70 text-right">税率(%)</th>
                                <th class="ashan-col-w90 text-right">金额(不含税)</th>
                                <th class="ashan-col-w80 text-right">税额</th>
                                <th class="ashan-col-w100 text-right">价税合计</th>
                                <th class="ashan-col-w120">备注</th>
                                <th class="ashan-col-w40 text-center">操作</th>
                            </tr>
                        </thead>
                        <tbody class="modal-inv-tbody"></tbody>
                    </table>
                </div>

                <!-- Invoice Card Footer -->
                <div class="reim-inv-footer">
                    <div>
                        <button type="button" class="reim-btn-sm reim-btn-add-item-row">
                            <span>➕ 添加物料明细行</span>
                        </button>
                    </div>
                    <div class="reim-inv-footer-summary">
                        <span>不含税: <strong class="font-mono text-slate-800" id="reim-inv-subtotal-${invId}">¥ 0.00</strong></span>
                        <span>税额: <strong class="font-mono text-slate-800" id="reim-inv-tax-${invId}">¥ 0.00</strong></span>
                        <span>发票合计: <strong class="reim-inv-total-highlight" id="reim-inv-total-${invId}">¥ 0.00</strong></span>
                    </div>
                </div>
            </div>
        `;

        const $container = this.creation.$wrapper ? this.creation.$wrapper.find("#modal-reim-invoices-container") : $("#modal-reim-invoices-container");
        $container.append(cardHtml);

        // 自动为新发票添加第一行
        this.add_item_row(invId);
        this.recalculate_all();
    }

    remove_invoice_card(invId) {
        const count = $(".reim-inv-card").length;
        if (count <= 1) {
            frappe.show_alert({ message: __("至少需要保留一张发票卡片"), indicator: "orange" });
            return;
        }
        $(`#reim-inv-card-${invId}`).remove();
        this.recalculate_all();
    }

    add_item_row(invId) {
        const $card = this.creation.$wrapper ? this.creation.$wrapper.find(`#reim-inv-card-${invId}`) : $(`#reim-inv-card-${invId}`);
        const $tbody = $card.find(".modal-inv-tbody");
        const rowIdx = $tbody.find("tr").length + 1;
        const invType = $card.find(".modal-inv-type-select").val() || "专用发票";
        const defaultTaxRate = invType === "专用发票" ? "13" : "0";
        const isTaxDisabled = invType !== "专用发票" ? "disabled" : "";

        const rowHtml = `
            <tr>
                <td class="text-center font-bold text-muted">${rowIdx}</td>
                <td>
                    <input type="text" class="reim-cell-input modal-row-item-name" placeholder="输入物料/费用名称..." />
                </td>
                <td>
                    <input type="text" class="reim-cell-input modal-row-spec" placeholder="规格型号..." />
                </td>
                <td>
                    <input type="text" class="reim-cell-input text-center modal-row-uom" value="个" />
                </td>
                <td>
                    <input type="number" step="any" min="0.0001" class="reim-cell-input number modal-row-qty" value="1" />
                </td>
                <td>
                    <input type="number" step="any" min="0.01" class="reim-cell-input number modal-row-rate" placeholder="0.00" />
                </td>
                <td>
                    <input type="number" step="any" class="reim-cell-input number modal-row-tax-rate" value="${defaultTaxRate}" ${isTaxDisabled} />
                </td>
                <td class="text-right font-mono modal-row-amount">¥ 0.00</td>
                <td class="text-right font-mono modal-row-tax-amount">¥ 0.00</td>
                <td class="text-right font-mono font-bold text-primary modal-row-line-total">¥ 0.00</td>
                <td>
                    <input type="text" class="reim-cell-input modal-row-remarks" placeholder="备注..." />
                </td>
                <td class="text-center">
                    <button type="button" class="reim-btn-delete-row" title="删除此行">✕</button>
                </td>
            </tr>
        `;

        $tbody.append(rowHtml);
    }

    recalculate_invoice(invId) {
        const $card = $(`#reim-inv-card-${invId}`);
        let subtotal = 0;
        let totalTax = 0;

        $card.find(".modal-inv-tbody tr").each(function () {
            const qty = flt($(this).find(".modal-row-qty").val() || 0);
            const rate = flt($(this).find(".modal-row-rate").val() || 0);
            const taxRate = flt($(this).find(".modal-row-tax-rate").val() || 0);

            const amt = flt(qty * rate, 2);
            const taxAmt = flt(amt * (taxRate / 100.0), 2);

            subtotal += amt;
            totalTax += taxAmt;
        });

        const totalAmt = flt(subtotal + totalTax, 2);

        $(`#reim-inv-subtotal-${invId}`).text(format_currency(subtotal));
        $(`#reim-inv-tax-${invId}`).text(format_currency(totalTax));
        $(`#reim-inv-total-${invId}`).text(format_currency(totalAmt));

        this.recalculate_all();
    }

    recalculate_all() {
        let invCount = 0;
        const suppliers = new Set();
        let grandTotal = 0;

        $(".reim-inv-card").each(function () {
            invCount++;
            const supp = $(this).find(".modal-inv-supplier-input").val().trim();
            if (supp) suppliers.add(supp);

            $(this).find(".modal-inv-tbody tr").each(function () {
                const qty = flt($(this).find(".modal-row-qty").val() || 0);
                const rate = flt($(this).find(".modal-row-rate").val() || 0);
                const taxRate = flt($(this).find(".modal-row-tax-rate").val() || 0);
                const amt = flt(qty * rate, 2);
                const taxAmt = flt(amt * (taxRate / 100.0), 2);
                grandTotal += flt(amt + taxAmt, 2);
            });
        });

        $("#modal-reim-sum-inv-count").text(`${invCount} 张`);
        $("#modal-reim-sum-supp-count").text(`${suppliers.size} 个`);
        $("#modal-reim-sum-grand-total").text(format_currency(grandTotal));
    }

    async submit_manual_reimbursement() {
        const me = this;
        const company = $("#modal-reim-company").val();
        if (!company) {
            frappe.msgprint(__("请选择所属公司。"));
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

        // Collect all invoices and items
        const invoicePayload = [];
        let hasErrors = false;

        $(".reim-inv-card").each(function (idx) {
            const cardIdx = idx + 1;
            const invType = $(this).find(".modal-inv-type-select").val();
            const supplier = $(this).find(".modal-inv-supplier-input").val().trim();
            const invoiceNo = $(this).find(".modal-inv-no-input").val().trim();
            const invoiceDate = $(this).find(".modal-inv-date-input").val() || dateVal;

            if (!supplier && invType !== "无发票") {
                frappe.msgprint(__(`发票 #${cardIdx} 请填写商户/供应商名称。`));
                hasErrors = true;
                return false;
            }

            const items = [];
            $(this).find(".modal-inv-tbody tr").each(function (rowIdx) {
                const itemName = $(this).find(".modal-row-item-name").val().trim();
                const spec = $(this).find(".modal-row-spec").val().trim();
                const uom = $(this).find(".modal-row-uom").val().trim() || "个";
                const qty = flt($(this).find(".modal-row-qty").val() || 0);
                const rate = flt($(this).find(".modal-row-rate").val() || 0);
                const taxRate = flt($(this).find(".modal-row-tax-rate").val() || 0);
                const remarks = $(this).find(".modal-row-remarks").val().trim();

                if (!itemName) {
                    frappe.msgprint(__(`发票 #${cardIdx} 第 ${rowIdx + 1} 行物料名称不能为空。`));
                    hasErrors = true;
                    return false;
                }

                if (qty <= 0 || rate <= 0) {
                    frappe.msgprint(__(`发票 #${cardIdx} 第 ${rowIdx + 1} 行 [${itemName}] 的数量与单价必须大于0！根据财务纪律，严禁为0。`));
                    hasErrors = true;
                    return false;
                }

                const amount = flt(qty * rate, 2);
                const taxAmount = flt(amount * (taxRate / 100.0), 2);

                items.append ? null : items.push({
                    item_code: itemName,
                    item_name: itemName,
                    spec: spec,
                    uom: uom,
                    qty: qty,
                    rate: rate,
                    amount: amount,
                    tax_rate: taxRate,
                    tax_amount: taxAmount,
                    remarks: remarks,
                });
            });

            if (hasErrors) return false;

            if (!items.length) {
                frappe.msgprint(__(`发票 #${cardIdx} 至少需要录入一行有效的明细。`));
                hasErrors = true;
                return false;
            }

            invoicePayload.push({
                invoice_type: invType,
                supplier: supplier,
                invoice_no: invoiceNo,
                invoice_date: invoiceDate,
                items: items,
            });
        });

        if (hasErrors || !invoicePayload.length) return;

        const $btn = this.creation.dialog.get_primary_btn();
        $btn.prop("disabled", true).text(__("🚀 正在创建全链路单据..."));

        try {
            const r = await frappe.call({
                method: REIM_API.create_manual,
                type: "POST",
                freeze: true,
                freeze_message: __("正在全自动生成采购与报销单据 (PO+PR+PI+RR)，请稍候..."),
                args: {
                    company: company,
                    employee: employeeCode,
                    posting_date: dateVal,
                    title: titleVal,
                    auto_receive_stock: autoStock,
                    invoices: JSON.stringify(invoicePayload),
                },
            });

            if (r.message && r.message.success) {
                this.creation.dialog.hide();
                frappe.show_alert({
                    message: __(`🎉 报销申请 ${r.message.rr_name} 创建并过账成功！共生成 ${r.message.invoice_count} 张发票单据链。`),
                    indicator: "green",
                });
                await this.refresh_all();
                frappe.set_route("Form", "Reimbursement Request", r.message.rr_name);
            }
        } catch (err) {
            console.error(err);
        } finally {
            $btn.prop("disabled", false).text(__("🚀 确认创建报销"));
        }
    }
}
