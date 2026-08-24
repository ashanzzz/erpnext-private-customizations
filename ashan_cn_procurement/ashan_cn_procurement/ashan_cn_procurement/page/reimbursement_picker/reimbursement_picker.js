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
    search_items: "ashan_cn_procurement.services.reimbursement_picker_service.search_items_for_reimbursement",
    search_suppliers: "ashan_cn_procurement.services.reimbursement_picker_service.get_suppliers_for_reimbursement",
    quick_create_item: "ashan_cn_procurement.services.reimbursement_picker_service.quick_create_reimbursement_item",
    quick_create_supp: "ashan_cn_procurement.services.reimbursement_picker_service.quick_create_reimbursement_supplier",
    get_detail: "ashan_cn_procurement.services.reimbursement_picker_service.get_reimbursement_detail_for_edit",
    delete_bundle: "ashan_cn_procurement.services.reimbursement_picker_service.delete_reimbursement_bundle",
};

class ReimbursementPicker {
    constructor(page) {
        this.page = page;
        this.active_company = "All";
        this.companies = [];
        this.view_mode = "doc";
        this.match_status = "pending";
        this.cached_rows = [];
        this.kpis = {};
        this.cached_items = [];
        this.cached_suppliers = [];

        this.creation = {
            dialog: null,
            is_edit: false,
            current_rr_name: null,
            company: null,
            posting_date: null,
            title: "",
            auto_receive_stock: 1,
            invoices: [],
            invoice_counter: 0,
            $wrapper: null,
        };

        this.init();
    }

    async init() {
        this.render_layout();
        await this.load_companies();
        this.preload_master_data();
        this.bind_global_events();
        this.refresh_all();
    }

