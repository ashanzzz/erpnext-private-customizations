// -*- coding: utf-8 -*-
frappe.pages['vehicle-toll-ledger'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('高速费月度台账大屏'),
        single_column: true
    });
    wrapper.vehicle_toll_ledger = new VehicleTollLedger(wrapper, page);
};

frappe.pages['vehicle-toll-ledger'].on_page_show = function(wrapper) {
    if (wrapper.vehicle_toll_ledger) {
        wrapper.vehicle_toll_ledger.refresh();
    }
};

/* ============================================================
   VehicleTollLedger — 高速费月度台账（车辆选项卡大屏）
   ============================================================ */
class VehicleTollLedger {
    constructor(wrapper, page) {
        this.wrapper = wrapper;
        this.page = page;
        this.$container = $(wrapper).find('.layout-main-section');

        const now = new Date();
        this.currentYear = now.getFullYear();
        this.currentMonth = now.getMonth() + 1;

        this.vehicles = [];          // 入池车辆列表
        this.activeVehicle = null;   // 当前选中的 vehicle_config name
        this.sheetData = null;       // 当前车辆当月台账数据
        this.isDirty = false;
        this.isManager = false;

        this.init_dom();
        this.bind_global_events();
        this.load_vehicles();
    }

    // ─── DOM 骨架 ────────────────────────────────────────────
    init_dom() {
        this.$container.html(`
        <div class="toll-ledger-wrapper">

            <!-- 顶部控制栏 -->
            <div class="toll-header-bar">
                <div class="toll-title-box">
                    <h3 class="toll-page-title">🛣️ 高速通行费月度台账</h3>
                    <span id="toll-status-badge" class="toll-status-badge status-open">🟢 正常录入中</span>
                </div>
                <div class="toll-period-selector">
                    <button class="toll-btn-nav" id="btn-prev-month">◀</button>
                    <select id="sel-year" class="toll-select-period"></select>
                    <select id="sel-month" class="toll-select-period"></select>
                    <button class="toll-btn-nav" id="btn-next-month">▶</button>
                    <button class="toll-btn-nav" id="btn-cur-month">本月</button>
                </div>
                <div class="toll-actions">
                    <button class="toll-btn toll-btn-secondary" id="btn-manage-vehicles">⚙️ 管理入池车辆</button>
                    <button class="toll-btn toll-btn-secondary" id="btn-config-routes" style="display:none;">🛤️ 配置收费站列</button>
                    <button class="toll-btn toll-btn-lock" id="btn-toggle-lock" style="display:none;">🔒 本月核定</button>
                    <button class="toll-btn toll-btn-primary" id="btn-save" style="display:none;">💾 保存 (Ctrl+S)</button>
                </div>
            </div>

            <!-- KPI 概览卡片 -->
            <div class="toll-kpi-grid" id="kpi-grid" style="display:none;">
                <div class="toll-kpi-card kpi-opening">
                    <div class="toll-kpi-title">期初结转余额</div>
                    <div class="toll-kpi-value" id="kpi-opening">¥ 0.00</div>
                </div>
                <div class="toll-kpi-card kpi-expense">
                    <div class="toll-kpi-title">本期通行费合计</div>
                    <div class="toll-kpi-value" id="kpi-expense">¥ 0.00</div>
                </div>
                <div class="toll-kpi-card kpi-deposit">
                    <div class="toll-kpi-title">本期公司预支/注入</div>
                    <div class="toll-kpi-value" id="kpi-deposit">¥ 0.00</div>
                </div>
                <div class="toll-kpi-card kpi-closing">
                    <div class="toll-kpi-title">期末结余</div>
                    <div class="toll-kpi-value" id="kpi-closing">¥ 0.00</div>
                </div>
            </div>

            <!-- 车辆选项卡栏 -->
            <div class="toll-tabs-wrapper" id="toll-tabs-wrapper" style="display:none;">
                <div class="toll-tabs" id="toll-tabs-bar">
                    <!-- 动态渲染 -->
                </div>
            </div>

            <!-- 台账表格区域 -->
            <div class="toll-sheet-container" id="toll-sheet-container" style="display:none;">
                <div class="toll-table-wrapper">
                    <table class="toll-excel-table" id="toll-matrix-table">
                        <thead id="toll-thead"></thead>
                        <tbody id="toll-tbody"></tbody>
                        <tfoot id="toll-tfoot"></tfoot>
                    </table>
                </div>
                <!-- 快捷预支注入面板 -->
                <div class="toll-deposit-panel" id="toll-deposit-panel">
                    <div class="toll-deposit-header">
                        <strong>💰 本月公司预支/注入流水</strong>
                        <button class="toll-btn toll-btn-deposit" id="btn-add-deposit">＋ 新增预支充值</button>
                    </div>
                    <div id="deposit-list-container"><!-- 动态渲染 --></div>
                </div>
                <div class="toll-footer-bar">
                    <div class="toll-shortcuts">
                        <span><kbd>Tab</kbd>/<kbd>Enter</kbd> 换格</span>
                        <span><kbd>Ctrl+S</kbd> 保存</span>
                        <span>💡 通行费录入后自动计算结余</span>
                    </div>
                    <div id="toll-save-status">尚未修改</div>
                </div>
            </div>

            <!-- 无车辆空态提示 -->
            <div class="toll-empty-state" id="toll-empty-state" style="display:none;">
                <div class="toll-empty-icon">🚗</div>
                <div class="toll-empty-title">暂无入池车辆</div>
                <div class="toll-empty-desc">点击上方「⚙️ 管理入池车辆」添加需要纳入高速费管理的车辆</div>
            </div>

        </div>`);

        // 年月选择器
        const $yearSel = this.$container.find('#sel-year');
        const nowYear = new Date().getFullYear();
        for (let y = nowYear - 3; y <= nowYear + 2; y++) {
            $yearSel.append(`<option value="${y}">${y}年</option>`);
        }
        $yearSel.val(this.currentYear);

        const $monthSel = this.$container.find('#sel-month');
        for (let m = 1; m <= 12; m++) {
            $monthSel.append(`<option value="${m}">${m}月</option>`);
        }
        $monthSel.val(this.currentMonth);
    }

