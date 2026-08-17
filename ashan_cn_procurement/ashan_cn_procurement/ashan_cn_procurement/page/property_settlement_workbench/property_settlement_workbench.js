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

            <!-- ❶ 顶部标题与月度控制栏 -->
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

                <div class="prop-actions">
                    <button class="prop-btn prop-btn-secondary" id="btn-save-draft">💾 保存草稿</button>
                    <button class="prop-btn prop-btn-primary" id="btn-preview-bills">📄 结算单预览/打印</button>
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
                                <th style="text-align: center; width: 100px;">公司结算单</th>
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
            this.$container.find('.prop-excel-table, .rate-input').addClass('table-locked');
        } else {
            $badge.removeClass('status-locked').addClass('status-draft').html('🟡 草稿录入中');
            $btnFinalize.show();
            $btnRevert.hide();
            $btnSave.show();
            $btnAddAdj.show();
            this.$container.find('.prop-excel-table, .rate-input').removeClass('table-locked');
        }

        // 单价
        this.$container.find('#inp-elec-price').val(d.electricity_price || 1.1957).prop('disabled', isLocked);
        this.$container.find('#inp-water-price').val(d.water_price || 5.5).prop('disabled', isLocked);

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
                            🖨️ 结算单
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
            $tbody.append($r);
        });

        // 合计行
        $tbody.append(`
            <tr class="prop-row-total">
                <td><b>合计</b></td>
                <td style="text-align: right;">¥ ${format_currency(totRent)}</td>
                <td style="text-align: right;">¥ ${format_currency(totProp)}</td>
                <td style="text-align: right;">${format_number(totElecU)}</td>
                <td style="text-align: right;">¥ ${format_currency(totElecA)}</td>
                <td style="text-align: right;">${format_number(totWaterU)}</td>
                <td style="text-align: right;">¥ ${format_currency(totWaterA)}</td>
                <td style="text-align: right;">${totAdj !== 0 ? '¥ ' + format_currency(totAdj) : '—'}</td>
                <td style="text-align: right; font-weight: 800; font-size: 15px; color: #166534;">¥ ${format_currency(totGrand)}</td>
                <td></td>
            </tr>
        `);
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

        // 调用集中纯算法
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
                    label: '调整原因 (必填)',
                    reqd: 1,
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
                    reason: values.reason
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

    // ─── 弹窗 3: 单一公司结算单预览与打印 ─────────────────────
    open_single_bill_dialog(company) {
        const self = this;
        const d = self.data;
        if (!d) return;

        const compMeters = (d.meter_readings || []).filter(m => m.company === company);
        const compLeases = (d.lease_charges || []).filter(l => l.company === company);
        const compSummary = (d.company_summaries || []).find(s => s.company === company) || {};

        const compAdjustments = [];
        (d.adjustments || []).forEach(a => {
            if (a.adjustment_scope === '单公司' && a.company === company) {
                compAdjustments.push({
                    title: a.utility_type,
                    type: a.adjustment_type,
                    scope: '单公司调整',
                    usage: a.equivalent_usage,
                    amount: a.amount_adjustment,
                    reason: a.reason
                });
            } else if (a.adjustment_scope === '公司间转移') {
                if (a.from_company === company) {
                    compAdjustments.push({
                        title: `${a.utility_type}调出 (转至 ${a.to_company})`,
                        type: `${a.adjustment_type} (公司间转出)`,
                        scope: '公司间转移',
                        usage: -a.equivalent_usage,
                        amount: -a.amount_adjustment,
                        reason: a.reason
                    });
                } else if (a.to_company === company) {
                    compAdjustments.push({
                        title: `${a.utility_type}调入 (来自 ${a.from_company})`,
                        type: `${a.adjustment_type} (公司间转入)`,
                        scope: '公司间转移',
                        usage: a.equivalent_usage,
                        amount: a.amount_adjustment,
                        reason: a.reason
                    });
                }
            }
        });

        const bill = {
            settlement_month: d.settlement_month,
            company: company,
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
        const monthStr = bill.settlement_month.substring(0, 7);

        let meterRows = '';
        (bill.meters || []).forEach(m => {
            meterRows += `
                <tr>
                    <td>${m.utility_type}</td>
                    <td style="text-align:center;">${m.meter_no}</td>
                    <td style="text-align:right;">${format_number(m.previous_reading)}</td>
                    <td style="text-align:right;">${format_number(m.current_reading)}</td>
                    <td style="text-align:right;">${format_number(m.raw_usage)}</td>
                    <td style="text-align:center;">×${m.multiplier}</td>
                    <td style="text-align:right; font-weight:600;">${format_number(m.calculated_usage)}</td>
                    <td style="text-align:right;">¥ ${m.unit_price}</td>
                    <td style="text-align:right; font-weight:700;">¥ ${format_currency(m.amount_tax_incl)}</td>
                </tr>
            `;
        });

        let leaseRows = '';
        (bill.leases || []).forEach(l => {
            const propFeeText = (l.property_fee_mode === '单独计收物业费')
                ? `¥ ${format_currency(l.property_fee_amount_tax_incl)} (${l.property_fee_rate_snapshot || ''})`
                : '已包含在房租中';

            leaseRows += `
                <tr>
                    <td>${frappe.utils.escape_html(l.property_name)}</td>
                    <td style="text-align:right;">${format_number(l.area)} ㎡</td>
                    <td>${frappe.utils.escape_html(l.rent_rate_snapshot || '—')}</td>
                    <td>${propFeeText}</td>
                    <td style="text-align:center;">${l.billing_days} 天</td>
                    <td style="text-align:right;">¥ ${format_currency(l.rent_amount_tax_incl)}</td>
                    <td style="text-align:right; font-weight:700; color:#166534;">¥ ${format_currency(l.amount_tax_incl)}</td>
                </tr>
            `;
        });

        let adjRows = '';
        (bill.adjustments || []).forEach(a => {
            adjRows += `
                <tr>
                    <td>${a.title}</td>
                    <td>${a.type} (${a.scope})</td>
                    <td style="text-align:right;">${a.usage ? format_number(a.usage) : '—'}</td>
                    <td style="text-align:right; font-weight:700; color:${a.amount < 0 ? '#dc2626' : '#059669'};">¥ ${format_currency(a.amount)}</td>
                    <td>${frappe.utils.escape_html(a.reason || '')}</td>
                </tr>
            `;
        });

        const totalAmt = bill.summary ? bill.summary.total_amount : 0;
        const rentAmt = bill.summary ? bill.summary.rent_amount : 0;
        const propAmt = bill.summary ? bill.summary.property_fee_amount : 0;

        const dlg = new frappe.ui.Dialog({
            title: `📄 ${bill.company} — ${monthStr} 物业水电结算单`,
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'bill_html',
                    options: `
                        <div class="print-bill-container" id="printable-company-bill">
                            <div class="bill-header">
                                <h3 class="bill-title">${frappe.utils.escape_html(bill.company)} 物业及水电月度结算单</h3>
                                <div class="bill-meta">
                                    <span>结算周期: <b>${monthStr}</b></span>
                                    <span>状态: <b>${bill.status}</b></span>
                                </div>
                            </div>

                            ${bill.meters?.length ? `
                            <div class="bill-section-title">一、水电费明细 (电价: ¥${bill.electricity_price}/kWh, 水价: ¥${bill.water_price}/m³)</div>
                            <table class="bill-table">
                                <thead>
                                    <tr>
                                        <th>类型</th><th>表号</th><th>上期</th><th>本期</th><th>差值</th><th>倍率</th><th>核定用量</th><th>单价</th><th>含税金额</th>
                                    </tr>
                                </thead>
                                <tbody>${meterRows}</tbody>
                            </table>
                            ` : ''}

                            ${bill.leases?.length ? `
                            <div class="bill-section-title" style="margin-top:14px;">二、房租及物业费明细 (房租合计: ¥${format_currency(rentAmt)}, 物业费合计: ¥${format_currency(propAmt)})</div>
                            <table class="bill-table">
                                <thead>
                                    <tr>
                                        <th>场地</th><th>面积</th><th>房租单价</th><th>物业费计收</th><th>计费天数</th><th>房租金额</th><th>含税合计</th>
                                    </tr>
                                </thead>
                                <tbody>${leaseRows}</tbody>
                            </table>
                            ` : ''}

                            ${bill.adjustments?.length ? `
                            <div class="bill-section-title" style="margin-top:14px;">三、费用调整明细</div>
                            <table class="bill-table">
                                <thead>
                                    <tr>
                                        <th>调整项</th><th>方式</th><th>等效用量</th><th>调整金额</th><th>原因说明</th>
                                    </tr>
                                </thead>
                                <tbody>${adjRows}</tbody>
                            </table>
                            ` : ''}

                            <div class="bill-footer-total">
                                <span>本月应付总额: </span>
                                <span class="grand-total-amount">¥ ${format_currency(totalAmt)}</span>
                            </div>
                        </div>
                    `
                }
            ],
            primary_action_label: '🖨️ 打印结算单',
            primary_action() {
                const printContents = document.getElementById('printable-company-bill').innerHTML;
                const win = window.open('', '', 'height=700,width=900');
                win.document.write(`
                    <html>
                    <head>
                        <title>${bill.company} - ${monthStr} 物业结算单</title>
                        <style>
                            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 24px; }
                            .bill-header { text-align: center; margin-bottom: 20px; border-bottom: 2px solid #333; padding-bottom: 10px; }
                            .bill-title { margin: 0 0 8px 0; font-size: 20px; }
                            .bill-meta { display: flex; justify-content: space-between; font-size: 13px; color: #555; }
                            .bill-section-title { font-weight: 700; margin: 16px 0 8px 0; font-size: 14px; color: #111; }
                            .bill-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 12px; }
                            .bill-table th, .bill-table td { border: 1px solid #ccc; padding: 6px 8px; }
                            .bill-table th { background: #f5f5f5; font-weight: 600; }
                            .bill-footer-total { text-align: right; font-size: 16px; font-weight: 700; margin-top: 20px; padding: 10px; background: #f9f9f9; border: 1px solid #ddd; }
                            .grand-total-amount { color: #166534; font-size: 20px; }
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

    // 2. 调整
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

    (data.lease_charges || []).forEach(l => {
        const area = parseFloat(l.area) || 0;
        const l_days = parseInt(l.billing_days) || 30;

        let rent_amt = parseFloat(l.rent_amount_tax_incl) || 0;
        if (l.rent_annual_amount > 0) {
            rent_amt = Math.round((parseFloat(l.rent_annual_amount) / 365 * l_days) * 100) / 100;
        } else if (l.rent_daily_rate > 0 && area > 0) {
            rent_amt = Math.round((area * parseFloat(l.rent_daily_rate) * l_days) * 100) / 100;
        } else if (l.rent_monthly_amount > 0) {
            rent_amt = Math.round((parseFloat(l.rent_monthly_amount) * (l_days / 30.0)) * 100) / 100;
        }

        let prop_amt = 0;
        if (l.property_fee_mode === '单独计收物业费') {
            if (l.property_fee_annual_amount > 0) {
                prop_amt = Math.round((parseFloat(l.property_fee_annual_amount) / 365 * l_days) * 100) / 100;
            } else if (l.property_fee_daily_rate > 0 && area > 0) {
                prop_amt = Math.round((area * parseFloat(l.property_fee_daily_rate) * l_days) * 100) / 100;
            } else if (l.property_fee_monthly_amount > 0) {
                prop_amt = Math.round((parseFloat(l.property_fee_monthly_amount) * (l_days / 30.0)) * 100) / 100;
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