    async preload_master_data() {
        try {
            const [itemRes, suppRes] = await Promise.all([
                frappe.call({ method: REIM_API.search_items, args: { txt: "", limit: 100 } }),
                frappe.call({ method: REIM_API.search_suppliers, args: { txt: "", limit: 100 } }),
            ]);
            if (itemRes.message) this.cached_items = itemRes.message;
            if (suppRes.message) this.cached_suppliers = suppRes.message;
        } catch (e) {
            console.error("Failed to preload master data:", e);
        }
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
                        <label>供应商:</label>
                        <input type="text" class="picker-input" data-filter="supplier" placeholder="搜索供应商..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>发票号码:</label>
                        <input type="text" class="picker-input" data-filter="invoice_no" placeholder="发票号码..." />
                    </div>
                    <div class="picker-filter-group">
                        <label>物料名称:</label>
                        <input type="text" class="picker-input" data-filter="item_code" placeholder="物料代码/名称..." />
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

        $("#reim-company-select").on("change", function () {
            me.active_company = $(this).val();
            me.refresh_all();
        });

        $("#reim-status-btn-group").on("click", ".picker-status-btn", function () {
            $(this).addClass("active").siblings().removeClass("active");
            me.match_status = $(this).data("status");
            me.load_rows();
        });

        $(".picker-view-switch-group").on("click", ".picker-view-btn", function () {
            $(this).addClass("active").siblings().removeClass("active");
            me.view_mode = $(this).data("mode");
            me.load_rows();
        });

        let filterTimer = null;
        $("#reim-filter-bar").on("input", "input.picker-input", function () {
            clearTimeout(filterTimer);
            filterTimer = setTimeout(() => {
                me.load_rows();
            }, 300);
        });

        $("#reim-refresh-btn").on("click", () => {
            this.refresh_all();
        });

        $("#reim-open-create-modal-btn").on("click", () => {
            this.open_create_reimbursement_modal();
        });

        $("#reim-data-table").on("click", ".reim-btn-delete-doc", function (e) {
            e.stopPropagation();
            const rrName = $(this).data("rr-name");
            me.confirm_delete_reimbursement(rrName);
        });

        $("#reim-data-table").on("click", ".picker-clickable-doc", function () {
            const rrName = $(this).data("rr-name");
            me.open_manage_reimbursement_modal(rrName);
        });

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
                <th class="ashan-col-w90 text-center">报销日期</th>
                <th class="ashan-col-w140">发票信息</th>
                <th class="ashan-col-w140">供应商</th>
                <th class="ashan-col-w110 text-right">报销总额</th>
                <th class="ashan-col-w110 text-right">待结款金额</th>
                <th class="ashan-col-w90 text-center">状态</th>
                <th class="ashan-col-w160">关联采购单据</th>
                <th class="ashan-col-w60 text-center">操作</th>
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
                        <span class="picker-clickable-doc" data-rr-name="${r.rr_name}" title="点击打开管理弹窗编辑/删除">${r.rr_name}</span>
                    </td>
                    <td>${r.company}</td>
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
                    <td class="text-center">
                        <button type="button" class="reim-btn-delete-doc" data-rr-name="${r.rr_name}" title="删除报销单及关联采购单据">🗑️</button>
                    </td>
                </tr>
            `;
        }).join("");

        $("#reim-table-body").html(bodyHtml);

        const footHtml = `
            <tr>
                <td colspan="6" class="text-right font-bold">合计 (${rows.length} 笔):</td>
                <td class="text-right font-mono font-bold text-primary">${format_currency(totalAmt)}</td>
                <td class="text-right font-mono font-bold text-amber-600">${format_currency(totalOut)}</td>
                <td colspan="3"></td>
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
                <th class="ashan-col-w140">供应商</th>
                <th class="ashan-col-w120">发票号码</th>
                <th class="ashan-col-w90 text-center">发票类型</th>
                <th class="ashan-col-w140">物料名称</th>
                <th class="ashan-col-w120">规格型号</th>
                <th class="ashan-col-w80 text-right">数量</th>
                <th class="ashan-col-w90 text-right">单价</th>
                <th class="ashan-col-w100 text-right">报销金额</th>
                <th class="ashan-col-w90 text-center">状态</th>
                <th class="ashan-col-w140">来源采购发票</th>
                <th class="ashan-col-w60 text-center">操作</th>
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
                        <span class="picker-clickable-doc" data-rr-name="${r.rr_name}" title="点击打开管理弹窗编辑/删除">${r.rr_name}</span>
                    </td>
                    <td>${r.company}</td>
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
                    <td class="text-center">
                        <button type="button" class="reim-btn-delete-doc" data-rr-name="${r.rr_name}" title="删除报销单及关联采购单据">🗑️</button>
                    </td>
                </tr>
            `;
        }).join("");

        $("#reim-table-body").html(bodyHtml);

        const footHtml = `
            <tr>
                <td colspan="8" class="text-right font-bold">合计:</td>
                <td class="text-right font-mono font-bold">${totalQty.toFixed(2)}</td>
                <td></td>
                <td class="text-right font-mono font-bold text-primary">${format_currency(totalAmt)}</td>
                <td colspan="3"></td>
            </tr>
        `;
        $("#reim-table-foot").html(footHtml);
    }

    // =========================================================================
    // Multi-Invoice Manual Entry & Edit Modal Engine
    // =========================================================================

    open_create_reimbursement_modal() {
        this.reset_creation_state(false, null);
        this.show_reimbursement_dialog(__("🧾 新建现金报销 · 多发票卡片录单"));
        this.add_invoice_card();
    }

    async open_manage_reimbursement_modal(rrName) {
        this.reset_creation_state(true, rrName);
        this.show_reimbursement_dialog(__(`🧾 报销单管理 · ${rrName}`));

        try {
            const r = await frappe.call({
                method: REIM_API.get_detail,
                args: { rr_name: rrName },
            });
            if (r.message) {
                const data = r.message;
                this.creation.company = data.company;
                this.creation.posting_date = data.posting_date;
                this.creation.title = data.title;

                if (this.creation.$wrapper) {
                    this.creation.$wrapper.find("#modal-reim-company").val(data.company);
                    this.creation.$wrapper.find("#modal-reim-date").val(data.posting_date);
                    this.creation.$wrapper.find("#modal-reim-title").val(data.title);
                }

                if (data.invoices && data.invoices.length) {
                    data.invoices.forEach((inv) => {
                        this.add_invoice_card(inv);
                    });
                } else {
                    this.add_invoice_card();
                }
            }
        } catch (e) {
            console.error("Failed to load reimbursement detail:", e);
        }
    }

    reset_creation_state(isEdit = false, rrName = null) {
        this.creation.is_edit = isEdit;
        this.creation.current_rr_name = rrName;
        this.creation.company = this.active_company !== "All" ? this.active_company : (this.companies[0] || null);
        this.creation.posting_date = frappe.datetime.get_today();
        this.creation.title = "";
        this.creation.auto_receive_stock = 1;
        this.creation.invoices = [];
        this.creation.invoice_counter = 0;
        this.creation.$wrapper = null;
    }

    show_reimbursement_dialog(title) {
        if (this.creation.dialog) {
            try {
                this.creation.dialog.hide();
                this.creation.dialog.$wrapper.remove();
            } catch (e) {}
            this.creation.dialog = null;
        }
        $(".modal:has(.reim-v2-modal-container)").remove();

        const isEdit = this.creation.is_edit;
        const me = this;

        const d = new frappe.ui.Dialog({
            title: title,
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "root_html",
                },
            ],
            primary_action_label: isEdit ? __("💾 保存修改") : __("🚀 确认创建报销"),
            primary_action: () => this.submit_manual_reimbursement(),
        });

        if (isEdit) {
            d.add_custom_action(__("🗑️ 删除整单"), () => {
                me.confirm_delete_reimbursement(me.creation.current_rr_name, () => {
                    d.hide();
                });
            }, "btn-danger");
        }

        this.creation.dialog = d;
        d.show();

        const $wrapper = d.fields_dict.root_html.$wrapper;
        this.creation.$wrapper = $wrapper;
        $wrapper.html(this.get_creation_dialog_html());

        this.populate_company_dropdown($wrapper);
        this.bind_creation_dialog_events($wrapper);
    }

    populate_company_dropdown($wrapper) {
        const $sel = $wrapper.find("#modal-reim-company");
        $sel.empty();
        const comps = this.companies.length ? this.companies : [this.creation.company].filter(Boolean);
        comps.forEach((c) => {
            $sel.append(`<option value="${c}">${c}</option>`);
        });
        if (this.creation.company) {
            $sel.val(this.creation.company);
        }
    }

    get_creation_dialog_html() {
        return `
            <div class="reim-v2-modal-container">
                <!-- Section 1: Business Context (报销标题单独占据一整行) -->
                <div class="reim-v2-section-card">
                    <div class="reim-v2-section-header">
                        <div class="reim-v2-section-title">🏢 1. 报销业务信息</div>
                    </div>
                    <div class="reim-v2-grid-2">
                        <div class="reim-v2-field-group">
                            <label>所属公司<span class="req">*</span></label>
                            <select id="modal-reim-company" class="reim-v2-input-control"></select>
                        </div>
                        <div class="reim-v2-field-group">
                            <label>报销申请日期<span class="req">*</span></label>
                            <input type="date" id="modal-reim-date" class="reim-v2-input-control" value="${frappe.datetime.get_today()}" />
                        </div>
                        <div class="reim-full-width-field">
                            <label>报销标题<span class="req">*</span></label>
                            <input type="text" id="modal-reim-title" class="reim-v2-input-control" placeholder="例: 8月差旅与零星物料采购报销..." />
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

    bind_creation_dialog_events($wrapper) {
        const me = this;

        $wrapper.on("change", "#modal-reim-company", function () {
            me.creation.company = $(this).val();
        });

        $wrapper.on("click", "#modal-reim-add-inv-btn", function () {
            me.add_invoice_card();
        });

        $wrapper.on("click", ".reim-btn-delete-inv", function () {
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.remove_invoice_card(invId);
        });

        // Change Invoice Type
        $wrapper.on("change", ".modal-inv-type-select", function () {
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            const typeVal = $(this).val();
            const $card = me.creation.$wrapper ? me.creation.$wrapper.find(`#reim-inv-card-${invId}`) : $(`#reim-inv-card-${invId}`);
            const $noInput = $card.find(".modal-inv-no-input");

            if (typeVal === "无发票") {
                $noInput.val("").prop("placeholder", "无发票 (系统自动编号)").prop("disabled", true);
                $card.find(".modal-row-tax-rate").val("0").prop("disabled", true);
            } else if (typeVal === "普通发票") {
                $noInput.prop("placeholder", "输入发票号码...").prop("disabled", false);
                $card.find(".modal-row-tax-rate").val("0").prop("disabled", true);
            } else {
                $noInput.prop("placeholder", "输入发票号码...").prop("disabled", false);
                $card.find(".modal-row-tax-rate").prop("disabled", false);
                $card.find(".modal-row-tax-rate").each(function () {
                    if ($(this).val() === "0" || !$(this).val()) $(this).val("13");
                });
            }

            $card.find(".modal-inv-tbody tr").each(function () {
                me.handle_row_calc("tax_rate", $(this), invId);
            });
            me.recalculate_invoice(invId);
        });

        $wrapper.on("click", ".reim-btn-add-item-row", function () {
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.add_item_row(invId);
        });

        $wrapper.on("click", ".reim-btn-delete-row", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            $row.remove();
            me.recalculate_invoice(invId);
        });

        // =====================================================================
        // Enterprise Autocomplete (物料与供应商智能浮层，双行排版 + 快捷新建)
        // =====================================================================

        // 1. 物料模糊搜索与智能下拉
        let itemSuggestTimer = null;
        $wrapper.on("input focus", ".modal-row-item-input", function () {
            const $input = $(this);
            const $wrap = $input.closest(".picker-suggest-wrapper");
            const $dd = $wrap.find(".picker-suggest-dropdown");
            const val = $input.val().trim().toLowerCase();

            clearTimeout(itemSuggestTimer);
            itemSuggestTimer = setTimeout(() => {
                const matched = me.cached_items.filter((it) => {
                    if (!val) return true;
                    return (it.item_code && it.item_code.toLowerCase().includes(val)) ||
                           (it.item_name && it.item_name.toLowerCase().includes(val)) ||
                           (it.spec && it.spec.toLowerCase().includes(val));
                }).slice(0, 15);

                let ddHtml = "";
                matched.forEach((it) => {
                    ddHtml += `
                        <div class="picker-suggest-item reim-suggest-item-entry"
                             data-code="${frappe.utils.escape_html(it.item_code)}"
                             data-name="${frappe.utils.escape_html(it.item_name)}"
                             data-spec="${frappe.utils.escape_html(it.spec || '')}"
                             data-uom="${frappe.utils.escape_html(it.uom || '个')}"
                             data-rate="${it.rate || 0}">
                            <div class="picker-suggest-main">
                                <span class="picker-suggest-code">${frappe.utils.escape_html(it.item_code)}</span>
                                <span class="picker-suggest-name">${frappe.utils.escape_html(it.item_name)} (${it.uom || '个'})</span>
                            </div>
                            <div class="picker-suggest-price">¥ ${flt(it.rate || 0).toFixed(2)}</div>
                        </div>
                    `;
                });

                ddHtml += `
                    <div class="picker-suggest-create-btn reim-suggest-create-item-btn">
                        <span>➕</span>
                        <span>新建物料 (Create Item)</span>
                    </div>
                `;

                $dd.html(ddHtml).addClass("is-open");

                const rect = $input[0].getBoundingClientRect();
                $dd.css({
                    top: (rect.bottom + 2) + "px",
                    left: rect.left + "px",
                    width: Math.max(rect.width, 360) + "px",
                });
            }, 150);
        });

        // 选中物料
        $wrapper.on("click", ".reim-suggest-item-entry", function (e) {
            e.stopPropagation();
            const $row = $(this).closest("tr");
            const code = $(this).data("code");
            const name = $(this).data("name");
            const spec = $(this).data("spec");
            const uom = $(this).data("uom");

            $row.find(".modal-row-item-input").val(name);
            $row.find(".modal-row-item-code").val(code);
            $row.find(".modal-row-item-name").val(name);
            $row.find(".modal-row-spec").val(spec || "-");
            $row.find(".modal-row-uom").val(uom || "个");

            $wrapper.find(".picker-suggest-dropdown").removeClass("is-open");
        });

        // 点击 ➕ 新建物料 (Create Item)
        $wrapper.on("click", ".reim-suggest-create-item-btn", function (e) {
            e.stopPropagation();
            const $row = $(this).closest("tr");
            $wrapper.find(".picker-suggest-dropdown").removeClass("is-open");
            me.open_quick_create_item_dialog($row);
        });

        // 2. 供应商模糊搜索与智能下拉
        let suppSuggestTimer = null;
        $wrapper.on("input focus", ".modal-inv-supplier-input", function () {
            const $input = $(this);
            const $wrap = $input.closest(".picker-suggest-wrapper");
            const $dd = $wrap.find(".picker-suggest-dropdown");
            const val = $input.val().trim().toLowerCase();

            clearTimeout(suppSuggestTimer);
            suppSuggestTimer = setTimeout(() => {
                const matched = me.cached_suppliers.filter((s) => {
                    if (!val) return true;
                    return (s.supplier && s.supplier.toLowerCase().includes(val)) ||
                           (s.supplier_name && s.supplier_name.toLowerCase().includes(val));
                }).slice(0, 15);

                let ddHtml = "";
                matched.forEach((s) => {
                    ddHtml += `
                        <div class="picker-suggest-item reim-suggest-supp-entry"
                             data-code="${frappe.utils.escape_html(s.supplier)}"
                             data-name="${frappe.utils.escape_html(s.supplier_name || s.supplier)}">
                            <div class="picker-suggest-main">
                                <span class="picker-suggest-code">${frappe.utils.escape_html(s.supplier)}</span>
                                <span class="picker-suggest-name">${frappe.utils.escape_html(s.supplier_name || s.supplier)}</span>
                            </div>
                        </div>
                    `;
                });

                ddHtml += `
                    <div class="picker-suggest-create-btn reim-suggest-create-supp-btn">
                        <span>➕</span>
                        <span>新建供应商 (Create Supplier)</span>
                    </div>
                `;

                $dd.html(ddHtml).addClass("is-open");

                const rect = $input[0].getBoundingClientRect();
                $dd.css({
                    top: (rect.bottom + 2) + "px",
                    left: rect.left + "px",
                    width: Math.max(rect.width, 360) + "px",
                });
            }, 150);
        });

        // 选中供应商
        $wrapper.on("click", ".reim-suggest-supp-entry", function (e) {
            e.stopPropagation();
            const $card = $(this).closest(".reim-inv-card");
            const suppName = $(this).data("name") || $(this).data("code");
            $card.find(".modal-inv-supplier-input").val(suppName);
            $wrapper.find(".picker-suggest-dropdown").removeClass("is-open");
            me.recalculate_all();
        });

        // 点击 ➕ 新建供应商 (Create Supplier)
        $wrapper.on("click", ".reim-suggest-create-supp-btn", function (e) {
            e.stopPropagation();
            const $card = $(this).closest(".reim-inv-card");
            $wrapper.find(".picker-suggest-dropdown").removeClass("is-open");
            me.open_quick_create_supplier_dialog($card);
        });

        // 点击外部关闭所有 Suggest Dropdown
        $(document).off("click.reim_suggest").on("click.reim_suggest", (e) => {
            if (!$(e.target).closest(".picker-suggest-wrapper").length && !$(e.target).closest(".picker-suggest-dropdown").length) {
                $wrapper.find(".picker-suggest-dropdown.is-open").removeClass("is-open");
            }
        });

        // 滚动关闭
        $wrapper.closest(".modal-body").off("scroll.reim_suggest").on("scroll.reim_suggest", () => {
            $wrapper.find(".picker-suggest-dropdown.is-open").removeClass("is-open");
        });

        // Multi-directional Calculation Handlers
        $wrapper.on("input", ".modal-row-qty", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.handle_row_calc("qty", $row, invId);
        });