    // ─── 全局事件绑定 ────────────────────────────────────────
    bind_global_events() {
        const self = this;
        const $c = this.$container;

        $c.find('#sel-year, #sel-month').on('change', () => {
            self.currentYear = parseInt($c.find('#sel-year').val());
            self.currentMonth = parseInt($c.find('#sel-month').val());
            if (self.activeVehicle) self.load_sheet();
        });
        $c.find('#btn-prev-month').on('click', () => { self.shift_month(-1); });
        $c.find('#btn-next-month').on('click', () => { self.shift_month(1); });
        $c.find('#btn-cur-month').on('click', () => {
            const now = new Date();
            self.currentYear = now.getFullYear();
            self.currentMonth = now.getMonth() + 1;
            self.update_period_ui();
            if (self.activeVehicle) self.load_sheet();
        });
        $c.find('#btn-save').on('click', () => self.save_sheet());
        $c.find('#btn-toggle-lock').on('click', () => {
            if (!self.sheetData) return;
            self.sheetData.is_locked ? self.reopen_sheet() : self.close_sheet();
        });
        $c.find('#btn-manage-vehicles').on('click', () => self.open_manage_vehicles_dialog());
        $c.find('#btn-config-routes').on('click', () => self.open_config_routes_dialog());
        $c.find('#btn-add-deposit').on('click', () => self.open_add_deposit_dialog());

        $(document).on('keydown.toll_ledger', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                if ($('#toll-matrix-table').is(':visible')) {
                    e.preventDefault();
                    self.save_sheet();
                }
            }
        });
    }

    shift_month(delta) {
        let m = this.currentMonth + delta;
        let y = this.currentYear;
        if (m > 12) { m = 1; y++; }
        if (m < 1) { m = 12; y--; }
        this.currentMonth = m;
        this.currentYear = y;
        this.update_period_ui();
        if (this.activeVehicle) this.load_sheet();
    }

    update_period_ui() {
        this.$container.find('#sel-year').val(this.currentYear);
        this.$container.find('#sel-month').val(this.currentMonth);
    }

    refresh() {
        this.load_vehicles();
    }

    // ─── 加载入池车辆列表 ────────────────────────────────────
    load_vehicles() {
        const self = this;
        frappe.call({
            method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.get_enrolled_vehicles',
            freeze: true,
            freeze_message: '正在加载高速费车辆列表...',
            callback(r) {
                if (!r.message) return;
                self.vehicles = r.message.vehicles || [];
                self.isManager = r.message.is_manager;
                self.render_tabs();
            }
        });
    }

    // ─── 渲染车辆选项卡 ──────────────────────────────────────
    render_tabs() {
        const self = this;
        const $tabsBar = this.$container.find('#toll-tabs-bar');
        $tabsBar.empty();

        if (!this.vehicles.length) {
            this.$container.find('#toll-tabs-wrapper').hide();
            this.$container.find('#toll-sheet-container').hide();
            this.$container.find('#kpi-grid').hide();
            this.$container.find('#toll-empty-state').show();
            return;
        }

        this.$container.find('#toll-empty-state').hide();
        this.$container.find('#toll-tabs-wrapper').show();
        this.$container.find('#kpi-grid').show();

        this.vehicles.forEach(v => {
            const isActive = v.config_name === self.activeVehicle;
            const $tab = $(`
                <div class="toll-tab-item ${isActive ? 'active' : ''}" data-config="${v.config_name}">
                    <span class="toll-tab-icon">🚗</span>
                    <span class="toll-tab-label">${frappe.utils.escape_html(v.display_name)}</span>
                </div>
            `);
            $tab.on('click', () => {
                self.activeVehicle = v.config_name;
                self.$container.find('.toll-tab-item').removeClass('active');
                $tab.addClass('active');
                self.load_sheet();
            });
            $tabsBar.append($tab);
        });

        // 如果还没选中任何车辆，自动选第一辆
        if (!this.activeVehicle || !this.vehicles.find(v => v.config_name === this.activeVehicle)) {
            this.activeVehicle = this.vehicles[0].config_name;
            $tabsBar.find('.toll-tab-item').first().addClass('active');
        }

        this.load_sheet();
    }

    // ─── 加载当前车辆当月台账 ────────────────────────────────
    load_sheet() {
        const self = this;
        if (!this.activeVehicle) return;

        frappe.call({
            method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.get_vehicle_monthly_sheet',
            args: {
                vehicle_config: self.activeVehicle,
                year: self.currentYear,
                month: self.currentMonth
            },
            freeze: true,
            freeze_message: '正在加载台账数据...',
            callback(r) {
                if (r.message) {
                    self.sheetData = r.message;
                    self.render_sheet();
                }
            }
        });
    }

    // ─── 渲染台账表格 ─────────────────────────────────────────
    render_sheet() {
        const d = this.sheetData;
        const self = this;
        const $c = this.$container;

        $c.find('#toll-sheet-container').show();

        // 状态与按钮
        const $badge = $c.find('#toll-status-badge');
        const $lockBtn = $c.find('#btn-toggle-lock');
        const $sheetBox = $c.find('#toll-sheet-container');
        const $saveBtn = $c.find('#btn-save');
        const $configRoutes = $c.find('#btn-config-routes');

        $configRoutes.show();

        if (d.is_locked) {
            $badge.removeClass('status-open').addClass('status-locked')
                .html(`🔒 ${d.year}年${d.month}月已核定锁定`);
            $sheetBox.addClass('toll-sheet-locked');
            $saveBtn.hide();
            if (d.is_manager) {
                $lockBtn.show().removeClass('toll-btn-lock').addClass('toll-btn-unlock').html('🔓 取消核定');
            } else {
                $lockBtn.hide();
            }
        } else {
            $badge.removeClass('status-locked').addClass('status-open').html('🟢 正常录入中');
            $sheetBox.removeClass('toll-sheet-locked');
            $saveBtn.show();
            if (d.is_manager) {
                $lockBtn.show().removeClass('toll-btn-unlock').addClass('toll-btn-lock').html('🔒 本月核定');
            } else {
                $lockBtn.hide();
            }
        }

        const routes = d.toll_routes || [];

        // 表头
        let thHtml = `<tr>
            <th style="width:140px;">日期</th>`;
        routes.forEach(r => {
            thHtml += `<th style="min-width:85px;">${frappe.utils.escape_html(r.name)}</th>`;
        });
        thHtml += `
            <th style="min-width:90px;background:#fef2f2;color:#991b1b;">日合计</th>
            <th style="min-width:110px;background:#f0fdf4;color:#166534;">公司预支注入</th>
            <th style="min-width:110px;background:#f5f3ff;color:#5b21b6;">实时结余</th>
            <th style="min-width:130px;">备注</th>
        </tr>`;
        $c.find('#toll-thead').html(thHtml);

        // 表体：期初行 + 每日行
        let tbHtml = `<tr class="row-opening">
            <td class="cell-date">🔁 结转期初</td>`;
        routes.forEach(() => { tbHtml += `<td></td>`; });
        tbHtml += `
            <td></td>
            <td></td>
            <td class="cell-balance" id="opening-bal-cell">
                ${d.is_locked
                    ? `<span class="cell-readonly">${fmt_cur(d.opening_balance)}</span>`
                    : `<input type="number" step="0.01" class="cell-input" id="input-opening" value="${d.opening_balance || 0}">`
                }
            </td>
            <td style="font-size:12px;color:#15803d;">上月期末结转</td>
        </tr>`;

        (d.daily_records || []).forEach(r => {
            const weekendCls = r.is_weekend ? 'row-weekend' : '';
            const deposits_html = r.deposit > 0
                ? `<span class="deposit-badge">+${fmt_cur(r.deposit)}</span>`
                : '';
            tbHtml += `<tr class="${weekendCls}" data-day="${r.day}">
                <td class="cell-date">${r.date_display || r.date}</td>`;

            routes.forEach(route => {
                const val = (r.routes && r.routes[route.id]) ? r.routes[route.id] : '';
                tbHtml += `<td>
                    <input type="number" step="0.01" class="cell-input cell-route-input"
                           data-day="${r.day}" data-rid="${route.id}"
                           value="${val}" placeholder="—"
                           ${d.is_locked ? 'disabled' : ''}>
                </td>`;
            });

            tbHtml += `
                <td class="cell-readonly cell-expense" id="exp-${r.day}">
                    ${r.expense > 0 ? fmt_cur(r.expense) : '—'}
                </td>
                <td class="cell-readonly cell-deposit" id="dep-${r.day}">
                    ${r.deposit > 0 ? `+${fmt_cur(r.deposit)}` : '—'}
                </td>
                <td class="cell-readonly cell-balance ${r.balance < 0 ? 'negative' : ''}" id="bal-${r.day}">
                    ${fmt_cur(r.balance)}
                </td>
                <td>
                    <input type="text" class="cell-input cell-remark-input"
                           data-day="${r.day}"
                           value="${frappe.utils.escape_html(r.remark || '')}"
                           placeholder="备注"
                           ${d.is_locked ? 'disabled' : ''}>
                </td>
            </tr>`;
        });

        $c.find('#toll-tbody').html(tbHtml);

        // 表尾合计行
        let tfHtml = `<tr class="row-summary">
            <td style="text-align:center;">📊 月度合计</td>`;
        routes.forEach(route => {
            tfHtml += `<td class="cell-readonly" id="sum-route-${route.id}">—</td>`;
        });
        tfHtml += `
            <td class="cell-readonly cell-expense" id="sum-expense">—</td>
            <td class="cell-readonly cell-deposit" id="sum-deposit">—</td>
            <td class="cell-readonly cell-balance" id="sum-balance">—</td>
            <td></td>
        </tr>`;
        $c.find('#toll-tfoot').html(tfHtml);

        // 绑定输入事件
        this.bind_cell_events();

        // 全量重算
        this.recalculate();

        // 渲染预支流水面板
        this.render_deposit_panel(d.deposit_records || []);
    }

    // ─── 绑定单元格事件 ──────────────────────────────────────
    bind_cell_events() {
        const self = this;
        const $t = this.$container.find('#toll-matrix-table');

        $t.find('.cell-route-input, #input-opening').on('input', function() {
            $(this).addClass('changed');
            self.isDirty = true;
            self.$container.find('#toll-save-status').html('⚠️ 有未保存修改');
            self.recalculate();
        });

        // Enter 跳到下一行同列
        $t.find('.cell-input').on('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const idx = $(this).closest('td').index();
                const $nextRow = $(this).closest('tr').next('tr:not(.row-summary)');
                if ($nextRow.length) {
                    const $inp = $nextRow.children('td').eq(idx).find('.cell-input');
                    if ($inp.length) $inp.focus().select();
                }
            }
        });
    }

    // ─── 全表级联重算 ─────────────────────────────────────────
    recalculate() {
        const d = this.sheetData;
        if (!d) return;
        const routes = d.toll_routes || [];

        let opening = d.is_locked
            ? flt(d.opening_balance)
            : flt(this.$container.find('#input-opening').val());

        let curBal = opening;
        let totExp = 0, totDep = 0;
        const routeTotals = {};
        routes.forEach(r => routeTotals[r.id] = 0);

        this.$container.find('#toll-tbody tr[data-day]').each(function() {
            const $row = $(this);
            const dayNum = parseInt($row.attr('data-day'));

            let dayExp = 0;
            routes.forEach(route => {
                const v = flt($row.find(`.cell-route-input[data-rid="${route.id}"]`).val());
                dayExp += v;
                routeTotals[route.id] += v;
            });

            // 预支注入来自服务器数据（只读列，不可在表格直接编辑）
            const dayRec = (d.daily_records || []).find(r => r.day === dayNum);
            const dayDep = dayRec ? flt(dayRec.deposit) : 0;

            curBal = curBal - dayExp + dayDep;
            totExp += dayExp;
            totDep += dayDep;

            $(`#exp-${dayNum}`).text(dayExp > 0 ? fmt_cur(dayExp) : '—');
            const $balCell = $(`#bal-${dayNum}`);
            $balCell.text(fmt_cur(curBal));
            $balCell.toggleClass('negative', curBal < 0);
        });

        // 合计行
        routes.forEach(r => {
            $(`#sum-route-${r.id}`).text(routeTotals[r.id] > 0 ? fmt_cur(routeTotals[r.id]) : '—');
        });
        this.$container.find('#sum-expense').text(fmt_cur(totExp));
        this.$container.find('#sum-deposit').text(totDep > 0 ? `+${fmt_cur(totDep)}` : '—');
        const $sumBal = this.$container.find('#sum-balance');
        $sumBal.text(fmt_cur(curBal)).toggleClass('negative', curBal < 0);

        // KPI
        this.$container.find('#kpi-opening').text(`¥ ${fmt_cur(opening)}`);
        this.$container.find('#kpi-expense').text(`¥ ${fmt_cur(totExp)}`);
        this.$container.find('#kpi-deposit').text(`¥ ${fmt_cur(totDep)}`);
        this.$container.find('#kpi-closing').text(`¥ ${fmt_cur(curBal)}`);
    }

    // ─── 收集当前表格数据 ────────────────────────────────────
    collect_data() {
        const d = this.sheetData;
        const routes = d.toll_routes || [];
        let opening = d.is_locked ? flt(d.opening_balance) : flt(this.$container.find('#input-opening').val());

        const daily_records = [];
        this.$container.find('#toll-tbody tr[data-day]').each(function() {
            const $row = $(this);
            const dayNum = parseInt($row.attr('data-day'));
            const dateStr = `${d.year}/${String(d.month).padStart(2,'0')}/${String(dayNum).padStart(2,'0')}`;

            const routesData = {};
            routes.forEach(route => {
                const v = flt($row.find(`.cell-route-input[data-rid="${route.id}"]`).val());
                if (v > 0) routesData[route.id] = v;
            });

            const remark = $row.find('.cell-remark-input').val() || '';
            daily_records.push({ day: dayNum, date: dateStr, routes: routesData, remark });
        });

        return {
            vehicle_config: this.activeVehicle,
            year: this.currentYear,
            month: this.currentMonth,
            daily_records,
            toll_routes: routes,
            remark: this.$container.find('.toll-sheet-remark')?.val() || ''
        };
    }

    // ─── 保存台账 ────────────────────────────────────────────
    save_sheet() {
        const self = this;
        const payload = this.collect_data();
        frappe.call({
            method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.save_vehicle_toll_sheet',
            args: {
                vehicle_config: payload.vehicle_config,
                year: payload.year,
                month: payload.month,
                daily_records: payload.daily_records,
                toll_routes: payload.toll_routes,
                remark: payload.remark
            },
            freeze: true,
            freeze_message: '正在保存台账...',
            callback(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({ message: '月度高速费台账保存成功！', indicator: 'green' }, 4);
                    self.isDirty = false;
                    self.$container.find('.cell-input').removeClass('changed');
                    self.$container.find('#toll-save-status').text(`已于 ${new Date().toLocaleTimeString()} 保存`);
                    self.load_sheet();
                }
            }
        });
    }

    // ─── 月度核定 / 解锁 ─────────────────────────────────────
    close_sheet() {
        const self = this;
        frappe.confirm(
            `确定核定锁定 <b>${self.currentYear}年${self.currentMonth}月</b>（${self.sheetData?.display_name}）的台账吗？<br>核定后期末结存将自动结转至下月期初。`,
            () => {
                const payload = self.collect_data();
                frappe.call({
                    method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.save_vehicle_toll_sheet',
                    args: { ...payload },
                    callback() {
                        frappe.call({
                            method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.close_vehicle_toll_sheet',
                            args: { vehicle_config: self.activeVehicle, year: self.currentYear, month: self.currentMonth },
                            freeze: true,
                            freeze_message: '正在执行月度核定...',
                            callback(r) {
                                if (r.message?.success) {
                                    frappe.msgprint({ title: '核定成功', indicator: 'green', message: r.message.message });
                                    self.load_sheet();
                                }
                            }
                        });
                    }
                });
            }
        );
    }

    reopen_sheet() {
        const self = this;
        frappe.confirm(`确定取消 <b>${self.currentYear}年${self.currentMonth}月</b>（${self.sheetData?.display_name}）的核定锁定吗？`, () => {
            frappe.call({
                method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.reopen_vehicle_toll_sheet',
                args: { vehicle_config: self.activeVehicle, year: self.currentYear, month: self.currentMonth },
                freeze: true,
                callback(r) {
                    if (r.message?.success) {
                        frappe.show_alert({ message: r.message.message, indicator: 'blue' }, 4);
                        self.load_sheet();
                    }
                }
            });
        });
    }

    // ─── 预支/注入流水面板 ────────────────────────────────────
    render_deposit_panel(deposits) {
        const self = this;
        const $list = this.$container.find('#deposit-list-container');
        $list.empty();

        if (!deposits.length) {
            $list.html(`<div class="deposit-empty">本月暂无预支/注入记录，点击右侧按钮新增</div>`);
            return;
        }

        let html = `<table class="deposit-table">
            <thead><tr>
                <th>预支日期</th><th>金额</th><th>预支方式</th><th>凭证号</th><th>备注</th>
                ${self.sheetData?.is_locked ? '' : '<th>操作</th>'}
            </tr></thead><tbody>`;

        deposits.forEach(dep => {
            html += `<tr>
                <td>${dep.deposit_date || ''}</td>
                <td class="dep-amount">+¥ ${fmt_cur(flt(dep.amount))}</td>
                <td>${dep.deposit_type || ''}</td>
                <td>${dep.reference_no || '—'}</td>
                <td>${dep.remark || '—'}</td>
                ${self.sheetData?.is_locked ? '' : `<td><button class="toll-btn-del-dep" data-name="${dep.name}">🗑</button></td>`}
            </tr>`;
        });

        html += `</tbody></table>`;
        $list.html(html);

        // 绑定删除按钮
        $list.find('.toll-btn-del-dep').on('click', function() {
            const depName = $(this).attr('data-name');
            frappe.confirm('确定删除此预支记录吗？删除后结余将实时重新计算。', () => {
                frappe.call({
                    method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.delete_toll_deposit',
                    args: { deposit_name: depName },
                    callback(r) {
                        if (r.message?.success) {
                            frappe.show_alert({ message: '预支记录已删除', indicator: 'orange' }, 3);
                            self.load_sheet();
                        }
                    }
                });
            });
        });
    }

    // ─── 新增预支 Dialog ──────────────────────────────────────
    open_add_deposit_dialog() {
        const self = this;
        const d = new frappe.ui.Dialog({
            title: `💰 新增公司预支/充值 — ${self.sheetData?.display_name || ''}`,
            fields: [
                {
                    fieldname: 'deposit_date', fieldtype: 'Date', label: '预支/充值日期',
                    reqd: 1,
                    default: frappe.datetime.get_today()
                },
                {
                    fieldname: 'amount', fieldtype: 'Currency', label: '预支金额 (元)',
                    reqd: 1, description: '公司向该车辆ETC账户注入的资金金额'
                },
                {
                    fieldname: 'deposit_type', fieldtype: 'Select', label: '预支方式',
                    options: '现金预支\n公户转账\nETC自动充值\n其他',
                    default: '现金预支'
                },
                {
                    fieldname: 'reference_no', fieldtype: 'Data', label: '凭证号/流水号',
                    description: '转账凭证号或ETC充值流水号（可选）'
                },
                { fieldname: 'remark', fieldtype: 'Small Text', label: '备注' }
            ],
            primary_action_label: '确认保存',
            primary_action(values) {
                frappe.call({
                    method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.add_toll_deposit',
                    args: {
                        vehicle_config: self.activeVehicle,
                        deposit_date: values.deposit_date,
                        amount: values.amount,
                        deposit_type: values.deposit_type,
                        reference_no: values.reference_no || '',
                        remark: values.remark || ''
                    },
                    freeze: true,
                    freeze_message: '正在保存预支记录...',
                    callback(r) {
                        if (r.message?.success) {
                            frappe.show_alert({ message: r.message.message, indicator: 'green' }, 4);
                            d.hide();
                            self.load_sheet();
                        }
                    }
                });
            }
        });
        d.show();
    }

    // ─── 管理入池车辆 Dialog ──────────────────────────────────
    open_manage_vehicles_dialog() {
        const self = this;
        const d = new frappe.ui.Dialog({
            title: '⚙️ 管理高速费入池车辆',
            size: 'large',
            fields: [
                {
                    fieldname: 'info_html', fieldtype: 'HTML',
                    options: `<div style="font-size:12px;color:#6b7280;margin-bottom:12px;">
                        在此管理纳入高速费台账的车辆。只有在此加入的车辆才会出现在顶部选项卡中。
                        可从"车辆管理"DocType中选择已有车辆。
                    </div>`
                },
                {
                    fieldname: 'section_add', fieldtype: 'Section Break', label: '添加新车辆到高速费管理'
                },
                {
                    fieldname: 'new_vehicle', fieldtype: 'Link', label: '选择车辆',
                    options: 'Vehicle',
                    description: '从车辆管理档案中选择需要纳入高速费管理的车辆'
                },
                {
                    fieldname: 'new_display_name', fieldtype: 'Data', label: '选项卡显示名称',
                    description: '如"粤B·8888 专车"，留空则使用车辆名称'
                },
                {
                    fieldname: 'new_opening_balance', fieldtype: 'Currency', label: '初始期初余额',
                    default: 0,
                    description: '该车辆高速费账户的启动资金余额（只在首次录入时有效）'
                },
                {
                    fieldname: 'section_cur', fieldtype: 'Section Break', label: '当前入池车辆'
                },
                {
                    fieldname: 'current_vehicles_html', fieldtype: 'HTML',
                    options: self._render_current_vehicles_html()
                }
            ],
            primary_action_label: '添加到入池',
            primary_action(values) {
                if (!values.new_vehicle) {
                    frappe.msgprint('请先选择要添加的车辆！');
                    return;
                }
                frappe.call({
                    method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.add_vehicle_to_toll',
                    args: {
                        vehicle: values.new_vehicle,
                        display_name: values.new_display_name || values.new_vehicle,
                        opening_balance: values.new_opening_balance || 0
                    },
                    freeze: true,
                    callback(r) {
                        if (r.message?.success) {
                            frappe.show_alert({ message: `车辆 ${values.new_vehicle} 已成功加入高速费管理！`, indicator: 'green' }, 4);
                            d.hide();
                            self.load_vehicles();
                        }
                    }
                });
            }
        });
        d.show();

        // 绑定停用按钮
        d.$wrapper.on('click', '.btn-deactivate-vehicle', function() {
            const configName = $(this).attr('data-config');
            const label = $(this).attr('data-label');
            frappe.confirm(`确定将 <b>${label}</b> 移出高速费管理吗？历史台账数据将保留。`, () => {
                frappe.call({
                    method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.remove_vehicle_from_toll',
                    args: { vehicle_config: configName },
                    callback(r) {
                        if (r.message?.success) {
                            frappe.show_alert({ message: `已将 ${label} 移出高速费管理`, indicator: 'orange' }, 3);
                            d.hide();
                            if (self.activeVehicle === configName) self.activeVehicle = null;
                            self.load_vehicles();
                        }
                    }
                });
            });
        });
    }

    _render_current_vehicles_html() {
        if (!this.vehicles.length) {
            return `<div style="color:#9ca3af;padding:8px;">暂无入池车辆</div>`;
        }
        let html = `<table style="width:100%;font-size:13px;border-collapse:collapse;">
            <thead><tr style="background:#f8fafc;font-weight:600;">
                <th style="padding:6px 10px;border:1px solid #e2e8f0;">车辆</th>
                <th style="padding:6px 10px;border:1px solid #e2e8f0;">显示名称</th>
                <th style="padding:6px 10px;border:1px solid #e2e8f0;">操作</th>
            </tr></thead><tbody>`;
        this.vehicles.forEach(v => {
            html += `<tr>
                <td style="padding:6px 10px;border:1px solid #e2e8f0;">${frappe.utils.escape_html(v.vehicle || v.config_name)}</td>
                <td style="padding:6px 10px;border:1px solid #e2e8f0;">${frappe.utils.escape_html(v.display_name)}</td>
                <td style="padding:6px 10px;border:1px solid #e2e8f0;">
                    <button class="btn-deactivate-vehicle" data-config="${v.config_name}" data-label="${frappe.utils.escape_html(v.display_name)}"
                        style="background:#fef2f2;color:#dc2626;border:1px solid #fecaca;border-radius:4px;padding:2px 8px;cursor:pointer;font-size:12px;">
                        移出
                    </button>
                </td>
            </tr>`;
        });
        html += `</tbody></table>`;
        return html;
    }

    // ─── 配置收费站列 Dialog ──────────────────────────────────
    open_config_routes_dialog() {
        const self = this;
        if (!self.activeVehicle || !self.sheetData) return;

        const routes = self.sheetData.toll_routes || [];
        const d = new frappe.ui.Dialog({
            title: `🛤️ 配置收费站/路段列 — ${self.sheetData.display_name}`,
            fields: [
                {
                    fieldname: 'help_html', fieldtype: 'HTML',
                    options: `<div style="font-size:12px;color:#6b7280;margin-bottom:10px;">
                        配置该车辆每日高速通行费的收费站列（如"进城收费站"、"出城收费站"等）。修改后当月台账立即生效。
                    </div>`
                },
                {
                    fieldname: 'routes_table', fieldtype: 'Table', label: '收费站/路段列',
                    data: routes.map(r => ({ rid: r.id, rname: r.name })),
                    fields: [
                        { fieldname: 'rid', fieldtype: 'Data', label: '列ID', in_list_view: 1, columns: 3, read_only: 1 },
                        { fieldname: 'rname', fieldtype: 'Data', label: '收费站/路段名称', in_list_view: 1, reqd: 1, columns: 6 }
                    ]
                }
            ],
            primary_action_label: '确认保存',
            primary_action(values) {
                const rows = d.fields_dict.routes_table.get_value() || [];
                const updatedRoutes = rows.map((r, idx) => ({
                    id: r.rid || `r_${Date.now()}_${idx}`,
                    name: (r.rname || `收费站${idx + 1}`).trim()
                }));
                if (!updatedRoutes.length) {
                    frappe.msgprint('至少需要保留一个收费站列！');
                    return;
                }
                frappe.call({
                    method: 'ashan_cn_procurement.ashan_cn_procurement.page.vehicle_toll_ledger.vehicle_toll_ledger.update_vehicle_toll_routes',
                    args: { vehicle_config: self.activeVehicle, toll_routes: updatedRoutes },
                    callback(r) {
                        if (r.message?.success) {
                            frappe.show_alert({ message: '收费站列配置已更新！', indicator: 'green' }, 3);
                            d.hide();
                            self.sheetData.toll_routes = updatedRoutes;
                            self.render_sheet();
                        }
                    }
                });
            }
        });

        d.set_secondary_action_label('＋ 添加收费站');
        d.set_secondary_action(() => {
            const table = d.fields_dict.routes_table;
            const cur = table.get_value() || [];
            const next = cur.length + 1;
            cur.push({ rid: `r${next}`, rname: `收费站${next}` });
            table.df.data = cur;
            table.refresh();
        });

        d.show();
    }
}

function fmt_cur(val) {
    return flt(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
