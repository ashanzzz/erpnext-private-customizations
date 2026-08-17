// -*- coding: utf-8 -*-
frappe.pages['property-settlement-workbench'].on_page_load = function(wrapper) {
    $(wrapper).find('.layout-main-section').css({
        'background-color': '#f8f9fa',
        'min-height': 'calc(100vh - 60px)'
    });
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('物业月结'),
        single_column: true
    });
    wrapper.property_settlement_workbench = new PropertyMonthlySettlement(wrapper, page);
};

frappe.pages['property-settlement-workbench'].on_page_show = function(wrapper) {
    $(wrapper).find('.layout-main-section').css({
        'background-color': '#f8f9fa',
        'min-height': 'calc(100vh - 60px)'
    });
    if (wrapper.property_settlement_workbench) {
        wrapper.property_settlement_workbench.refresh();
    }
};


/* ============================================================
   PropertyMonthlySettlement — 物业与租赁月结单页工作台
   ============================================================ */
class PropertyMonthlySettlement {
    constructor(wrapper, page) {
        this.wrapper = wrapper;
        this.page = page;
        this.$container = $(wrapper).find('.layout-main-section');

        const now = new Date();
        this.currentYear = now.getFullYear();
        this.currentMonth = now.getMonth() + 1;

        this.data = null;
        this._isDirty = false;

        this.init_dom();
        this.bind_global_events();
        this.load_month_settlement();
    }

    // ─── 初始化 DOM 骨架 ──────────────────────────────────────
    init_dom() {
        this.$container.html(`
        <div class="prop-settle-wrapper">

            <!-- ❶ 顶部标题与月度控制栏 (高度严格 36px 统一对齐) -->
            <div class="prop-header-bar">
                <div class="prop-title-box">
                    <h3 class="prop-page-title">🏢 物业与租赁月结</h3>
                    <span id="settle-status-badge" class="prop-status-badge status-draft">🟡 草稿录入中</span>
                </div>

                <div class="prop-period-controls">
                    <button class="prop-btn-nav" id="btn-prev-month">◀</button>
                    <select id="sel-settle-year" class="prop-select-period"></select>
                    <select id="sel-settle-month" class="prop-select-period"></select>
                    <button class="prop-btn-nav" id="btn-next-month">▶</button>
                    <button class="prop-btn-nav" id="btn-cur-month">本月</button>
                </div>

                <div class="prop-mgmt-box">
                    <label>物业公司:</label>
                    <input type="text" id="inp-prop-mgmt" class="prop-mgmt-input" value="天津金利达物业管理有限公司" placeholder="天津金利达物业管理有限公司" />
                </div>

                <div class="prop-actions">
                    <button class="prop-btn prop-btn-secondary" id="btn-save-draft">💾 保存草稿</button>
                    <div class="btn-group">
                        <button type="button" class="prop-btn prop-btn-excel" id="btn-export-dropdown">
                            📥 导出 Excel ▾
                        </button>
                        <div class="dropdown-menu dropdown-menu-right" id="menu-export-excel">
                            <a class="dropdown-item" href="#" id="act-export-full">📊 导出【全套月结工作簿】(含各分公司与合计)</a>
                            <div class="dropdown-divider"></div>
                            <a class="dropdown-item" href="#" id="act-export-total">📑 导出【全公司合计单证】Excel</a>
                            <div class="dropdown-divider"></div>
                            <div id="comp-export-items"></div>
                        </div>
                    </div>
                    <button class="prop-btn prop-btn-primary" id="btn-preview-bills">📄 单证预览/打印</button>
                    <button class="prop-btn prop-btn-lock" id="btn-finalize-settle">🔒 完成本月结算</button>
                    <button class="prop-btn prop-btn-unlock" id="btn-revert-settle" style="display:none;">🔓 取消结算</button>
                </div>
            </div>

            <!-- ❷ 公司结算汇总看板 -->
            <div class="prop-card-section">
                <div class="prop-section-header">
                    <span class="sec-title">📊 本月公司结算汇总看板</span>
                    <span class="sec-tip">💡 依据水电实际读数、调配分摊与租赁收费标准自动核算</span>
                </div>
                <div class="prop-table-responsive">
                    <table class="prop-summary-table" id="table-comp-summary">
                        <thead>
                            <tr>
                                <th style="min-width: 140px;">结算公司</th>
                                <th style="text-align: right;">房租金额</th>
                                <th style="text-align: right;">物业费金额</th>
                                <th style="text-align: right;">核定电量(kWh)</th>
                                <th style="text-align: right;">电费金额</th>
                                <th style="text-align: right;">核定水量(m³)</th>
                                <th style="text-align: right;">水费金额</th>
                                <th style="text-align: right;">调整金额</th>
                                <th style="text-align: right; background: #ecfdf5; color: #065f46;">本月应付总额</th>
                                <th style="text-align: center; width: 140px;">单证与打印</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-comp-summary"></tbody>
                    </table>
                </div>
            </div>

            <!-- ❸ 电表抄表矩阵 -->
            <div class="prop-card-section">
                <div class="prop-section-header">
                    <div class="sec-title-with-rate">
                        <span class="sec-title">⚡ 电表抄表与核算</span>
                        <div class="rate-config-box">
                            <label>本月含税电价:</label>
                            <input type="number" step="0.0001" id="inp-elec-price" class="rate-input" />
                            <span class="unit">元/kWh</span>
                            <span class="tax-tip">(含税 13%)</span>
                        </div>
                    </div>
                </div>
                <div class="prop-table-responsive">
                    <table class="prop-excel-table" id="table-elec-meters">
                        <thead>
                            <tr>
                                <th style="width: 130px;">归属公司</th>
                                <th style="width: 90px; text-align: center;">表号</th>
                                <th style="min-width: 140px;">表具名称</th>
                                <th style="width: 110px; text-align: right;">上期表数</th>
                                <th style="width: 120px; text-align: right; background: #fefce8;">本期表数</th>
                                <th style="width: 90px; text-align: right;">原始差值</th>
                                <th style="width: 80px; text-align: center;">倍率</th>
                                <th style="width: 110px; text-align: right; background: #eff6ff; color: #1e40af;">核定度数(kWh)</th>
                                <th style="width: 110px; text-align: right; background: #fef2f2; color: #991b1b;">含税电费</th>
                                <th style="min-width: 120px;">抄表备注</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-elec-meters"></tbody>
                    </table>
                </div>
            </div>

            <!-- ❹ 水表抄表矩阵 -->
            <div class="prop-card-section">
                <div class="prop-section-header">
                    <div class="sec-title-with-rate">
                        <span class="sec-title">💧 水表抄表与核算</span>
                        <div class="rate-config-box">
                            <label>本月含税水价:</label>
                            <input type="number" step="0.01" id="inp-water-price" class="rate-input" />
                            <span class="unit">元/m³</span>
                            <span class="tax-tip">(含税 9%)</span>
                        </div>
                    </div>
                </div>
                <div class="prop-table-responsive">
                    <table class="prop-excel-table" id="table-water-meters">
                        <thead>
                            <tr>
                                <th style="width: 130px;">归属公司</th>
                                <th style="width: 90px; text-align: center;">表号</th>
                                <th style="min-width: 140px;">表具名称</th>
                                <th style="width: 110px; text-align: right;">上期表数</th>
                                <th style="width: 120px; text-align: right; background: #fefce8;">本期表数</th>
                                <th style="width: 90px; text-align: right;">原始差值</th>
                                <th style="width: 80px; text-align: center;">倍率</th>
                                <th style="width: 110px; text-align: right; background: #eff6ff; color: #1e40af;">核定水量(m³)</th>
                                <th style="width: 110px; text-align: right; background: #fef2f2; color: #991b1b;">含税水费</th>
                                <th style="min-width: 120px;">抄表备注</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-water-meters"></tbody>
                    </table>
                </div>
            </div>

            <!-- ❺ 费用调整明细 (支持按用量/按金额、单公司/公司间转移) -->
            <div class="prop-card-section">
                <div class="prop-section-header">
                    <span class="sec-title">💰 本月费用调整 (公司间转移 / 单项修正)</span>
                    <button class="prop-btn prop-btn-secondary" id="btn-add-adj">➕ 添加费用调整</button>
                </div>
                <div class="prop-table-responsive">
                    <table class="prop-excel-table" id="table-adjustments">
                        <thead>
                            <tr>
                                <th style="width: 100px;">调整方式</th>
                                <th style="width: 90px;">费用类型</th>
                                <th style="width: 110px;">调整范围</th>
                                <th style="width: 130px;">转出/扣减方</th>
                                <th style="width: 130px;">转入/归属方</th>
                                <th style="width: 110px; text-align: right;">输入调整值</th>
                                <th style="width: 110px; text-align: right;">等效用量</th>
                                <th style="width: 110px; text-align: right; color: #b45309;">调整金额</th>
                                <th style="min-width: 160px;">调整原因说明</th>
                                <th style="width: 60px; text-align: center;">操作</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-adjustments"></tbody>
                    </table>
                </div>
            </div>

            <!-- ❻ 固定房租与物业费明细 (平米单价·日/月/年多周期自选与物业费自选) -->
            <div class="prop-card-section">
                <div class="prop-section-header">
                    <span class="sec-title">🏠 房租与物业费明细 (按平米·日/月/年单价自动核算)</span>
                    <span class="sec-tip">💡 支持按日/月/年自选单价，支持房租含物业或每平米独立计收物业费</span>
                </div>
                <div class="prop-table-responsive">
                    <table class="prop-excel-table" id="table-leases">
                        <thead>
                            <tr>
                                <th style="width: 130px;">所属公司</th>
                                <th style="min-width: 150px;">场地名称</th>
                                <th style="width: 90px; text-align: right;">面积(㎡)</th>
                                <th style="width: 130px;">房租计价与单价</th>
                                <th style="width: 130px;">物业费模式/单价</th>
                                <th style="width: 70px; text-align: center;">计费天数</th>
                                <th style="width: 100px; text-align: right;">房租金额</th>
                                <th style="width: 100px; text-align: right;">物业费金额</th>
                                <th style="width: 110px; text-align: right; background: #ecfdf5; color: #065f46;">本月含税小计</th>
                                <th style="width: 80px; text-align: right;">税额</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-leases"></tbody>
                    </table>
                </div>
            </div>

        </div>
        `);
    }