        $wrapper.on("input", ".modal-row-rate", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.handle_row_calc("rate", $row, invId);
        });

        $wrapper.on("input", ".modal-row-tax-rate", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.handle_row_calc("tax_rate", $row, invId);
        });

        $wrapper.on("input", ".modal-row-amount-input", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.handle_row_calc("amount", $row, invId);
        });

        $wrapper.on("input", ".modal-row-tax-amount-input", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.handle_row_calc("tax_amount", $row, invId);
        });

        $wrapper.on("input", ".modal-row-line-total-input", function () {
            const $row = $(this).closest("tr");
            const invId = $(this).closest(".reim-inv-card").data("inv-id");
            me.handle_row_calc("line_total", $row, invId);
        });

        // Upload attachment
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

    open_quick_create_item_dialog($row) {
        const me = this;
        const d = new frappe.ui.Dialog({
            title: __("➕ 新建物料 (Create Item)"),
            fields: [
                { fieldtype: "Data", fieldname: "item_code", label: __("物料代码 / 编号"), reqd: 1 },
                { fieldtype: "Data", fieldname: "item_name", label: __("物料名称"), reqd: 1 },
                { fieldtype: "Data", fieldname: "stock_uom", label: __("计量单位"), default: "个", reqd: 1 },
                { fieldtype: "Data", fieldname: "spec", label: __("规格型号") },
                { fieldtype: "Check", fieldname: "is_stock_item", label: __("允许维护库存品 (Stock Item)"), default: 0 },
            ],
            primary_action_label: __("保存并选中"),
            primary_action: async (values) => {
                try {
                    const r = await frappe.call({
                        method: REIM_API.quick_create_item,
                        type: "POST",
                        args: values,
                    });
                    if (r.message && r.message.success) {
                        d.hide();
                        const it = r.message;
                        me.cached_items.unshift(it);

                        $row.find(".modal-row-item-input").val(it.item_name);
                        $row.find(".modal-row-item-code").val(it.item_code);
                        $row.find(".modal-row-item-name").val(it.item_name);
                        $row.find(".modal-row-spec").val(it.spec || "-");
                        $row.find(".modal-row-uom").val(it.uom || "个");

                        frappe.show_alert({ message: __(`物料 [${it.item_code}] ${it.item_name} 已成功创建并回填！`), indicator: "green" });
                    }
                } catch (err) {
                    console.error("Quick create item error:", err);
                }
            },
        });
        d.show();
    }

    open_quick_create_supplier_dialog($card) {
        const me = this;
        const d = new frappe.ui.Dialog({
            title: __("➕ 新建供应商 (Create Supplier)"),
            fields: [
                { fieldtype: "Data", fieldname: "supplier_name", label: __("供应商 / 商户全称"), reqd: 1 },
            ],
            primary_action_label: __("保存并选中"),
            primary_action: async (values) => {
                try {
                    const r = await frappe.call({
                        method: REIM_API.quick_create_supp,
                        type: "POST",
                        args: values,
                    });
                    if (r.message && r.message.success) {
                        d.hide();
                        const supp = r.message;
                        me.cached_suppliers.unshift(supp);
                        $card.find(".modal-inv-supplier-input").val(supp.supplier_name);
                        me.recalculate_all();
                        frappe.show_alert({ message: __(`供应商 [${supp.supplier_name}] 已成功创建并回填！`), indicator: "green" });
                    }
                } catch (err) {
                    console.error("Quick create supplier error:", err);
                }
            },
        });
        d.show();
    }

    handle_row_calc(triggerField, $row, invId) {
        let qty = flt($row.find(".modal-row-qty").val() || 0);
        let rate = flt($row.find(".modal-row-rate").val() || 0);
        let taxRate = flt($row.find(".modal-row-tax-rate").val() || 0);
        let amount = flt($row.find(".modal-row-amount-input").val() || 0);
        let taxAmount = flt($row.find(".modal-row-tax-amount-input").val() || 0);
        let lineTotal = flt($row.find(".modal-row-line-total-input").val() || 0);

        if (triggerField === "qty" || triggerField === "rate") {
            amount = flt(qty * rate, 2);
            taxAmount = flt(amount * (taxRate / 100.0), 2);
            lineTotal = flt(amount + taxAmount, 2);
        } else if (triggerField === "tax_rate") {
            taxAmount = flt(amount * (taxRate / 100.0), 2);
            lineTotal = flt(amount + taxAmount, 2);
        } else if (triggerField === "amount") {
            if (qty > 0) rate = flt(amount / qty, 4);
            taxAmount = flt(amount * (taxRate / 100.0), 2);
            lineTotal = flt(amount + taxAmount, 2);
        } else if (triggerField === "tax_amount") {
            lineTotal = flt(amount + taxAmount, 2);
            if (amount > 0) taxRate = flt((taxAmount / amount) * 100, 2);
        } else if (triggerField === "line_total") {
            amount = flt(lineTotal / (1 + (taxRate / 100.0)), 2);
            taxAmount = flt(lineTotal - amount, 2);
            if (qty > 0) rate = flt(amount / qty, 4);
        }

        if (triggerField !== "qty") $row.find(".modal-row-qty").val(qty ? qty : "");
        if (triggerField !== "rate") $row.find(".modal-row-rate").val(rate ? rate.toFixed(2) : "");
        if (triggerField !== "tax_rate") $row.find(".modal-row-tax-rate").val(taxRate);
        if (triggerField !== "amount") $row.find(".modal-row-amount-input").val(amount ? amount.toFixed(2) : "");
        if (triggerField !== "tax_amount") $row.find(".modal-row-tax-amount-input").val(taxAmount ? taxAmount.toFixed(2) : "");
        if (triggerField !== "line_total") $row.find(".modal-row-line-total-input").val(lineTotal ? lineTotal.toFixed(2) : "");

        this.recalculate_invoice(invId);
    }

    add_invoice_card(initData = null) {
        this.creation.invoice_counter++;
        const invId = this.creation.invoice_counter;

        const initType = initData ? initData.invoice_type : "专用发票";
        const initSupp = initData ? initData.supplier : "";
        const initNo = initData ? initData.invoice_no : "";
        const initDate = initData ? initData.invoice_date : frappe.datetime.get_today();

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

                <!-- Invoice Fields (严格 3 种发票类型, 供应商 Autocomplete 智能浮层) -->
                <div class="reim-inv-fields-grid">
                    <div class="reim-v2-field-group">
                        <label>发票类型<span class="req">*</span></label>
                        <select class="reim-v2-input-control modal-inv-type-select">
                            <option value="专用发票" ${initType === '专用发票' ? 'selected' : ''}>💎 专用发票</option>
                            <option value="普通发票" ${initType === '普通发票' ? 'selected' : ''}>📄 普通发票</option>
                            <option value="无发票" ${initType === '无发票' ? 'selected' : ''}>🚫 无发票</option>
                        </select>
                    </div>
                    <div class="reim-v2-field-group">
                        <label>供应商<span class="req">*</span></label>
                        <div class="picker-suggest-wrapper">
                            <input type="text" class="reim-v2-input-control modal-inv-supplier-input" placeholder="输入或选择供应商..." value="${initSupp}" />
                            <div class="picker-suggest-dropdown" id="reim-supp-dd-${invId}"></div>
                        </div>
                    </div>
                    <div class="reim-v2-field-group">
                        <label>发票号码</label>
                        <input type="text" class="reim-v2-input-control modal-inv-no-input" placeholder="${initType === '无发票' ? '无发票 (系统自动编号)' : '输入发票号码...'}" value="${initNo}" ${initType === '无发票' ? 'disabled' : ''} />
                    </div>
                    <div class="reim-v2-field-group">
                        <label>开票日期<span class="req">*</span></label>
                        <input type="date" class="reim-v2-input-control modal-inv-date-input" value="${initDate}" />
                    </div>
                </div>

                <!-- Item Rows Table -->
                <div class="reim-inv-table-wrap">
                    <table class="reim-inv-table">
                        <thead>
                            <tr>
                                <th class="ashan-col-w40 text-center">#</th>
                                <th class="ashan-col-w160">物料名称<span class="req">*</span></th>
                                <th class="ashan-col-w120">规格型号</th>
                                <th class="ashan-col-w70 text-center">单位</th>
                                <th class="ashan-col-w70 text-right">数量<span class="req">*</span></th>
                                <th class="ashan-col-w80 text-right">单价(元)<span class="req">*</span></th>
                                <th class="ashan-col-w70 text-right">税率(%)</th>
                                <th class="ashan-col-w90 text-right">金额(不含税)</th>
                                <th class="ashan-col-w80 text-right">税额</th>
                                <th class="ashan-col-w90 text-right">价税合计</th>
                                <th class="ashan-col-w110">备注</th>
                                <th class="ashan-col-w40 text-center">操作</th>
                            </tr>
                        </thead>
                        <tbody class="modal-inv-tbody"></tbody>
                    </table>
                </div>

                <!-- Invoice Card Footer -->
                <div class="reim-inv-footer">
                    <div>
                        <button type="button" class="reim-btn-grid-add reim-btn-add-item-row">
                            <span class="font-bold">+</span>
                            <span>添加行</span>
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

        if (initData && initData.items && initData.items.length) {
            initData.items.forEach((item) => {
                this.add_item_row(invId, item);
            });
        } else {
            this.add_item_row(invId);
        }

        this.recalculate_invoice(invId);
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

    add_item_row(invId, initItem = null) {
        const $card = this.creation.$wrapper ? this.creation.$wrapper.find(`#reim-inv-card-${invId}`) : $(`#reim-inv-card-${invId}`);
        const $tbody = $card.find(".modal-inv-tbody");
        const rowIdx = $tbody.find("tr").length + 1;
        const invType = $card.find(".modal-inv-type-select").val() || "专用发票";
        const defaultTaxRate = invType === "专用发票" ? "13" : "0";
        const isTaxDisabled = invType !== "专用发票" ? "disabled" : "";

        const nameVal = initItem ? initItem.item_name : "";
        const specVal = initItem ? (initItem.spec || "-") : "自动带出";
        const uomVal = initItem ? (initItem.uom || "个") : "个";
        const qtyVal = initItem ? initItem.qty : 1;
        const rateVal = initItem ? (flt(initItem.rate).toFixed(2)) : "";
        const taxRateVal = initItem ? initItem.tax_rate : defaultTaxRate;
        const amtVal = initItem ? (flt(initItem.amount).toFixed(2)) : "";
        const taxAmtVal = initItem ? (flt(initItem.tax_amount).toFixed(2)) : "";
        const lineTotalVal = initItem ? (flt(initItem.line_total).toFixed(2)) : "";
        const remarksVal = initItem ? (initItem.remarks || "") : "";

        const rowHtml = `
            <tr data-row-idx="${rowIdx}">
                <td class="text-center font-bold text-muted">${rowIdx}</td>
                <td>
                    <div class="picker-suggest-wrapper">
                        <input type="text" class="reim-cell-input modal-row-item-input" placeholder="输入或选择物料..." value="${nameVal}" />
                        <div class="picker-suggest-dropdown" id="reim-item-dd-${invId}-${rowIdx}"></div>
                        <input type="hidden" class="modal-row-item-code" value="${nameVal}" />
                        <input type="hidden" class="modal-row-item-name" value="${nameVal}" />
                    </div>
                </td>
                <td>
                    <input type="text" class="reim-cell-input readonly modal-row-spec" placeholder="自动带出" value="${specVal}" readonly />
                </td>
                <td>
                    <input type="text" class="reim-cell-input text-center readonly modal-row-uom" value="${uomVal}" readonly />
                </td>
                <td>
                    <input type="number" step="any" min="0.0001" class="reim-cell-input number modal-row-qty" value="${qtyVal}" />
                </td>
                <td>
                    <input type="number" step="any" min="0.01" class="reim-cell-input number modal-row-rate" placeholder="0.00" value="${rateVal}" />
                </td>
                <td>
                    <input type="number" step="any" class="reim-cell-input number modal-row-tax-rate" value="${taxRateVal}" ${isTaxDisabled} />
                </td>
                <td>
                    <input type="number" step="any" class="reim-cell-input number modal-row-amount-input" placeholder="0.00" value="${amtVal}" />
                </td>
                <td>
                    <input type="number" step="any" class="reim-cell-input number modal-row-tax-amount-input" placeholder="0.00" value="${taxAmtVal}" />
                </td>
                <td>
                    <input type="number" step="any" class="reim-cell-input number font-bold text-primary modal-row-line-total-input" placeholder="0.00" value="${lineTotalVal}" />
                </td>
                <td>
                    <input type="text" class="reim-cell-input modal-row-remarks" placeholder="备注..." value="${remarksVal}" />
                </td>
                <td class="text-center">
                    <button type="button" class="reim-btn-delete-row" title="删除此行">✕</button>
                </td>
            </tr>
        `;

        $tbody.append(rowHtml);
    }

    recalculate_invoice(invId) {
        const $card = this.creation.$wrapper ? this.creation.$wrapper.find(`#reim-inv-card-${invId}`) : $(`#reim-inv-card-${invId}`);
        let subtotal = 0;
        let totalTax = 0;

        $card.find(".modal-inv-tbody tr").each(function () {
            const amt = flt($(this).find(".modal-row-amount-input").val() || 0);
            const taxAmt = flt($(this).find(".modal-row-tax-amount-input").val() || 0);
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
                const lineTotal = flt($(this).find(".modal-row-line-total-input").val() || 0);
                grandTotal += lineTotal;
            });
        });

        $("#modal-reim-sum-inv-count").text(`${invCount} 张`);
        $("#modal-reim-sum-supp-count").text(`${suppliers.size} 个`);
        $("#modal-reim-sum-grand-total").text(format_currency(grandTotal));
    }

    confirm_delete_reimbursement(rrName, onSuccess = null) {
        const me = this;
        frappe.confirm(
            __(`⚠️ 确定要删除报销申请单 <strong>${rrName}</strong> 及其关联的所有采购订单、入库单与采购发票吗？此操作不可逆！`),
            async () => {
                try {
                    const r = await frappe.call({
                        method: REIM_API.delete_bundle,
                        type: "POST",
                        args: { rr_name: rrName },
                        freeze: true,
                        freeze_message: __("正在安全级联删除报销单及关联单据..."),
                    });
                    if (r.message && r.message.success) {
                        frappe.show_alert({ message: __(`✓ 报销单 ${rrName} 及关联单据已彻底删除`), indicator: "green" });
                        if (onSuccess) onSuccess();
                        me.refresh_all();
                    }
                } catch (e) {
                    console.error("Delete failed:", e);
                }
            }
        );
    }

    async submit_manual_reimbursement() {
        const company = $("#modal-reim-company").val();
        if (!company) {
            frappe.msgprint(__("请选择所属公司。"));
            return;
        }

        const dateVal = $("#modal-reim-date").val() || frappe.datetime.get_today();
        const titleVal = $("#modal-reim-title").val().trim();
        if (!titleVal) {
            frappe.msgprint(__("请填写报销标题。"));
            return;
        }

        const autoStock = $("#modal-reim-auto-stock").is(":checked") ? 1 : 0;

        const invoicePayload = [];
        let hasErrors = false;

        $(".reim-inv-card").each(function (idx) {
            const cardIdx = idx + 1;
            const invType = $(this).find(".modal-inv-type-select").val();
            const supplier = $(this).find(".modal-inv-supplier-input").val().trim();
            const invoiceNo = $(this).find(".modal-inv-no-input").val().trim();
            const invoiceDate = $(this).find(".modal-inv-date-input").val() || dateVal;

            if (!supplier && invType !== "无发票") {
                frappe.msgprint(__(`发票 #${cardIdx} 请填写供应商名称。`));
                hasErrors = true;
                return false;
            }

            const items = [];
            $(this).find(".modal-inv-tbody tr").each(function (rowIdx) {
                const itemCode = $(this).find(".modal-row-item-code").val().trim();
                const itemName = $(this).find(".modal-row-item-name").val().trim() || $(this).find(".modal-row-item-input").val().trim();
                const spec = $(this).find(".modal-row-spec").val().trim();
                const uom = $(this).find(".modal-row-uom").val().trim() || "个";
                const qty = flt($(this).find(".modal-row-qty").val() || 0);
                const rate = flt($(this).find(".modal-row-rate").val() || 0);
                const taxRate = flt($(this).find(".modal-row-tax-rate").val() || 0);
                const amount = flt($(this).find(".modal-row-amount-input").val() || (qty * rate));
                const taxAmount = flt($(this).find(".modal-row-tax-amount-input").val() || (amount * taxRate / 100));
                const remarks = $(this).find(".modal-row-remarks").val().trim();

                if (!itemName) {
                    frappe.msgprint(__(`发票 #${cardIdx} 第 ${rowIdx + 1} 行物料名称不能为空。`));
                    hasErrors = true;
                    return false;
                }

                if (qty <= 0 || rate <= 0 || amount <= 0) {
                    frappe.msgprint(__(`发票 #${cardIdx} 第 ${rowIdx + 1} 行 [${itemName}] 的数量与单价必须大于0！根据财务纪律，严禁为0。`));
                    hasErrors = true;
                    return false;
                }

                items.push({
                    item_code: itemCode || itemName,
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

        const isEdit = this.creation.is_edit;
        const rrName = this.creation.current_rr_name;

        const $btn = this.creation.dialog.get_primary_btn();
        $btn.prop("disabled", true).text(__("🚀 正在创建全链路单据..."));

        try {
            if (isEdit && rrName) {
                await frappe.call({
                    method: REIM_API.delete_bundle,
                    type: "POST",
                    args: { rr_name: rrName },
                });
            }

            const r = await frappe.call({
                method: REIM_API.create_manual,
                type: "POST",
                freeze: true,
                freeze_message: __("正在全自动生成采购与报销单据 (PO+PR+PI+RR)，请稍候..."),
                args: {
                    company: company,
                    posting_date: dateVal,
                    title: titleVal,
                    auto_receive_stock: autoStock,
                    invoices: JSON.stringify(invoicePayload),
                },
            });

            if (r.message && r.message.success) {
                if (this.creation.dialog) {
                    try {
                        this.creation.dialog.hide();
                        this.creation.dialog.$wrapper.remove();
                    } catch (e) {}
                    this.creation.dialog = null;
                }
                $(".modal, .modal-backdrop").remove();
                $("body").removeClass("modal-open");

                frappe.show_alert({
                    message: __(`🎉 报销申请 ${r.message.rr_name} ${isEdit ? '已更新并过账成功！' : '创建并过账成功！'} 共生成 ${r.message.invoice_count} 张发票单据链。`),
                    indicator: "green",
                });
                await this.refresh_all();
            }
        } catch (err) {
            console.error(err);
        } finally {
            $btn.prop("disabled", false).text(isEdit ? __("💾 保存修改") : __("🚀 确认创建报销"));
        }
    }
}