    // ─── 全局事件绑定 ─────────────────────────────────────────
    bind_global_events() {
        const self = this;

        // 年月下拉初始化
        const $selY = this.$container.find('#sel-settle-year');
        const $selM = this.$container.find('#sel-settle-month');

        for (let y = this.currentYear - 3; y <= this.currentYear + 2; y++) {
            $selY.append(`<option value="${y}" ${y === self.currentYear ? 'selected' : ''}>${y}年</option>`);
        }
        for (let m = 1; m <= 12; m++) {
            $selM.append(`<option value="${m}" ${m === self.currentMonth ? 'selected' : ''}>${m < 10 ? '0' + m : m}月</option>`);
        }

        $selY.on('change', () => {
            self.currentYear = parseInt($selY.val());
            self.load_month_settlement();
        });
        $selM.on('change', () => {
            self.currentMonth = parseInt($selM.val());
            self.load_month_settlement();
        });

        // 物业公司输入修改
        this.$container.find('#inp-prop-mgmt').on('change input', function() {
            if (self.data) {
                self.data.property_management_company = $(this).val();
            }
        });

        // 导航按钮
        this.$container.find('#btn-prev-month').on('click', () => {
            if (self.currentMonth === 1) {
                self.currentYear -= 1;
                self.currentMonth = 12;
            } else {
                self.currentMonth -= 1;
            }
            $selY.val(self.currentYear);
            $selM.val(self.currentMonth);
            self.load_month_settlement();
        });

        this.$container.find('#btn-next-month').on('click', () => {
            if (self.currentMonth === 12) {
                self.currentYear += 1;
                self.currentMonth = 1;
            } else {
                self.currentMonth += 1;
            }
            $selY.val(self.currentYear);
            $selM.val(self.currentMonth);
            self.load_month_settlement();
        });

        this.$container.find('#btn-cur-month').on('click', () => {
            const now = new Date();
            self.currentYear = now.getFullYear();
            self.currentMonth = now.getMonth() + 1;
            $selY.val(self.currentYear);
            $selM.val(self.currentMonth);
            self.load_month_settlement();
        });

        // 单价修改即时触发重算
        this.$container.find('#inp-elec-price, #inp-water-price').on('input change', () => {
            self.recalculate();
        });

        // 保存草稿
        this.$container.find('#btn-save-draft').on('click', () => {
            self.save_draft();
        });

        // 导出 Excel 菜单与点击控制
        const $btnDropdown = this.$container.find('#btn-export-dropdown');
        const $menuDropdown = this.$container.find('#menu-export-excel');

        $btnDropdown.on('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            $menuDropdown.toggle();
        });

        $(document).on('click.prop_excel_menu', (e) => {
            if (!$(e.target).closest('#btn-export-dropdown, #menu-export-excel').length) {
                $menuDropdown.hide();
            }
        });

        this.$container.find('#act-export-full').on('click', (e) => {
            e.preventDefault();
            $menuDropdown.hide();
            self.download_excel('all');
        });
        this.$container.find('#act-export-total').on('click', (e) => {
            e.preventDefault();
            $menuDropdown.hide();
            self.download_excel('total');
        });

        // 添加调整弹窗
        this.$container.find('#btn-add-adj').on('click', () => {
            self.open_add_adjustment_dialog();
        });

        // 完成本月结算
        this.$container.find('#btn-finalize-settle').on('click', () => {
            self.open_finalize_confirm_dialog();
        });

        // 取消结算
        this.$container.find('#btn-revert-settle').on('click', () => {
            self.revert_settlement();
        });

        // 预览全部结算单
        this.$container.find('#btn-preview-bills').on('click', () => {
            self.open_bills_preview_dialog();
        });
    }

    refresh() {
        this.load_month_settlement();
    }

    // ─── 加载月份数据 ─────────────────────────────────────────
    load_month_settlement() {
        const self = this;
        frappe.call({
            method: 'ashan_cn_procurement.ashan_cn_procurement.page.property_settlement_workbench.property_settlement_workbench.get_settlement',
            args: {
                year: self.currentYear,
                month: self.currentMonth
            },
            callback(r) {
                if (r.message) {
                    self.data = r.message;
                    self.render_all();
                }
            }
        });
    }

    // ─── 渲染整个页面 ─────────────────────────────────────────
    render_all() {
        const self = this;
        const d = this.data;
        if (!d) return;

        const isLocked = (d.status === '已结算');
        const $badge = this.$container.find('#settle-status-badge');
        const $btnFinalize = this.$container.find('#btn-finalize-settle');
        const $btnRevert = this.$container.find('#btn-revert-settle');
        const $btnSave = this.$container.find('#btn-save-draft');
        const $btnAddAdj = this.$container.find('#btn-add-adj');

        if (isLocked) {
            $badge.removeClass('status-draft').addClass('status-locked').html('🔒 已核定锁定');
            $btnFinalize.hide();
            $btnRevert.show();
            $btnSave.hide();
            $btnAddAdj.hide();
            this.$container.find('.prop-excel-table, .rate-input, .prop-mgmt-input').addClass('table-locked');
        } else {
            $badge.removeClass('status-locked').addClass('status-draft').html('🟡 草稿录入中');
            $btnFinalize.show();
            $btnRevert.hide();
            $btnSave.show();
            $btnAddAdj.show();
            this.$container.find('.prop-excel-table, .rate-input, .prop-mgmt-input').removeClass('table-locked');
        }

        // 物业公司
        this.$container.find('#inp-prop-mgmt').val(d.property_management_company || '天津金利达物业管理有限公司').prop('disabled', isLocked);

        // 单价
        this.$container.find('#inp-elec-price').val(d.electricity_price || 1.1957).prop('disabled', isLocked);
        this.$container.find('#inp-water-price').val(d.water_price || 5.5).prop('disabled', isLocked);

        // 更新 Excel 导出菜单中的各公司项
        const $compMenu = this.$container.find('#comp-export-items');
        $compMenu.empty();
        (d.company_summaries || []).forEach(s => {
            const shortName = s.company.includes('祺富') ? '祺富单证' : (s.company.includes('吉众') ? '吉众单证' : `${s.company}单证`);
            const $item = $(`<a class="dropdown-item" href="#">📄 导出【${shortName}】Excel</a>`);
            $item.on('click', (e) => {
                e.preventDefault();
                self.$container.find('#menu-export-excel').hide();
                self.download_excel('company', s.company);
            });
            $compMenu.append($item);
        });

        this.render_summary_table();
        this.render_meter_tables();
        this.render_adjustments_table();
        this.render_leases_table();
    }

    // ─── 渲染公司汇总表格 ─────────────────────────────────────
    render_summary_table() {
        const self = this;
        const summaries = this.data?.company_summaries || [];
        const $tbody = this.$container.find('#tbody-comp-summary');
        $tbody.empty();

        if (!summaries.length) {
            $tbody.html('<tr><td colspan="10" class="text-center text-muted" style="padding:16px;">暂无公司数据</td></tr>');
            return;
        }

        let totRent = 0, totProp = 0, totElecU = 0, totElecA = 0, totWaterU = 0, totWaterA = 0, totAdj = 0, totGrand = 0;

        summaries.forEach(s => {
            totRent += s.rent_amount;
            totProp += s.property_fee_amount;
            totElecU += s.electricity_usage;
            totElecA += s.electricity_amount;
            totWaterU += s.water_usage;
            totWaterA += s.water_amount;
            totAdj += s.adjustment_amount;
            totGrand += s.total_amount;

            const row = `
                <tr>
                    <td><b>🏢 ${frappe.utils.escape_html(s.company)}</b></td>
                    <td style="text-align: right;">¥ ${format_currency(s.rent_amount)}</td>
                    <td style="text-align: right;">¥ ${format_currency(s.property_fee_amount)}</td>
                    <td style="text-align: right;">${format_number(s.electricity_usage)}</td>
                    <td style="text-align: right;">¥ ${format_currency(s.electricity_amount)}</td>
                    <td style="text-align: right;">${format_number(s.water_usage)}</td>
                    <td style="text-align: right;">¥ ${format_currency(s.water_amount)}</td>
                    <td style="text-align: right; color: ${s.adjustment_amount < 0 ? '#dc2626' : (s.adjustment_amount > 0 ? '#059669' : '#4b5563')};">
                        ${s.adjustment_amount !== 0 ? (s.adjustment_amount > 0 ? '+' : '') + '¥ ' + format_currency(s.adjustment_amount) : '—'}
                    </td>
                    <td style="text-align: right; font-weight: 700; background: #f0fdf4; color: #166534; font-size: 14px;">
                        ¥ ${format_currency(s.total_amount)}
                    </td>
                    <td style="text-align: center;">
                        <button class="prop-btn-link btn-print-company" data-company="${frappe.utils.escape_html(s.company)}">
                            🖨️ 单证预览
                        </button>
                        <button class="prop-btn-link btn-export-company" data-company="${frappe.utils.escape_html(s.company)}" title="导出Excel" style="margin-left:4px; color:#0284c7;">
                            📥 Excel
                        </button>
                    </td>
                </tr>
            `;
            const $r = $(row);
            $r.find('.btn-print-company').on('click', function(e) {
                e.stopPropagation();
                const comp = $(this).attr('data-company');
                self.open_single_bill_dialog(comp);
            });
            $r.find('.btn-export-company').on('click', function(e) {
                e.stopPropagation();
                const comp = $(this).attr('data-company');
                self.download_excel('company', comp);
            });
            $tbody.append($r);
        });

        // 合计行
        const $rTot = $(`
            <tr class="prop-row-total">
                <td><b>全公司合计</b></td>
                <td style="text-align: right;">¥ ${format_currency(totRent)}</td>
                <td style="text-align: right;">¥ ${format_currency(totProp)}</td>
                <td style="text-align: right;">${format_number(totElecU)}</td>
                <td style="text-align: right;">¥ ${format_currency(totElecA)}</td>
                <td style="text-align: right;">${format_number(totWaterU)}</td>
                <td style="text-align: right;">¥ ${format_currency(totWaterA)}</td>
                <td style="text-align: right;">${totAdj !== 0 ? '¥ ' + format_currency(totAdj) : '—'}</td>
                <td style="text-align: right; font-weight: 800; font-size: 15px; color: #166534;">¥ ${format_currency(totGrand)}</td>
                <td style="text-align: center;">
                    <button class="prop-btn-link" id="btn-print-total">
                        🖨️ 合计单证
                    </button>
                    <button class="prop-btn-link" id="btn-export-total-row" title="导出合计Excel" style="margin-left:4px; color:#0284c7;">
                        📥 Excel
                    </button>
                </td>
            </tr>
        `);
        $rTot.find('#btn-print-total').on('click', () => {
            self.open_single_bill_dialog('total');
        });
        $rTot.find('#btn-export-total-row').on('click', () => {
            self.download_excel('total');
        });
        $tbody.append($rTot);
    }

    // ─── 渲染水电抄表表格 ─────────────────────────────────────
    render_meter_tables() {
        const self = this;
        const readings = this.data?.meter_readings || [];
        const isLocked = (this.data?.status === '已结算');

        const $tbodyE = this.$container.find('#tbody-elec-meters');
        const $tbodyW = this.$container.find('#tbody-water-meters');
        $tbodyE.empty();
        $tbodyW.empty();

        readings.forEach((r, idx) => {
            const isElec = (r.utility_type === '电');
            const $tbody = isElec ? $tbodyE : $tbodyW;

            const row = `
                <tr data-idx="${idx}">
                    <td>${frappe.utils.escape_html(r.company)}</td>
                    <td style="text-align: center;"><b>${frappe.utils.escape_html(r.meter_no)}</b></td>
                    <td>${frappe.utils.escape_html(r.meter_name || r.utility_meter)}</td>
                    <td style="text-align: right;" class="cell-prev">${format_number(r.previous_reading)}</td>
                    <td style="text-align: right;">
                        <input type="number" step="any" class="cell-reading-input" data-idx="${idx}" value="${r.current_reading !== undefined ? r.current_reading : ''}" ${isLocked ? 'disabled' : ''} />
                    </td>
                    <td style="text-align: right;" class="cell-raw">${format_number(r.raw_usage)}</td>
                    <td style="text-align: center;"><span class="mult-badge">×${r.multiplier}</span></td>
                    <td style="text-align: right;" class="cell-calc"><b>${format_number(r.calculated_usage)}</b></td>
                    <td style="text-align: right;" class="cell-amount">¥ ${format_currency(r.amount_tax_incl)}</td>
                    <td>
                        <input type="text" class="cell-remark-input" data-idx="${idx}" value="${frappe.utils.escape_html(r.remark || '')}" placeholder="换表/异常说明" ${isLocked ? 'disabled' : ''} />
                    </td>
                </tr>
            `;
            const $r = $(row);

            $r.find('.cell-reading-input').on('input change', function() {
                const i = parseInt($(this).attr('data-idx'));
                self.data.meter_readings[i].current_reading = parseFloat($(this).val()) || 0;
                self.recalculate();
            });

            $r.find('.cell-remark-input').on('change', function() {
                const i = parseInt($(this).attr('data-idx'));
                self.data.meter_readings[i].remark = $(this).val();
            });

            // Enter 快捷换行
            $r.find('.cell-reading-input').on('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const $nextRow = $r.next('tr');
                    if ($nextRow.length) {
                        $nextRow.find('.cell-reading-input').focus().select();
                    }
                }
            });

            $tbody.append($r);
        });

        if (!$tbodyE.children().length) {
            $tbodyE.html('<tr><td colspan="10" class="text-center text-muted" style="padding:16px;">暂无电表数据</td></tr>');
        }
        if (!$tbodyW.children().length) {
            $tbodyW.html('<tr><td colspan="10" class="text-center text-muted" style="padding:16px;">暂无水表数据</td></tr>');
        }
    }

    // ─── 渲染调整表格 ─────────────────────────────────────────
    render_adjustments_table() {
        const self = this;
        const adjustments = this.data?.adjustments || [];
        const isLocked = (this.data?.status === '已结算');
        const $tbody = this.$container.find('#tbody-adjustments');
        $tbody.empty();

        if (!adjustments.length) {
            $tbody.html('<tr><td colspan="10" class="text-center text-muted" style="padding:16px;">本月暂无特殊调整项</td></tr>');
            return;
        }

        adjustments.forEach((adj, idx) => {
            const isTransfer = (adj.adjustment_scope === '公司间转移');
            const fromDisplay = isTransfer ? frappe.utils.escape_html(adj.from_company || '—') : '—';
            const toDisplay = isTransfer ? frappe.utils.escape_html(adj.to_company || '—') : frappe.utils.escape_html(adj.company || '—');

            const valDisplay = adj.adjustment_type === '按用量'
                ? `${adj.usage_adjustment} (度/m³)`
                : `¥ ${format_currency(adj.amount_adjustment)}`;

            const row = `
                <tr>
                    <td><span class="prop-tag tag-type">${adj.adjustment_type}</span></td>
                    <td><b>${adj.utility_type}</b></td>
                    <td>${adj.adjustment_scope}</td>
                    <td><span class="company-out">${fromDisplay}</span></td>
                    <td><span class="company-in">${toDisplay}</span></td>
                    <td style="text-align: right;"><b>${valDisplay}</b></td>
                    <td style="text-align: right;">${adj.equivalent_usage ? format_number(adj.equivalent_usage) : '—'}</td>
                    <td style="text-align: right; font-weight: 700; color: #b45309;">¥ ${format_currency(adj.amount_adjustment)}</td>
                    <td>${frappe.utils.escape_html(adj.reason || '—')}</td>
                    <td style="text-align: center;">
                        ${!isLocked ? `<button class="prop-btn-del-adj" data-idx="${idx}" title="删除调整">🗑️</button>` : ''}
                    </td>
                </tr>
            `;
            const $r = $(row);
            $r.find('.prop-btn-del-adj').on('click', function() {
                const i = parseInt($(this).attr('data-idx'));
                self.data.adjustments.splice(i, 1);
                self.recalculate();
            });
            $tbody.append($r);
        });
    }

    // ─── 渲染租赁固定费用表格 (多周期平米单价与物业费明细) ───────────
    render_leases_table() {
        const leases = this.data?.lease_charges || [];
        const $tbody = this.$container.find('#tbody-leases');
        $tbody.empty();

        if (!leases.length) {
            $tbody.html('<tr><td colspan="10" class="text-center text-muted" style="padding:16px;">暂无租赁物业配置</td></tr>');
            return;
        }

        leases.forEach(l => {
            const propFeeBadge = (l.property_fee_mode === '单独计收物业费')
                ? `<span class="prop-tag tag-prop-sep">单独计收</span> <span style="font-size:11.5px; color:#475569;">${frappe.utils.escape_html(l.property_fee_rate_snapshot || '')}</span>`
                : `<span class="prop-tag tag-prop-inc">房租已含</span>`;

            const row = `
                <tr>
                    <td><b>${frappe.utils.escape_html(l.company)}</b></td>
                    <td>${frappe.utils.escape_html(l.property_name)}</td>
                    <td style="text-align: right;">${format_number(l.area)} ㎡</td>
                    <td>
                        <span style="font-weight:600; color:#1e293b;">${frappe.utils.escape_html(l.rent_rate_snapshot || '—')}</span>
                    </td>
                    <td>${propFeeBadge}</td>
                    <td style="text-align: center;">${l.billing_days} 天</td>
                    <td style="text-align: right;">¥ ${format_currency(l.rent_amount_tax_incl)}</td>
                    <td style="text-align: right; color: ${l.property_fee_amount_tax_incl > 0 ? '#b45309' : '#94a3b8'};">
                        ${l.property_fee_amount_tax_incl > 0 ? '¥ ' + format_currency(l.property_fee_amount_tax_incl) : '—'}
                    </td>
                    <td style="text-align: right; font-weight: 700; background: #f0fdf4; color: #166534;">¥ ${format_currency(l.amount_tax_incl)}</td>
                    <td style="text-align: right; color:#64748b;">¥ ${format_currency(l.tax_amount)}</td>
                </tr>
            `;
            $tbody.append(row);
        });
    }

    // ─── 客户端即时联动重算 ───────────────────────────────────
    recalculate() {
        if (!this.data) return;

        this.data.electricity_price = parseFloat(this.$container.find('#inp-elec-price').val()) || 1.1957;
        this.data.water_price = parseFloat(this.$container.find('#inp-water-price').val()) || 5.5;
        this.data.property_management_company = this.$container.find('#inp-prop-mgmt').val() || '天津金利达物业管理有限公司';

        calculate_local_matrix(this.data);
        this.render_summary_table();
        this.render_meter_tables_dynamic_updates();
        this.render_adjustments_table();
        this.render_leases_table();
    }

    render_meter_tables_dynamic_updates() {
        const self = this;
        const readings = this.data?.meter_readings || [];
        readings.forEach((r, idx) => {
            const $r = self.$container.find(`tr[data-idx="${idx}"]`);
            if ($r.length) {
                $r.find('.cell-raw').text(format_number(r.raw_usage));
                $r.find('.cell-calc b').text(format_number(r.calculated_usage));
                $r.find('.cell-amount').text(`¥ ${format_currency(r.amount_tax_incl)}`);
            }
        });
    }

    // ─── 保存草稿 ─────────────────────────────────────────────
    save_draft() {
        const self = this;
        self.data.property_management_company = self.$container.find('#inp-prop-mgmt').val() || '天津金利达物业管理有限公司';
        frappe.call({
            method: 'ashan_cn_procurement.ashan_cn_procurement.page.property_settlement_workbench.property_settlement_workbench.save_settlement',
            args: {
                data: JSON.stringify(self.data)
            },
            callback(r) {
                if (r.message?.success) {
                    frappe.show_alert({ message: '草稿已成功保存！', indicator: 'green' }, 3);
                    self.data = r.message.data;
                    self.render_all();
                }
            }
        });
    }

    // ─── 导出 Excel (采用原生链接触发，防弹窗拦截) ───────────
    download_excel(mode, company) {
        const self = this;
        const month = self.data?.settlement_month || `${self.currentYear}-${self.currentMonth < 10 ? '0' + self.currentMonth : self.currentMonth}-01`;
        const propMgmt = self.$container.find('#inp-prop-mgmt').val() || self.data?.property_management_company || '天津金利达物业管理有限公司';

        let url = `/api/method/ashan_cn_procurement.services.property_settlement.export_settlement_excel?settlement_month=${encodeURIComponent(month)}&mode=${encodeURIComponent(mode)}&property_management_company=${encodeURIComponent(propMgmt)}`;
        if (company) {
            url += `&company=${encodeURIComponent(company)}`;
        }

        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // ─── 弹窗 1: 添加费用调整 ─────────────────────────────────
    open_add_adjustment_dialog() {
        const self = this;
        const companies = (self.data?.company_summaries || []).map(s => s.company);
        const compOptions = companies.join('\n');

        const dlg = new frappe.ui.Dialog({
            title: '➕ 添加费用调整 (按用量/按金额)',
            fields: [
                {
                    fieldname: 'adjustment_type',
                    fieldtype: 'Select',
                    label: '调整方式',
                    options: '按金额\n按用量',
                    default: '按金额',
                    reqd: 1,
                    onchange() {
                        const type = dlg.get_value('adjustment_type');
                        dlg.toggle_reqd('amount_adjustment', type === '按金额');
                        dlg.toggle_reqd('usage_adjustment', type === '按用量');
                        dlg.toggle_display('amount_adjustment', type === '按金额');
                        dlg.toggle_display('usage_adjustment', type === '按用量');
                    }
                },
                {
                    fieldname: 'utility_type',
                    fieldtype: 'Select',
                    label: '费用类型',
                    options: '电费\n水费\n房租\n物业费\n其他',
                    default: '电费',
                    reqd: 1
                },
                {
                    fieldname: 'adjustment_scope',
                    fieldtype: 'Select',
                    label: '调整范围',
                    options: '公司间转移\n单公司',
                    default: '公司间转移',
                    reqd: 1,
                    onchange() {
                        const scope = dlg.get_value('adjustment_scope');
                        dlg.toggle_display('from_company', scope === '公司间转移');
                        dlg.toggle_display('to_company', scope === '公司间转移');
                        dlg.toggle_display('company', scope === '单公司');
                    }
                },
                {
                    fieldtype: 'Section Break',
                    label: '调整对象与数值'
                },
                {
                    fieldname: 'from_company',
                    fieldtype: 'Select',
                    label: '转出/扣减公司 (费用减少)',
                    options: compOptions,
                    default: companies[0] || ''
                },
                {
                    fieldname: 'to_company',
                    fieldtype: 'Select',
                    label: '转入/承担公司 (费用增加)',
                    options: compOptions,
                    default: companies[1] || companies[0] || ''
                },
                {
                    fieldname: 'company',
                    fieldtype: 'Select',
                    label: '调整归属公司',
                    options: compOptions,
                    hidden: 1
                },
                {
                    fieldname: 'amount_adjustment',
                    fieldtype: 'Currency',
                    label: '调整金额 (元)',
                    description: '正数表示转出方减少该金额，转入方增加该金额'
                },
                {
                    fieldname: 'usage_adjustment',
                    fieldtype: 'Float',
                    label: '调整用量 (kWh / m³)',
                    hidden: 1,
                    description: '将按当月单价自动折算为调整金额'
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldname: 'reason',
                    fieldtype: 'Small Text',
                    label: '调整原因说明',
                    placeholder: '如：公司间电费分摊调整、4号电表修约补偿等'
                }
            ],
            primary_action_label: '确认添加',
            primary_action(values) {
                if (values.adjustment_scope === '公司间转移') {
                    if (!values.from_company || !values.to_company) {
                        frappe.msgprint('请选择转出公司与转入公司！');
                        return;
                    }
                    if (values.from_company === values.to_company) {
                        frappe.msgprint('转出公司与转入公司不能相同！');
                        return;
                    }
                }

                self.data.adjustments = self.data.adjustments || [];
                self.data.adjustments.push({
                    adjustment_type: values.adjustment_type,
                    utility_type: values.utility_type,
                    adjustment_scope: values.adjustment_scope,
                    from_company: values.from_company,
                    to_company: values.to_company,
                    company: values.company,
                    amount_adjustment: parseFloat(values.amount_adjustment) || 0,
                    usage_adjustment: parseFloat(values.usage_adjustment) || 0,
                    reason: values.reason || '电费调整'
                });

                dlg.hide();
                self.recalculate();
            }
        });
        dlg.show();
    }

    // ─── 弹窗 2: 完成月结确认 ─────────────────────────────────
    open_finalize_confirm_dialog() {
        const self = this;
        const summaries = this.data?.company_summaries || [];

        let summaryRows = '';
        summaries.forEach(s => {
            summaryRows += `
                <div class="confirm-comp-card">
                    <div class="comp-title">🏢 ${frappe.utils.escape_html(s.company)}</div>
                    <div class="comp-details">
                        <div>房租金额: <b>¥ ${format_currency(s.rent_amount)}</b></div>
                        <div>物业费: <b>¥ ${format_currency(s.property_fee_amount)}</b></div>
                        <div>水电费用: <b>¥ ${format_currency(s.electricity_amount + s.water_amount)}</b></div>
                        <div>费用调整: <b>¥ ${format_currency(s.adjustment_amount)}</b></div>
                        <div class="comp-subtotal">应付合计: <span>¥ ${format_currency(s.total_amount)}</span></div>
                    </div>
                </div>
            `;
        });

        const monthStr = `${self.currentYear}年${self.currentMonth < 10 ? '0' + self.currentMonth : self.currentMonth}月`;

        const dlg = new frappe.ui.Dialog({
            title: `🔒 核定并锁定 ${monthStr} 物业月结`,
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'confirm_html',
                    options: `
                        <div class="confirm-box">
                            <div class="alert alert-warning" style="font-size:13px; margin-bottom:14px;">
                                ⚠️ 完成月结后将锁定当月抄表、单价与调整数据，并固化历史快照！请核对以下各公司结算金额：
                            </div>
                            <div class="confirm-cards-container">
                                ${summaryRows}
                            </div>
                            <div class="confirm-grand-total">
                                全公司本月应付总额: <b>¥ ${format_currency(self.data.total_amount)}</b>
                            </div>
                        </div>
                    `
                }
            ],
            primary_action_label: '确认完成本月结算',
            primary_action() {
                self.data.property_management_company = self.$container.find('#inp-prop-mgmt').val() || '天津金利达物业管理有限公司';
                frappe.call({
                    method: 'ashan_cn_procurement.ashan_cn_procurement.page.property_settlement_workbench.property_settlement_workbench.finalize_settlement',
                    args: {
                        data: JSON.stringify(self.data)
                    },
                    callback(r) {
                        if (r.message?.success) {
                            frappe.show_alert({ message: r.message.message, indicator: 'green' }, 4);
                            dlg.hide();
                            self.data = r.message.data;
                            self.render_all();
                        }
                    }
                });
            }
        });
        dlg.show();
    }

    // ─── 取消月结 ─────────────────────────────────────────────
    revert_settlement() {
        const self = this;
        frappe.confirm(`确定要取消 ${self.currentYear}年${self.currentMonth}月的月结锁定并恢复为草稿状态吗？`, () => {
            frappe.call({
                method: 'ashan_cn_procurement.ashan_cn_procurement.page.property_settlement_workbench.property_settlement_workbench.revert_settlement',
                args: {
                    name: self.data.name
                },
                callback(r) {
                    if (r.message?.success) {
                        frappe.show_alert({ message: r.message.message, indicator: 'green' }, 3);
                        self.data = r.message.data;
                        self.render_all();
                    }
                }
            });
        });
    }

    // ─── 弹窗 3: 单一公司 / 全公司合计单证预览与打印 ─────────
    open_single_bill_dialog(company) {
        const self = this;
        const d = self.data;
        if (!d) return;

        const isTotal = (company === 'total' || company === '全公司合计');
        const compTitle = isTotal ? '全公司合计' : company;
        const propMgmt = self.$container.find('#inp-prop-mgmt').val() || d.property_management_company || '天津金利达物业管理有限公司';

        let compMeters = [], compLeases = [], compSummary = {}, compAdjustments = [];

        if (isTotal) {
            compMeters = d.meter_readings || [];
            compLeases = d.lease_charges || [];
            let totRent = 0, totProp = 0, totGrand = 0;
            (d.company_summaries || []).forEach(s => {
                totRent += s.rent_amount;
                totProp += s.property_fee_amount;
                totGrand += s.total_amount;
            });
            compSummary = {
                company: '全公司合计',
                rent_amount: totRent,
                property_fee_amount: totProp,
                total_amount: totGrand
            };
            (d.adjustments || []).forEach(a => {
                if (a.adjustment_scope === '单公司') {
                    compAdjustments.push({
                        title: a.utility_type.includes('电') ? '电费调整' : '水费调整',
                        type: a.adjustment_type,
                        scope: '单公司调整',
                        usage: a.equivalent_usage,
                        amount: a.amount_adjustment,
                        reason: a.reason
                    });
                }
            });
        } else {
            compMeters = (d.meter_readings || []).filter(m => m.company === company);
            compLeases = (d.lease_charges || []).filter(l => l.company === company);
            compSummary = (d.company_summaries || []).find(s => s.company === company) || {};

            (d.adjustments || []).forEach(a => {
                const adjTitle = a.utility_type.includes('电') ? '电费调整' : '水费调整';
                if (a.adjustment_scope === '单公司' && a.company === company) {
                    compAdjustments.push({
                        title: adjTitle,
                        type: a.adjustment_type,
                        scope: '单公司调整',
                        usage: a.equivalent_usage,
                        amount: a.amount_adjustment,
                        reason: a.reason
                    });
                } else if (a.adjustment_scope === '公司间转移') {
                    if (a.from_company === company) {
                        compAdjustments.push({
                            title: adjTitle,
                            type: `${a.adjustment_type} (公司间转出)`,
                            scope: '公司间转移',
                            usage: -a.equivalent_usage,
                            amount: -a.amount_adjustment,
                            reason: a.reason
                        });
                    } else if (a.to_company === company) {
                        compAdjustments.push({
                            title: adjTitle,
                            type: `${a.adjustment_type} (公司间转入)`,
                            scope: '公司间转移',
                            usage: a.equivalent_usage,
                            amount: a.amount_adjustment,
                            reason: a.reason
                        });
                    }
                }
            });
        }

        const bill = {
            settlement_month: d.settlement_month,
            company: compTitle,
            is_total: isTotal,
            property_management_company: propMgmt,
            status: d.status || '草稿',
            electricity_price: d.electricity_price,
            water_price: d.water_price,
            meters: compMeters,
            leases: compLeases,
            adjustments: compAdjustments,
            summary: compSummary
        };

        self.show_bill_modal(bill);
    }

    // ─── 弹窗 4: 预览全部结算单 ───────────────────────────────
    open_bills_preview_dialog() {
        const summaries = this.data?.company_summaries || [];
        if (!summaries.length) {
            frappe.msgprint('暂无可导出的公司结算数据！');
            return;
        }
        this.open_single_bill_dialog(summaries[0].company);
    }

    show_bill_modal(bill) {
        const self = this;
        const monthStr = bill.settlement_month.substring(0, 7);

        // 1. 电费明细表格行
        let meterRows = '';
        let sumElecRaw = 0, sumElecCalc = 0, sumElecAmt = 0;
        (bill.meters || []).filter(m => m.utility_type === '电').forEach(m => {
            sumElecRaw += (m.raw_usage || 0);
            sumElecCalc += (m.calculated_usage || 0);
            sumElecAmt += (m.amount_tax_incl || 0);
            meterRows += `
                <tr>
                    <td>${m.meter_no}</td>
                    <td>${format_number(m.previous_reading)}</td>
                    <td>${format_number(m.current_reading)}</td>
                    <td>${format_number(m.raw_usage)}</td>
                    <td>${m.multiplier}</td>
                    <td>${format_number(m.calculated_usage)}</td>
                    <td>${Number(m.unit_price).toFixed(4)}</td>
                    <td>${format_number(Math.round(m.amount_tax_incl || 0))}</td>
                </tr>
            `;
        });

        // 电费调整行 (标题统一展示为「电费调整」)
        (bill.adjustments || []).filter(a => a.title.includes('电') || a.type.includes('电')).forEach(a => {
            const u = a.usage || 0;
            const amt = a.amount || 0;
            sumElecRaw += u;
            sumElecCalc += u;
            sumElecAmt += amt;
            meterRows += `
                <tr>
                    <td><b>电费调整</b></td>
                    <td>—</td>
                    <td>—</td>
                    <td>${format_number(u)}</td>
                    <td>1</td>
                    <td>${format_number(u)}</td>
                    <td>—</td>
                    <td>${format_number(Math.round(amt))}</td>
                </tr>
            `;
        });

        // 2. 水费明细表格行
        let waterRows = '';
        let sumWaterRaw = 0, sumWaterCalc = 0, sumWaterAmt = 0;
        (bill.meters || []).filter(m => m.utility_type === '水').forEach(m => {
            sumWaterRaw += (m.raw_usage || 0);
            sumWaterCalc += (m.calculated_usage || 0);
            sumWaterAmt += (m.amount_tax_incl || 0);
            waterRows += `
                <tr>
                    <td>${m.meter_no}</td>
                    <td>${format_number(m.previous_reading)}</td>
                    <td>${format_number(m.current_reading)}</td>
                    <td>${format_number(m.raw_usage)}</td>
                    <td>${m.multiplier}</td>
                    <td>${format_number(m.calculated_usage)}</td>
                    <td>${Number(m.unit_price).toFixed(4)}</td>
                    <td>${format_number(Math.round(m.amount_tax_incl || 0))}</td>
                </tr>
            `;
        });

        (bill.adjustments || []).filter(a => a.title.includes('水') || a.type.includes('水')).forEach(a => {
            const u = a.usage || 0;
            const amt = a.amount || 0;
            sumWaterRaw += u;
            sumWaterCalc += u;
            sumWaterAmt += amt;
            waterRows += `
                <tr>
                    <td><b>水费调整</b></td>
                    <td>—</td>
                    <td>—</td>
                    <td>${format_number(u)}</td>
                    <td>1</td>
                    <td>${format_number(u)}</td>
                    <td>—</td>
                    <td>${format_number(Math.round(amt))}</td>
                </tr>
            `;
        });

        // 3. 房租与物业费表格行
        let leaseRows = '';
        let sumArea = 0, sumRentAmt = 0, sumPropAmt = 0, sumLeaseTot = 0;
        (bill.leases || []).forEach(l => {
            sumArea += (l.area || 0);
            sumRentAmt += (l.rent_amount_tax_incl || 0);
            sumPropAmt += (l.property_fee_amount_tax_incl || 0);
            sumLeaseTot += (l.amount_tax_incl || 0);

            const propFeeText = (l.property_fee_mode === '单独计收物业费')
                ? `¥ ${format_currency(l.property_fee_amount_tax_incl)} (${l.property_fee_rate_snapshot || ''})`
                : '已包含在房租中';

            leaseRows += `
                <tr>
                    <td>${frappe.utils.escape_html(l.property_name)}</td>
                    <td>${format_number(l.area)} ㎡</td>
                    <td>${l.billing_days} 天</td>
                    <td>${frappe.utils.escape_html(l.rent_rate_snapshot || '—')}</td>
                    <td>${propFeeText}</td>
                    <td>¥ ${format_currency(l.rent_amount_tax_incl)}</td>
                    <td>${l.property_fee_amount_tax_incl > 0 ? '¥ ' + format_currency(l.property_fee_amount_tax_incl) : '—'}</td>
                    <td style="font-weight:bold;">¥ ${format_currency(l.amount_tax_incl)}</td>
                </tr>
            `;
        });

        // 4. 税务与综合汇总行
        const elecRoundTot = Math.round(sumElecAmt);
        const elecExcl = Math.round((elecRoundTot / 1.13) * 100) / 100;
        const elecTax = Math.round((elecRoundTot - elecExcl) * 100) / 100;
        const elecAvg = sumElecCalc > 0 ? (elecRoundTot / sumElecCalc).toFixed(2) : '0.00';

        const waterRoundTot = Math.round(sumWaterAmt);
        const waterExcl = Math.round((waterRoundTot / 1.09) * 100) / 100;
        const waterTax = Math.round((waterRoundTot - waterExcl) * 100) / 100;
        const waterAvg = sumWaterCalc > 0 ? (waterRoundTot / sumWaterCalc).toFixed(2) : '0.00';

        const rentRoundTot = Math.round(sumRentAmt);
        const rentExcl = Math.round((rentRoundTot / 1.09) * 100) / 100;
        const rentTax = Math.round((rentRoundTot - rentExcl) * 100) / 100;

        const propRoundTot = Math.round(sumPropAmt);
        const propExcl = Math.round((propRoundTot / 1.09) * 100) / 100;
        const propTax = Math.round((propRoundTot - propExcl) * 100) / 100;

        const grandRoundTot = elecRoundTot + waterRoundTot + rentRoundTot + propRoundTot;

        // 快捷公司切换 Tab
        const allCompanies = (self.data?.company_summaries || []).map(s => s.company);
        let tabButtons = '';
        allCompanies.forEach(c => {
            const shortName = c.includes('祺富') ? '祺富单证' : (c.includes('吉众') ? '吉众单证' : c);
            const activeClass = (c === bill.company) ? 'btn-primary' : 'btn-default';
            tabButtons += `<button class="btn btn-xs ${activeClass} tab-switch-comp" data-comp="${frappe.utils.escape_html(c)}" style="margin-right:6px; font-weight:600;">${shortName}</button>`;
        });
        const totActive = bill.is_total ? 'btn-primary' : 'btn-default';
        tabButtons += `<button class="btn btn-xs ${totActive} tab-switch-comp" data-comp="total" style="font-weight:600;">合计单证</button>`;

        const shortComp = bill.is_total ? '全公司合计' : (bill.company.includes('祺富') ? '祺富' : (bill.company.includes('吉众') ? '吉众' : bill.company));

        const dlg = new frappe.ui.Dialog({
            title: `📄 ${bill.company} — ${monthStr} 物业明细（单价含税）`,
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'bill_html',
                    options: `
                        <div style="margin-bottom:12px; display:flex; align-items:center; justify-content:space-between;">
                            <div><b>单证切换:</b> ${tabButtons}</div>
                            <button class="btn btn-xs btn-default" id="btn-export-current-excel" style="color:#0284c7; font-weight:600;">📥 导出当前单证 Excel</button>
                        </div>

                        <div class="print-bill-container" id="printable-company-bill">
                            <div class="bill-header">
                                <h3 class="bill-title">${frappe.utils.escape_html(bill.company)}</h3>
                                <div class="bill-subtitle">物业明细（单价含税）</div>
                                <div class="bill-meta-row">
                                    <span>上期日期: <b>${monthStr}-01</b></span>
                                    <span>本期日期: <b>${monthStr}-01</b></span>
                                    <span>核定日期: <b>${monthStr}-01</b></span>
                                    <span>物业公司: <b>${frappe.utils.escape_html(bill.property_management_company || '')}</b></span>
                                </div>
                            </div>

                            <!-- 1. 电费 -->
                            <div class="bill-sec-title">电费</div>
                            <table class="bill-table-1to1">
                                <thead>
                                    <tr>
                                        <th style="width:18%;">表号</th>
                                        <th style="width:14%;">上期表数</th>
                                        <th style="width:14%;">本期表数</th>
                                        <th style="width:14%;">本期用电</th>
                                        <th style="width:10%;">倍率</th>
                                        <th style="width:14%;">核定度数</th>
                                        <th style="width:12%;">单价</th>
                                        <th style="width:18%;">总价</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${meterRows || '<tr><td colspan="8">无电费记录</td></tr>'}
                                    <tr class="total-row">
                                        <td>合计</td>
                                        <td></td><td></td>
                                        <td>${format_number(sumElecRaw)}</td>
                                        <td></td>
                                        <td>${format_number(sumElecCalc)}</td>
                                        <td></td>
                                        <td>${format_number(Math.round(sumElecAmt))}</td>
                                    </tr>
                                </tbody>
                            </table>

                            <!-- 2. 水费 -->
                            <div class="bill-sec-title">水费</div>
                            <table class="bill-table-1to1">
                                <thead>
                                    <tr>
                                        <th style="width:18%;">表号</th>
                                        <th style="width:14%;">上期表数</th>
                                        <th style="width:14%;">本期表数</th>
                                        <th style="width:14%;">本期用水</th>
                                        <th style="width:10%;">倍率</th>
                                        <th style="width:14%;">核定m³</th>
                                        <th style="width:12%;">单价</th>
                                        <th style="width:18%;">总价</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${waterRows || '<tr><td colspan="8">无水费记录</td></tr>'}
                                    <tr class="total-row">
                                        <td>合计</td>
                                        <td></td><td></td>
                                        <td>${format_number(sumWaterRaw)}</td>
                                        <td></td>
                                        <td>${format_number(sumWaterCalc)}</td>
                                        <td></td>
                                        <td>${format_number(Math.round(sumWaterAmt))}</td>
                                    </tr>
                                </tbody>
                            </table>

                            <!-- 3. 房租与物业费 (若有) -->
                            ${bill.leases?.length ? `
                            <div class="bill-sec-title">房租与物业费</div>
                            <table class="bill-table-1to1">
                                <thead>
                                    <tr>
                                        <th style="width:18%;">场地名称</th>
                                        <th style="width:14%;">面积(㎡)</th>
                                        <th style="width:10%;">计费天数</th>
                                        <th style="width:14%;">房租单价</th>
                                        <th style="width:14%;">物业费计收</th>
                                        <th style="width:12%;">房租金额</th>
                                        <th style="width:12%;">物业费金额</th>
                                        <th style="width:18%;">含税合计</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${leaseRows}
                                    <tr class="total-row">
                                        <td>合计</td>
                                        <td>${format_number(sumArea)} ㎡</td>
                                        <td></td><td></td><td></td>
                                        <td>¥ ${format_currency(sumRentAmt)}</td>
                                        <td>¥ ${format_currency(sumPropAmt)}</td>
                                        <td>¥ ${format_currency(sumLeaseTot)}</td>
                                    </tr>
                                </tbody>
                            </table>
                            ` : ''}

                            <!-- 4. 水电与物业综合汇总 (1:1 原版格式，大字合计居右) -->
                            <div class="bill-sec-title">${shortComp}合计水电费</div>
                            <table class="bill-table-1to1">
                                <thead>
                                    <tr>
                                        <th style="width:18%;">项目</th>
                                        <th style="width:14%;">金额</th>
                                        <th style="width:8%;">税率</th>
                                        <th style="width:12%;">税额</th>
                                        <th style="width:14%;">合计</th>
                                        <th style="width:12%;">数量</th>
                                        <th style="width:10%;">单位</th>
                                        <th style="width:18%;">水电费合计</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>电费</td>
                                        <td>${format_currency(elecExcl)}</td>
                                        <td>13%</td>
                                        <td>${format_currency(elecTax)}</td>
                                        <td>${format_number(elecRoundTot)}</td>
                                        <td>${format_number(sumElecCalc)}</td>
                                        <td>${elecAvg}</td>
                                        <td rowspan="${bill.leases?.length ? '4' : '2'}" class="grand-total-large-cell">
                                            ${format_number(grandRoundTot)}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>水费</td>
                                        <td>${format_currency(waterExcl)}</td>
                                        <td>9%</td>
                                        <td>${format_currency(waterTax)}</td>
                                        <td>${format_number(waterRoundTot)}</td>
                                        <td>${format_number(sumWaterCalc)}</td>
                                        <td>${waterAvg}</td>
                                    </tr>
                                    ${bill.leases?.length ? `
                                    <tr>
                                        <td>房租</td>
                                        <td>${format_currency(rentExcl)}</td>
                                        <td>9%</td>
                                        <td>${format_currency(rentTax)}</td>
                                        <td>${format_number(rentRoundTot)}</td>
                                        <td>${format_number(sumArea)}</td>
                                        <td>—</td>
                                    </tr>
                                    <tr>
                                        <td>物业费</td>
                                        <td>${format_currency(propExcl)}</td>
                                        <td>9%</td>
                                        <td>${format_currency(propTax)}</td>
                                        <td>${format_number(propRoundTot)}</td>
                                        <td>${format_number(sumArea)}</td>
                                        <td>—</td>
                                    </tr>
                                    ` : ''}
                                </tbody>
                            </table>
                        </div>
                    `
                }
            ],
            primary_action_label: '🖨️ 打印当前单证',
            primary_action() {
                const printContents = document.getElementById('printable-company-bill').innerHTML;
                const win = window.open('', '', 'height=750,width=950');
                win.document.write(`
                    <html>
                    <head>
                        <title>${bill.company} - ${monthStr} 物业明细（单价含税）</title>
                        <style>
                            body { font-family: "等线", "Microsoft YaHei", sans-serif; padding: 24px; color: #000; }
                            .bill-header { text-align: center; margin-bottom: 12px; }
                            .bill-title { margin: 0 0 4px 0; font-size: 20px; font-weight: bold; }
                            .bill-subtitle { font-size: 13px; margin-bottom: 6px; }
                            .bill-meta-row { display: flex; justify-content: space-between; border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 4px 0; font-size: 11.5px; }
                            .bill-sec-title { text-align: center; font-size: 12px; font-weight: bold; padding: 4px; border: 1.5px solid #000; border-bottom: 1px solid #000; margin-top: 10px; }
                            .bill-table-1to1 { width: 100%; border-collapse: collapse; font-size: 11.5px; margin-bottom: 6px; }
                            .bill-table-1to1 th { border: 1px solid #000; border-left: 1.5px solid #000; border-right: 1.5px solid #000; padding: 4px 6px; text-align: center; font-weight: bold; }
                            .bill-table-1to1 td { border: 1px solid #000; padding: 4px 6px; text-align: center; height: 26px; }
                            .bill-table-1to1 tr td:first-child { border-left: 1.5px solid #000; }
                            .bill-table-1to1 tr td:last-child { border-right: 1.5px solid #000; }
                            .bill-table-1to1 tr.total-row td { font-weight: bold; border-bottom: 1.5px solid #000; }
                            .grand-total-large-cell { font-size: 22px; font-weight: normal; vertical-align: middle; border: 1.5px solid #000 !important; }
                        </style>
                    </head>
                    <body>
                        ${printContents}
                    </body>
                    </html>
                `);
                win.document.close();
                win.focus();
                setTimeout(() => { win.print(); }, 500);
            }
        });

        // 绑定单证切换 Tab 事件
        dlg.$wrapper.find('.tab-switch-comp').on('click', function() {
            const comp = $(this).attr('data-comp');
            dlg.hide();
            self.open_single_bill_dialog(comp);
        });

        // 绑定导出当前单证 Excel
        dlg.$wrapper.find('#btn-export-current-excel').on('click', function() {
            if (bill.is_total) {
                self.download_excel('total');
            } else {
                self.download_excel('company', bill.company);
            }
        });

        dlg.show();
    }
}


// ─── 辅助函数 ─────────────────────────────────────────────────
function format_currency(v) {
    if (v === undefined || v === null || isNaN(v)) return '0.00';
    return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function format_number(v) {
    if (v === undefined || v === null || isNaN(v)) return '0';
    return Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function calculate_local_matrix(data) {
    const elec_price = parseFloat(data.electricity_price) || 1.1957;
    const water_price = parseFloat(data.water_price) || 5.5;

    // 1. 抄表
    (data.meter_readings || []).forEach(r => {
        const prev = parseFloat(r.previous_reading) || 0;
        const curr = parseFloat(r.current_reading) || 0;
        const mult = parseFloat(r.multiplier) || 1.0;
        const raw = Math.max(0, curr - prev);
        const calc_u = Math.round(raw * mult * 100) / 100;
        const price = (r.utility_type === '电') ? elec_price : water_price;
        const amt = Math.round(calc_u * price * 100) / 100;

        r.raw_usage = raw;
        r.calculated_usage = calc_u;
        r.unit_price = price;
        r.amount_tax_incl = amt;
    });

    // 2. 调整 (文字统一显示为「电费调整」或「水费调整」)
    (data.adjustments || []).forEach(a => {
        const u_type = a.utility_type;
        const price = (u_type === '电费') ? elec_price : ((u_type === '水费') ? water_price : 1.0);
        if (a.adjustment_type === '按用量') {
            a.amount_adjustment = Math.round((parseFloat(a.usage_adjustment) || 0) * price * 100) / 100;
            a.equivalent_usage = parseFloat(a.usage_adjustment) || 0;
        } else {
            a.equivalent_usage = price > 0 ? Math.round(((parseFloat(a.amount_adjustment) || 0) / price) * 100) / 100 : 0;
        }
    });

    // 3. 租赁明细与公司汇总
    const compMap = {};
    (data.company_summaries || []).forEach(s => {
        compMap[s.company] = {
            company: s.company,
            rent_amount: 0,
            property_fee_amount: 0,
            electricity_usage: 0,
            electricity_amount: 0,
            water_usage: 0,
            water_amount: 0,
            adjustment_amount: 0,
            total_amount: 0
        };
    });

    let days_in_month = 30;
    if (data.settlement_month) {
        const parts = String(data.settlement_month).split('-');
        if (parts.length >= 2) {
            const yr = parseInt(parts[0]);
            const mo = parseInt(parts[1]);
            days_in_month = new Date(yr, mo, 0).getDate();
        }
    }

    (data.lease_charges || []).forEach(l => {
        const area = parseFloat(l.area) || 0;
        const l_days = parseInt(l.billing_days) || days_in_month;

        let rent_amt = parseFloat(l.rent_amount_tax_incl) || 0;
        if (l.rent_annual_amount > 0) {
            rent_amt = Math.round((parseFloat(l.rent_annual_amount) / 365 * l_days) * 100) / 100;
        } else if (l.rent_daily_rate > 0 && area > 0) {
            rent_amt = Math.round((area * parseFloat(l.rent_daily_rate) * l_days) * 100) / 100;
        } else if (l.rent_monthly_amount > 0) {
            rent_amt = Math.round((parseFloat(l.rent_monthly_amount) * (l_days / days_in_month)) * 100) / 100;
        }

        let prop_amt = 0;
        if (l.property_fee_mode === '单独计收物业费') {
            if (l.property_fee_annual_amount > 0) {
                prop_amt = Math.round((parseFloat(l.property_fee_annual_amount) / 365 * l_days) * 100) / 100;
            } else if (l.property_fee_daily_rate > 0 && area > 0) {
                prop_amt = Math.round((area * parseFloat(l.property_fee_daily_rate) * l_days) * 100) / 100;
            } else if (l.property_fee_monthly_amount > 0) {
                prop_amt = Math.round((parseFloat(l.property_fee_monthly_amount) * (l_days / days_in_month)) * 100) / 100;
            } else {
                prop_amt = parseFloat(l.property_fee_amount_tax_incl) || 0;
            }
        }

        l.rent_amount_tax_incl = rent_amt;
        l.property_fee_amount_tax_incl = prop_amt;
        l.amount_tax_incl = Math.round((rent_amt + prop_amt) * 100) / 100;

        if (compMap[l.company]) {
            compMap[l.company].rent_amount += rent_amt;
            compMap[l.company].property_fee_amount += prop_amt;
        }
    });

    (data.meter_readings || []).forEach(m => {
        if (compMap[m.company]) {
            const u = parseFloat(m.calculated_usage) || 0;
            const amt = parseFloat(m.amount_tax_incl) || 0;
            if (m.utility_type === '电') {
                compMap[m.company].electricity_usage += u;
                compMap[m.company].electricity_amount += amt;
            } else {
                compMap[m.company].water_usage += u;
                compMap[m.company].water_amount += amt;
            }
        }
    });

    (data.adjustments || []).forEach(a => {
        const amt = parseFloat(a.amount_adjustment) || 0;
        const eq_u = parseFloat(a.equivalent_usage) || 0;
        const u_type = a.utility_type;

        if (a.adjustment_scope === '单公司' && compMap[a.company]) {
            compMap[a.company].adjustment_amount += amt;
            if (u_type === '电费') {
                compMap[a.company].electricity_usage += eq_u;
                compMap[a.company].electricity_amount += amt;
            } else if (u_type === '水费') {
                compMap[a.company].water_usage += eq_u;
                compMap[a.company].water_amount += amt;
            }
        } else if (a.adjustment_scope === '公司间转移') {
            if (compMap[a.from_company]) {
                compMap[a.from_company].adjustment_amount -= amt;
                if (u_type === '电费') {
                    compMap[a.from_company].electricity_usage -= eq_u;
                    compMap[a.from_company].electricity_amount -= amt;
                } else if (u_type === '水费') {
                    compMap[a.from_company].water_usage -= eq_u;
                    compMap[a.from_company].water_amount -= amt;
                }
            }
            if (compMap[a.to_company]) {
                compMap[a.to_company].adjustment_amount += amt;
                if (u_type === '电费') {
                    compMap[a.to_company].electricity_usage += eq_u;
                    compMap[a.to_company].electricity_amount += amt;
                } else if (u_type === '水费') {
                    compMap[a.to_company].water_usage += eq_u;
                    compMap[a.to_company].water_amount += amt;
                }
            }
        }
    });

    let grandTot = 0;
    data.company_summaries = Object.values(compMap).map(s => {
        s.rent_amount = Math.round(s.rent_amount * 100) / 100;
        s.property_fee_amount = Math.round(s.property_fee_amount * 100) / 100;
        s.electricity_usage = Math.round(s.electricity_usage * 100) / 100;
        s.electricity_amount = Math.round(s.electricity_amount * 100) / 100;
        s.water_usage = Math.round(s.water_usage * 100) / 100;
        s.water_amount = Math.round(s.water_amount * 100) / 100;
        s.adjustment_amount = Math.round(s.adjustment_amount * 100) / 100;

        s.total_amount = Math.round((s.rent_amount + s.property_fee_amount + s.electricity_amount + s.water_amount) * 100) / 100;
        grandTot += s.total_amount;
        return s;
    });

    data.total_amount = Math.round(grandTot * 100) / 100;
}
