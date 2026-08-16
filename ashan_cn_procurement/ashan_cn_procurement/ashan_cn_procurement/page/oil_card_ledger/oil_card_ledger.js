// Copyright (c) 2026, Ashan CN Procurement and contributors
// For license information, please see license.txt

function formatMoney(val) {
	if (val === null || val === undefined || isNaN(val)) return "¥ 0.00";
	return "¥ " + parseFloat(val).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

frappe.pages["oil-card-ledger"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("油卡综合台账明细台"),
		single_column: true,
	});

	new UnifiedOilCardLedgerConsole(page);
};

class UnifiedOilCardLedgerConsole {
	constructor(page) {
		this.page = page;
		this.wrapper = $(page.body);
		this.cards = [];
		this.activeCard = null;
		this.meta = { vehicles: [], modes_of_payment: [] };

		const now = new Date();
		this.selectedYear = now.getFullYear();
		this.selectedMonth = now.getMonth() + 1; // 1 - 12
		this.isManager = false;
		this.isLocked = false;
		this.currentEndingBalance = 0;

		this.initLayout();
		this.bindEvents();
		this.loadMeta();
		this.loadCards();
	}

	initLayout() {
		this.wrapper.html(`
			<div class="oil-console-layout">
				<!-- 左侧油卡选择侧边栏 -->
				<div class="oil-cards-sidebar">
					<div class="sidebar-header">
						<span class="sidebar-title">💳 全部油卡</span>
						<button class="btn-add-card" id="btn-create-card">+ 新建油卡</button>
					</div>
					<div class="card-search-box">
						<input type="text" class="card-search-input" id="card-search-input" placeholder="🔍 搜索油卡名称/卡号...">
					</div>
					<div class="cards-list-container" id="cards-list-container">
						<div class="empty-placeholder">
							<div class="empty-placeholder-icon">⏳</div>
							<div>加载油卡列表中…</div>
						</div>
					</div>
				</div>

				<!-- 右侧综合台账控制大屏 -->
				<div class="oil-console-main" id="console-main-pane">
					<div class="empty-placeholder" id="main-empty-placeholder" style="padding: 100px 0;">
						<div class="empty-placeholder-icon">💳</div>
						<div style="font-size: 15px; font-weight: 700; margin-bottom: 6px;">请从左侧选择一张油卡查看流水台账</div>
						<div style="font-size: 12px;">或点击左侧“+ 新建油卡”录入您的第一张企业油卡</div>
					</div>

					<div id="main-content-pane" style="display: none; display: flex; flex-direction: column; gap: 14px;">
						
						<!-- Zone 1: 顶部油卡信息栏 -->
						<div class="top-card-header">
							<div class="current-card-meta">
								<span class="meta-card-title" id="disp-card-name">--</span>
								<span class="meta-card-no" id="disp-card-no">--</span>
								<span class="status-pill-subtle status-pill-green" id="disp-card-status">正常</span>
								<span class="meta-card-company" id="disp-card-supplier"></span>
							</div>
						</div>

						<!-- 锁定警示条 (仅在锁定月份展示) -->
						<div class="locked-alert-banner" id="locked-banner" style="display: none;">
							<span>🔒 <b>本月度已核定锁定</b>：该月份单据处于保护状态，禁止新增、修改或删除记录。</span>
							<span id="locked-meta-info" style="font-size: 11.5px; color: #7f1d1d;"></span>
						</div>

						<!-- Zone 1: 5 大财务指标与核定状态看板 (汇总区) -->
						<div class="kpi-cards-grid">
							<!-- 1. 上期结转余额 -->
							<div class="kpi-card kpi-blue">
								<div class="kpi-card-top">
									<span class="kpi-card-label">💰 上期结转余额</span>
									<span class="kpi-card-count">期初</span>
								</div>
								<div class="kpi-card-value" id="kpi-opening-bal">¥ 0.00</div>
								<div class="kpi-card-desc">月初结存金额</div>
							</div>

							<!-- 2. 本期充值总额 -->
							<div class="kpi-card kpi-emerald">
								<div class="kpi-card-top">
									<span class="kpi-card-label">➕ 本期充值总额</span>
									<span class="kpi-card-count" id="kpi-recharge-count">0 笔</span>
								</div>
								<div class="kpi-card-value" id="kpi-recharge-total">¥ 0.00</div>
								<div class="kpi-card-desc" id="kpi-recharge-effective">入卡总额</div>
							</div>

							<!-- 3. 本期加油消费总额 -->
							<div class="kpi-card kpi-amber">
								<div class="kpi-card-top">
									<span class="kpi-card-label">➖ 本期加油消费</span>
									<span class="kpi-card-count" id="kpi-refuel-count">0 次</span>
								</div>
								<div class="kpi-card-value" id="kpi-refuel-total">¥ 0.00</div>
								<div class="kpi-card-desc" id="kpi-refuel-liters">共 0.00 升</div>
							</div>

							<!-- 4. 期末结存余额 -->
							<div class="kpi-card kpi-purple">
								<div class="kpi-card-top">
									<span class="kpi-card-label">🏁 期末结存余额</span>
									<span class="kpi-card-count">月末</span>
								</div>
								<div class="kpi-card-value" id="kpi-ending-bal">¥ 0.00</div>
								<div class="kpi-card-desc">期初 + 充值 - 消费</div>
							</div>

							<!-- 5. 月度核定状态 -->
							<div class="kpi-card kpi-lock-status" id="kpi-lock-card">
								<div class="kpi-card-top">
									<span class="kpi-card-label">🔒 月度核定状态</span>
								</div>
								<div class="kpi-card-value" id="kpi-lock-title" style="font-size: 15px;">未锁定</div>
								<div class="kpi-card-desc" id="kpi-lock-desc">正常录入中</div>
							</div>
						</div>

						<!-- Zone 2: 中间控制中枢工具栏 (汇总区下部、明细区上部) -->
						<div class="middle-command-strip">
							<!-- 左侧：时间筛选与快捷切换 -->
							<div class="time-nav-cluster">
								<span class="time-label">📅 账期:</span>
								<button class="btn-nav-step" id="btn-prev-month" title="上一月">◀ 上月</button>
								<select class="filter-select-prominent" id="sel-year"></select>
								<select class="filter-select-prominent" id="sel-month"></select>
								<button class="btn-nav-step" id="btn-next-month" title="下一月">下月 ▶</button>
								<button class="btn-nav-step" id="btn-this-month" title="回到当月">📅 本月</button>
							</div>

							<!-- 右侧：行内快捷录入与操作中枢 -->
							<div class="actions-cluster">
								<button class="btn-cmd-primary" id="btn-quick-refuel" title="在明细表最后一行快速录入加油">
									<span>⛽</span> 录入加油
								</button>
								<button class="btn-cmd-secondary" id="btn-quick-recharge" title="在明细表最后一行快速录入充值">
									<span>💳</span> 录入充值
								</button>
								<div id="lock-action-container" style="display: inline-block;">
									<!-- 动态渲染【本月核定 / 解锁】按钮 -->
								</div>
								<button class="btn-cmd-secondary" id="btn-refresh-data" title="刷新流水总账">
									<span>🔄</span>
								</button>
							</div>
						</div>

						<!-- Zone 3: 明细区表头 -->
						<div class="table-header-bar">
							<div class="table-title-main">
								<span>📑 油卡资金与能耗流水明细账</span>
								<span class="table-subtitle" id="disp-ledger-subhead"></span>
							</div>
						</div>

						<!-- Zone 3: 单一合流流水总账表格 -->
						<div class="oil-data-table-wrapper">
							<table class="oil-data-table" id="table-unified-ledger">
								<thead>
									<tr id="thead-row">
										<th>日期</th>
										<th>类型</th>
										<th>车辆 / 摘要</th>
										<th>油号</th>
										<th>当前里程</th>
										<th>升数(L)</th>
										<th>变动金额(¥)</th>
										<th class="col-balance">实时余额(¥)</th>
										<!-- 高级列 (管理员可见) -->
										<th class="mgr-col">行驶里程</th>
										<th class="mgr-col">百公里油耗</th>
										<th class="mgr-col">开票</th>
										<th>备注</th>
										<th>操作</th>
									</tr>
								</thead>
								<tbody id="tbody-unified-ledger">
									<!-- 动态渲染首行结转、流水与新增行 -->
								</tbody>
								<tfoot id="tfoot-unified-ledger">
									<!-- 动态合计行 -->
								</tfoot>
							</table>
						</div>

					</div>
				</div>
			</div>
		`);

		this.initFilterDropdowns();
	}

	loadMeta() {
		const self = this;
		frappe.call({
			method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.get_quick_entry_meta",
			callback: function (r) {
				if (r.message) {
					self.meta = r.message;
				}
			},
		});
	}

	initFilterDropdowns() {
		const selYear = this.wrapper.find("#sel-year");
		const selMonth = this.wrapper.find("#sel-month");

		const currentYear = new Date().getFullYear();
		selYear.empty();
		for (let y = currentYear + 1; y >= currentYear - 3; y--) {
			selYear.append(`<option value="${y}" ${y === this.selectedYear ? "selected" : ""}>${y} 年</option>`);
		}

		selMonth.empty();
		for (let m = 1; m <= 12; m++) {
			selMonth.append(`<option value="${m}" ${m === this.selectedMonth ? "selected" : ""}>${m} 月</option>`);
		}
	}

	bindEvents() {
		const self = this;

		// 搜索油卡
		this.wrapper.on("input", "#card-search-input", function () {
			const q = $(this).val().trim().toLowerCase();
			self.filterCardsList(q);
		});

		// 切换油卡
		this.wrapper.on("click", ".oil-card-item", function () {
			const cardName = String($(this).attr("data-name"));
			self.selectCard(cardName);
		});

		// 新建油卡 (单页弹窗，零跳转)
		this.wrapper.on("click", "#btn-create-card", function () {
			self.openCreateOilCardDialog();
		});

		// 删除油卡档案 (单页确认，零跳转)
		this.wrapper.on("click", ".btn-delete-card", function (e) {
			e.stopPropagation();
			const cardId = String($(this).attr("data-name"));
			const cardTitle = String($(this).attr("data-title") || cardId);
			frappe.confirm(
				`确定要彻底删除油卡【<b>${cardTitle}</b>】吗？<br><br><span style="color:#dc2626;">警告：该操作将删除该油卡档案，请确认该卡无未结清账目。</span>`,
				function () {
					frappe.call({
						method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.delete_oil_card",
						args: { oil_card: cardId },
						callback: function (r) {
							if (r.message && r.message.status === "ok") {
								frappe.show_alert({ message: r.message.message, indicator: "green" }, 3);
								if (self.activeCard && String(self.activeCard.name) === cardId) {
									self.activeCard = null;
								}
								self.loadCards();
							}
						},
					});
				}
			);
		});

		// 年月变更
		this.wrapper.on("change", "#sel-year", function () {
			self.selectedYear = parseInt($(this).val());
			self.loadLedgerData();
		});

		this.wrapper.on("change", "#sel-month", function () {
			self.selectedMonth = parseInt($(this).val());
			self.loadLedgerData();
		});

		// 快捷时间切换：上一月
		this.wrapper.on("click", "#btn-prev-month", function () {
			if (self.selectedMonth === 1) {
				self.selectedMonth = 12;
				self.selectedYear -= 1;
			} else {
				self.selectedMonth -= 1;
			}
			self.syncDropdowns();
			self.loadLedgerData();
		});

		// 快捷时间切换：下一月
		this.wrapper.on("click", "#btn-next-month", function () {
			if (self.selectedMonth === 12) {
				self.selectedMonth = 1;
				self.selectedYear += 1;
			} else {
				self.selectedMonth += 1;
			}
			self.syncDropdowns();
			self.loadLedgerData();
		});

		// 快捷时间切换：回到当月
		this.wrapper.on("click", "#btn-this-month", function () {
			const now = new Date();
			self.selectedYear = now.getFullYear();
			self.selectedMonth = now.getMonth() + 1;
			self.syncDropdowns();
			self.loadLedgerData();
		});

		// 刷新按钮
		this.wrapper.on("click", "#btn-refresh-data", function () {
			self.loadLedgerData();
			frappe.show_alert({ message: "流水总账已刷新", indicator: "green" }, 2);
		});

		// 触发【行内快速录入加油】
		this.wrapper.on("click", "#btn-quick-refuel", function () {
			if (!self.activeCard) return;
			if (self.isLocked && !self.isManager) {
				frappe.msgprint("当前月份已核定锁定，非管理员禁止录入记录！");
				return;
			}
			self.startInlineEntry("refuel");
		});

		// 触发【行内快速录入充值】
		this.wrapper.on("click", "#btn-quick-recharge", function () {
			if (!self.activeCard) return;
			if (self.isLocked && !self.isManager) {
				frappe.msgprint("当前月份已核定锁定，非管理员禁止录入记录！");
				return;
			}
			self.startInlineEntry("recharge");
		});

		// 取消行内录入
		this.wrapper.on("click", "#btn-inline-cancel", function () {
			$("#row-inline-entry").remove();
		});

		// 保存行内加油记录
		this.wrapper.on("click", "#btn-inline-save-refuel", function () {
			self.saveInlineRefuel();
		});

		// 保存行内充值记录
		this.wrapper.on("click", "#btn-inline-save-recharge", function () {
			self.saveInlineRecharge();
		});

		// 行内输入计算联动
		this.wrapper.on("input", "#inline-refuel-amount, #inline-refuel-liters, #inline-refuel-odo", function () {
			self.updateInlineRefuelCalculations();
		});

		this.wrapper.on("input", "#inline-recharge-amount, #inline-recharge-bonus", function () {
			self.updateInlineRechargeCalculations();
		});

		// 车辆智能搜索与下拉选项交互
		this.wrapper.on("focus input", "#inline-refuel-vehicle-input", function () {
			const q = $(this).val();
			self.renderVehicleDropdown(q);
		});

		this.wrapper.on("click", ".vehicle-dropdown-item", function () {
			const vehName = $(this).data("name");
			const veh = self.meta.vehicles.find((v) => String(v.name) === String(vehName));
			if (veh) {
				self.applyVehicleToInlineEntry(veh);
			}
		});

		this.wrapper.on("click", "#btn-quick-add-vehicle-from-dropdown", function (e) {
			e.stopPropagation();
			$("#vehicle-autocomplete-dropdown").hide();
			const currentText = $("#inline-refuel-vehicle-input").val();
			self.openCreateVehicleDialog(currentText);
		});

		// 点击其他区域关闭下拉
		$(document).on("click.vehicleDropdown", function (e) {
			if (!$(e.target).closest(".vehicle-combobox-wrapper").length) {
				$("#vehicle-autocomplete-dropdown").hide();
			}
		});

		// 车辆输入框回车：模糊匹配车牌（如9527自动匹配津AF9527）
		this.wrapper.on("keydown", "#inline-refuel-vehicle-input", function (e) {
			if (e.which === 13) {
				e.preventDefault();
				e.stopPropagation();
				const text = $(this).val().trim();
				const match = self.fuzzyMatchVehicle(text);
				if (match) {
					self.applyVehicleToInlineEntry(match);
				} else if (text) {
					$("#vehicle-autocomplete-dropdown").hide();
					self.openCreateVehicleDialog(text);
				}
			}
		});

		// 其它行内输入框回车保存，ESC取消
		this.wrapper.on("keydown", ".row-inline-entry input:not(#inline-refuel-vehicle-input)", function (e) {
			if (e.which === 13) {
				const isRefuel = $("#btn-inline-save-refuel").length > 0;
				if (isRefuel) self.saveInlineRefuel();
				else self.saveInlineRecharge();
			} else if (e.which === 27) {
				$("#row-inline-entry").remove();
			}
		});

		// 本月核定锁定
		this.wrapper.on("click", "#btn-lock-month-action", function () {
			if (!self.activeCard) return;
			frappe.confirm(
				`确定要对【${self.activeCard.card_name}】的 <b>${self.selectedYear}年${self.selectedMonth}月</b> 进行【本月核定与锁定】吗？<br><br><span style="color:#b45309;">核定后该月份流水将被保护，操作员不可再编辑或删除。</span>`,
				function () {
					frappe.call({
						method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.lock_monthly_ledger",
						args: {
							oil_card: self.activeCard.name,
							year: self.selectedYear,
							month: self.selectedMonth,
						},
						callback: function (r) {
							if (r.message && r.message.status === "ok") {
								frappe.show_alert({ message: r.message.message, indicator: "green" }, 4);
								self.loadLedgerData();
							}
						},
					});
				}
			);
		});

		// 解除月度锁定
		this.wrapper.on("click", "#btn-unlock-month-action", function () {
			if (!self.activeCard) return;
			frappe.confirm(
				`确定要解除【${self.activeCard.card_name}】 <b>${self.selectedYear}年${self.selectedMonth}月</b> 的锁定状态吗？`,
				function () {
					frappe.call({
						method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.unlock_monthly_ledger",
						args: {
							oil_card: self.activeCard.name,
							year: self.selectedYear,
							month: self.selectedMonth,
						},
						callback: function (r) {
							if (r.message && r.message.status === "ok") {
								frappe.show_alert({ message: r.message.message, indicator: "orange" }, 4);
								self.loadLedgerData();
							}
						},
					});
				}
			);
		});

		// 删除单笔记录
		this.wrapper.on("click", ".btn-delete-row", function () {
			const docType = $(this).data("doctype");
			const docName = $(this).data("name");

			if (self.isLocked && !self.isManager) {
				frappe.msgprint("当前月份已核定锁定，禁止删除记录！");
				return;
			}

			frappe.confirm(`确定要删除此笔记录 [${docName}] 吗？`, function () {
				frappe.call({
					method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.delete_ledger_record",
					args: {
						doc_type: docType,
						name: docName,
						oil_card: self.activeCard.name,
						year: self.selectedYear,
						month: self.selectedMonth,
					},
					callback: function (r) {
						if (r.message && r.message.status === "ok") {
							frappe.show_alert({ message: "记录已删除", indicator: "green" }, 3);
							self.loadLedgerData();
						}
					},
				});
			});
		});
	}

	startInlineEntry(type) {
		const existing = $("#row-inline-entry");
		if (existing.length > 0) {
			existing.find("input:first").focus();
			return;
		}

		const isMgr = this.isManager;
		const tbody = this.wrapper.find("#tbody-unified-ledger");

		// 默认日期取当前年月合适的时间
		const now = new Date();
		let defaultDate = `${this.selectedYear}-${String(this.selectedMonth).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
		if (this.selectedYear !== now.getFullYear() || this.selectedMonth !== now.getMonth() + 1) {
			defaultDate = `${this.selectedYear}-${String(this.selectedMonth).padStart(2, "0")}-01`;
		}

		let html = "";
		if (type === "refuel") {
			// 加油行内录入 (支持智能模糊匹配车牌、直接输入油号与快捷新建车辆)
			html = `
				<tr id="row-inline-entry" class="row-inline-entry">
					<td>
						<input type="date" id="inline-refuel-date" class="inline-input-sm" value="${defaultDate}" required style="width:115px;">
					</td>
					<td><span class="status-pill-subtle status-pill-amber">⛽ 新增加油</span></td>
					<td style="position:relative;">
						<div class="vehicle-combobox-wrapper">
							<input type="text" id="inline-refuel-vehicle-input" class="inline-input-sm" placeholder="输入车牌/9527..." autocomplete="off" style="width:130px; font-weight:600;" required>
							<input type="hidden" id="inline-refuel-vehicle-val">
							<div id="vehicle-autocomplete-dropdown" class="vehicle-dropdown-popup" style="display:none;"></div>
						</div>
					</td>
					<td>
						<input type="text" id="inline-refuel-grade" class="inline-input-sm" list="fuel-grades-list" placeholder="油号" value="95#" style="width:65px; font-weight:600;">
						<datalist id="fuel-grades-list">
							<option value="92#">92# 汽油</option>
							<option value="95#">95# 汽油</option>
							<option value="98#">98# 汽油</option>
							<option value="0#">0# 柴油</option>
							<option value="-10#">-10# 柴油</option>
							<option value="92">92</option>
							<option value="95">95</option>
							<option value="98">98</option>
							<option value="0">0#</option>
							<option value="柴油">柴油</option>
							<option value="汽油">汽油</option>
						</datalist>
					</td>
					<td>
						<input type="number" id="inline-refuel-odo" class="inline-input-sm" placeholder="当前里程" required style="width:85px;">
					</td>
					<td>
						<input type="number" step="0.01" id="inline-refuel-liters" class="inline-input-sm" placeholder="升数" required style="width:70px;">
					</td>
					<td>
						<input type="number" step="0.01" id="inline-refuel-amount" class="inline-input-sm" placeholder="金额¥" required style="width:80px;">
					</td>
					<td>
						<b id="inline-preview-balance" style="color:#1d4ed8; font-size:12.5px;">${formatMoney(this.currentEndingBalance)}</b>
					</td>
					${isMgr ? `
						<td class="mgr-col" id="inline-preview-dist" style="color:#64748b;">--</td>
						<td class="mgr-col" id="inline-preview-consum" style="color:#64748b;">--</td>
						<td class="mgr-col"><span class="status-pill-subtle status-pill-amber">未开票</span></td>
					` : ""}
					<td>
						<input type="text" id="inline-refuel-remark" class="inline-input-sm" placeholder="备注(选填)" style="width:85px;">
					</td>
					<td style="white-space:nowrap;">
						<button class="btn-save-inline" id="btn-inline-save-refuel" title="保存 (Enter)">💾 保存</button>
						<button class="btn-cancel-inline" id="btn-inline-cancel" title="取消 (Esc)">❌ 取消</button>
					</td>
				</tr>
			`;
		} else {
			// 充值行内录入
			let modeOptions = "";
			this.meta.modes_of_payment.forEach((m) => {
				modeOptions += `<option value="${m}">${m}</option>`;
			});

			html = `
				<tr id="row-inline-entry" class="row-inline-entry">
					<td>
						<input type="date" id="inline-recharge-date" class="inline-input-sm" value="${defaultDate}" required style="width:115px;">
					</td>
					<td><span class="status-pill-subtle status-pill-green">💳 新增充值</span></td>
					<td>
						<select id="inline-recharge-mode" class="inline-input-sm" style="width:120px;">
							${modeOptions}
						</select>
					</td>
					<td>--</td>
					<td>--</td>
					<td>--</td>
					<td>
						<input type="number" step="0.01" id="inline-recharge-amount" class="inline-input-sm" placeholder="+金额¥" required style="width:80px;">
					</td>
					<td>
						<b id="inline-preview-balance" style="color:#059669; font-size:12.5px;">${formatMoney(this.currentEndingBalance)}</b>
					</td>
					${isMgr ? `
						<td class="mgr-col">--</td>
						<td class="mgr-col">--</td>
						<td class="mgr-col">--</td>
					` : ""}
					<td>
						<input type="text" id="inline-recharge-remark" class="inline-input-sm" placeholder="备注(选填)" style="width:85px;">
					</td>
					<td style="white-space:nowrap;">
						<button class="btn-save-inline" id="btn-inline-save-recharge" title="保存 (Enter)">💾 保存</button>
						<button class="btn-cancel-inline" id="btn-inline-cancel" title="取消 (Esc)">❌ 取消</button>
					</td>
				</tr>
			`;
		}

		tbody.append(html);
		const targetInput = type === "refuel" ? $("#inline-refuel-vehicle-input") : $("#inline-recharge-amount");
		targetInput.focus();

		// 滚动到该行
		const tableWrapper = this.wrapper.find(".oil-data-table-wrapper");
		tableWrapper.scrollTop(tableWrapper[0].scrollHeight);
	}

	renderVehicleDropdown(q) {
		const dropdown = $("#vehicle-autocomplete-dropdown");
		const query = (q || "").trim().toLowerCase();
		let matches = this.meta.vehicles || [];
		if (query) {
			matches = matches.filter((v) => {
				const plate = (v.license_plate || v.name || "").toLowerCase();
				const model = (v.model || "").toLowerCase();
				return plate.includes(query) || model.includes(query);
			});
		}

		let itemsHtml = "";
		if (matches.length > 0) {
			matches.forEach((v) => {
				const isDiesel = v.fuel_type === "Diesel" || (v.fuel_type && v.fuel_type.toLowerCase().includes("diesel"));
				const fuelTag = isDiesel ? '<span class="veh-fuel-tag tag-diesel">柴油(0#)</span>' : '<span class="veh-fuel-tag tag-petrol">汽油(95#)</span>';
				const modelTag = v.model ? `<span class="veh-model-tag">${v.model}</span>` : '';
				const odoText = v.last_odometer ? `${v.last_odometer}km` : '0km';

				itemsHtml += `
					<div class="vehicle-dropdown-item" data-name="${v.name}">
						<div class="veh-item-left">
							<span class="veh-plate-text">${v.license_plate || v.name}</span>
							${modelTag}
							${fuelTag}
						</div>
						<div class="veh-item-right">${odoText}</div>
					</div>
				`;
			});
		} else {
			itemsHtml = `<div class="vehicle-dropdown-empty">未匹配到车辆 "${q}"</div>`;
		}

		const fullHtml = `
			<div class="vehicle-dropdown-items-scroll">${itemsHtml}</div>
			<div class="vehicle-dropdown-footer" id="btn-quick-add-vehicle-from-dropdown">
				<span>➕ 快速新建车辆档案...</span>
			</div>
		`;

		dropdown.html(fullHtml).show();
	}

	applyVehicleToInlineEntry(v) {
		if (!v) return;
		$("#inline-refuel-vehicle-input").val(v.license_plate || v.name);
		$("#inline-refuel-vehicle-val").val(v.name);
		$("#vehicle-autocomplete-dropdown").hide();

		// 自动联动推荐动力油号
		const isDiesel = v.fuel_type === "Diesel" || (v.fuel_type && v.fuel_type.toLowerCase().includes("diesel"));
		if (isDiesel) {
			$("#inline-refuel-grade").val("0#");
		} else {
			$("#inline-refuel-grade").val("95#");
		}

		// 提示上期里程
		if (v.last_odometer) {
			$("#inline-refuel-odo").attr("placeholder", `上期:${v.last_odometer}km`);
		}

		this.updateInlineRefuelCalculations();
		$("#inline-refuel-odo").focus();
	}

	fuzzyMatchVehicle(text) {
		if (!text) return null;
		const q = text.trim().toLowerCase();
		let match = this.meta.vehicles.find((v) => (v.license_plate || "").toLowerCase() === q || (v.name || "").toLowerCase() === q);
		if (match) return match;
		match = this.meta.vehicles.find((v) => (v.license_plate || "").toLowerCase().includes(q) || (v.name || "").toLowerCase().includes(q));
		return match || null;
	}

	openCreateVehicleDialog(prefillPlate = "") {
		const self = this;
		const companyDefault = self.meta.default_company || (self.meta.companies && self.meta.companies.length ? self.meta.companies[0].name : "");

		const d = new frappe.ui.Dialog({
			title: __("🚗 快速新建车辆档案"),
			fields: [
				{
					label: __("车牌号码"),
					fieldname: "license_plate",
					fieldtype: "Data",
					reqd: 1,
					default: prefillPlate,
					placeholder: "如：津AF9527、粤B·8888",
				},
				{
					fieldtype: "Column Break",
				},
				{
					label: __("车型分类"),
					fieldname: "vehicle_category",
					fieldtype: "Select",
					options: ["货车 / 卡车", "轿车 / 乘用车", "SUV / 越野车", "商务车 / MPV", "客车 / 大巴", "特种作业车"],
					default: "货车 / 卡车",
					reqd: 1,
				},
				{
					fieldtype: "Section Break",
				},
				{
					label: __("动力燃油类型"),
					fieldname: "fuel_type",
					fieldtype: "Select",
					options: ["Diesel (柴油)", "Petrol (汽油)", "Natural Gas (天然气)", "Electric (纯电/插混)"],
					default: "Diesel (柴油)",
					reqd: 1,
				},
				{
					fieldtype: "Column Break",
				},
				{
					label: __("当前表显里程 (km)"),
					fieldname: "last_odometer",
					fieldtype: "Int",
					default: 0,
					placeholder: "初始里程基准",
				},
				{
					fieldtype: "Section Break",
				},
				{
					fieldname: "fuel_match_alert_html",
					fieldtype: "HTML",
				},
			],
			primary_action_label: __("💾 立即创建车辆"),
			primary_action(values) {
				frappe.call({
					method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.quick_create_vehicle",
					args: {
						license_plate: values.license_plate,
						vehicle_category: values.vehicle_category,
						fuel_type: values.fuel_type,
						last_odometer: values.last_odometer || 0,
						company: companyDefault,
					},
					callback: function (r) {
						if (r.message && r.message.status === "ok") {
							frappe.show_alert({ message: r.message.message, indicator: "green" }, 3);
							d.hide();
							const veh = r.message.vehicle;
							self.meta.vehicles.push(veh);
							self.applyVehicleToInlineEntry(veh);
						}
					},
				});
			},
		});

		function updateFuelWarning() {
			const cat = d.get_value("vehicle_category") || "";
			const fuel = d.get_value("fuel_type") || "";
			const wrapper = d.fields_dict.fuel_match_alert_html.$wrapper;

			let html = "";
			if (cat.includes("货车") || cat.includes("卡车") || cat.includes("特种")) {
				if (fuel.includes("Petrol") || fuel.includes("汽油")) {
					html = `<div style="background:#fef2f2; border:1.5px solid #ef4444; border-radius:6px; padding:9px 12px; color:#b91c1c; font-size:12px; font-weight:700;">
						⚠️ <b>【动力匹配警示】</b>：您选择的车型是【${cat}】，该车型在实际运营中通常为【柴油】动力。请再次核实该车辆是否确为汽油发动机！
					</div>`;
				} else {
					html = `<div style="background:#f0fdf4; border:1px solid #86efac; border-radius:6px; padding:7px 12px; color:#15803d; font-size:11.5px;">
						✓ 动力匹配正常：货车已默认配置为【柴油动力（0#）】。
					</div>`;
				}
			} else if (cat.includes("轿车") || cat.includes("SUV") || cat.includes("商务车")) {
				if (fuel.includes("Diesel") || fuel.includes("柴油")) {
					html = `<div style="background:#fef2f2; border:1.5px solid #ef4444; border-radius:6px; padding:9px 12px; color:#b91c1c; font-size:12px; font-weight:700;">
						⚠️ <b>【动力匹配警示】</b>：您选择的车型是【${cat}】，乘用车通常为【汽油】动力。请再次核实该车辆是否确为柴油动力！
					</div>`;
				} else {
					html = `<div style="background:#f0fdf4; border:1px solid #86efac; border-radius:6px; padding:7px 12px; color:#15803d; font-size:11.5px;">
						✓ 动力匹配正常：乘用车已默认配置为【汽油动力（95#/92#）】。
					</div>`;
				}
			}
			wrapper.html(html);
		}

		// 联动车型与动力
		d.fields_dict.vehicle_category.$input.on("change", function () {
			const cat = $(this).val() || "";
			if (cat.includes("货车") || cat.includes("卡车") || cat.includes("特种")) {
				d.set_value("fuel_type", "Diesel (柴油)");
			} else {
				d.set_value("fuel_type", "Petrol (汽油)");
			}
			updateFuelWarning();
		});

		d.fields_dict.fuel_type.$input.on("change", function () {
			updateFuelWarning();
		});

		d.show();
		updateFuelWarning();
	}

	updateInlineRefuelCalculations() {
		const amt = parseFloat($("#inline-refuel-amount").val()) || 0;
		const lit = parseFloat($("#inline-refuel-liters").val()) || 0;
		const odo = parseFloat($("#inline-refuel-odo").val()) || 0;
		const vehName = $("#inline-refuel-vehicle-val").val() || $("#inline-refuel-vehicle-input").val();

		const previewBal = this.currentEndingBalance - amt;
		$("#inline-preview-balance").text(formatMoney(previewBal));

		if (this.isManager && vehName) {
			const veh = this.meta.vehicles.find((v) => String(v.name) === String(vehName) || String(v.license_plate) === String(vehName));
			if (veh && odo > (veh.last_odometer || 0)) {
				const dist = odo - (veh.last_odometer || 0);
				$("#inline-preview-dist").text(`${dist} km`);
				if (dist > 0 && lit > 0) {
					const consum = ((lit / dist) * 100).toFixed(2);
					$("#inline-preview-consum").text(`${consum} L/100km`);
				} else {
					$("#inline-preview-consum").text("--");
				}
			} else {
				$("#inline-preview-dist").text("--");
				$("#inline-preview-consum").text("--");
			}
		}
	}

	updateInlineRechargeCalculations() {
		const amt = parseFloat($("#inline-recharge-amount").val()) || 0;
		const previewBal = this.currentEndingBalance + amt;
		$("#inline-preview-balance").text(formatMoney(previewBal));
	}

	saveInlineRefuel() {
		const self = this;
		const dateVal = $("#inline-refuel-date").val();
		let vehVal = $("#inline-refuel-vehicle-val").val();
		const vehInput = $("#inline-refuel-vehicle-input").val();
		if (!vehVal && vehInput) {
			const match = self.fuzzyMatchVehicle(vehInput);
			if (match) {
				vehVal = match.name;
			} else {
				vehVal = vehInput;
			}
		}

		const odoVal = $("#inline-refuel-odo").val();
		const litVal = $("#inline-refuel-liters").val();
		const amtVal = $("#inline-refuel-amount").val();
		const gradeVal = $("#inline-refuel-grade").val();
		const remarkVal = $("#inline-refuel-remark").val();

		// 校验必填项
		let hasErr = false;
		$(".inline-input-sm").removeClass("input-invalid");

		if (!dateVal) { $("#inline-refuel-date").addClass("input-invalid"); hasErr = true; }
		if (!vehVal) { $("#inline-refuel-vehicle-input").addClass("input-invalid"); hasErr = true; }
		if (!odoVal || parseFloat(odoVal) <= 0) { $("#inline-refuel-odo").addClass("input-invalid"); hasErr = true; }
		if (!litVal || parseFloat(litVal) <= 0) { $("#inline-refuel-liters").addClass("input-invalid"); hasErr = true; }
		if (!amtVal || parseFloat(amtVal) <= 0) { $("#inline-refuel-amount").addClass("input-invalid"); hasErr = true; }

		if (hasErr) {
			frappe.show_alert({ message: "请完整填写标红的必填项（日期、车辆、当前里程、加油升数与金额）！", indicator: "red" }, 4);
			return;
		}

		frappe.call({
			method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.quick_add_refuel",
			args: {
				oil_card: self.activeCard.name,
				posting_date: dateVal,
				vehicle: vehVal,
				odometer: odoVal,
				liters: litVal,
				amount: amtVal,
				fuel_grade: gradeVal,
				remark: remarkVal,
			},
			callback: function (r) {
				if (r.message && r.message.status === "ok") {
					frappe.show_alert({ message: r.message.message, indicator: "green" }, 3);
					$("#row-inline-entry").remove();
					self.loadLedgerData();
					self.loadMeta(); // 刷新车辆最新里程
				}
			},
		});
	}

	saveInlineRecharge() {
		const self = this;
		const dateVal = $("#inline-recharge-date").val();
		const modeVal = $("#inline-recharge-mode").val();
		const amtVal = $("#inline-recharge-amount").val();
		const remarkVal = $("#inline-recharge-remark").val();

		let hasErr = false;
		$(".inline-input-sm").removeClass("input-invalid");

		if (!dateVal) { $("#inline-recharge-date").addClass("input-invalid"); hasErr = true; }
		if (!amtVal || parseFloat(amtVal) <= 0) { $("#inline-recharge-amount").addClass("input-invalid"); hasErr = true; }

		if (hasErr) {
			frappe.show_alert({ message: "请完整填写标红的必填项（日期与充值金额）！", indicator: "red" }, 4);
			return;
		}

		frappe.call({
			method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.quick_add_recharge",
			args: {
				oil_card: self.activeCard.name,
				posting_date: dateVal,
				recharge_amount: amtVal,
				mode_of_payment: modeVal,
				bonus_amount: 0,
				remark: remarkVal,
			},
			callback: function (r) {
				if (r.message && r.message.status === "ok") {
					frappe.show_alert({ message: r.message.message, indicator: "green" }, 3);
					$("#row-inline-entry").remove();
					self.loadLedgerData();
				}
			},
		});
	}

	syncDropdowns() {
		this.wrapper.find("#sel-year").val(this.selectedYear);
		this.wrapper.find("#sel-month").val(this.selectedMonth);
	}

	openCreateOilCardDialog() {
		const self = this;
		const companyDefault = self.meta.default_company || (self.meta.companies && self.meta.companies.length ? self.meta.companies[0].name : "");

		const d = new frappe.ui.Dialog({
			title: __("💳 新建企业油卡档案"),
			fields: [
				{
					label: __("油卡名称"),
					fieldname: "card_name",
					fieldtype: "Data",
					reqd: 1,
					placeholder: "如：粤B·8888 专车油卡、应急车队副卡",
				},
				{
					fieldtype: "Column Break",
				},
				{
					label: __("卡类型"),
					fieldname: "card_type",
					fieldtype: "Select",
					options: ["主卡", "副卡", "单卡"],
					default: "主卡",
					reqd: 1,
				},
				{
					fieldtype: "Section Break",
				},
				{
					label: __("实体油卡卡号"),
					fieldname: "card_no",
					fieldtype: "Data",
					reqd: 1,
					placeholder: "如：1000118888888888",
				},
				{
					fieldtype: "Column Break",
				},
				{
					label: __("油企 / 供应商"),
					fieldname: "supplier",
					fieldtype: "Link",
					options: "Supplier",
					default: self.meta.default_supplier || "",
					placeholder: "选择或输入油企",
				},
				{
					fieldtype: "Section Break",
				},
				{
					label: __("所属公司"),
					fieldname: "company",
					fieldtype: "Link",
					options: "Company",
					default: companyDefault,
					reqd: 1,
				},
				{
					fieldtype: "Column Break",
				},
				{
					label: __("期初建账余额 (¥)"),
					fieldname: "opening_balance",
					fieldtype: "Currency",
					default: 0,
					description: "建账时的初始可用余额",
				},
			],
			primary_action_label: __("💾 立即创建"),
			primary_action(values) {
				frappe.call({
					method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.quick_create_oil_card",
					args: {
						card_name: values.card_name,
						card_no: values.card_no,
						card_type: values.card_type,
						company: values.company,
						supplier: values.supplier,
						opening_balance: values.opening_balance,
					},
					callback: function (r) {
						if (r.message && r.message.status === "ok") {
							frappe.show_alert({ message: r.message.message, indicator: "green" }, 3);
							d.hide();
							self.loadCards(r.message.name);
						}
					},
				});
			},
		});
		d.show();
	}

	loadCards(targetCardName) {
		const self = this;
		frappe.call({
			method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.get_all_oil_cards",
			callback: function (r) {
				self.cards = r.message || [];
				self.renderCardsList();

				if (self.cards.length > 0) {
					if (targetCardName && self.cards.some((c) => c.name === targetCardName)) {
						self.selectCard(targetCardName);
					} else if (!self.activeCard || !self.cards.some((c) => c.name === self.activeCard.name)) {
						self.selectCard(self.cards[0].name);
					} else {
						self.selectCard(self.activeCard.name);
					}
				} else {
					self.activeCard = null;
					self.wrapper.find("#main-empty-placeholder").show();
					self.wrapper.find("#main-content-pane").hide();
				}
			},
		});
	}

	renderCardsList() {
		const container = this.wrapper.find("#cards-list-container");
		if (this.cards.length === 0) {
			container.html(`
				<div class="empty-placeholder">
					<div class="empty-placeholder-icon">💳</div>
					<div>暂无油卡档案</div>
				</div>
			`);
			return;
		}

		let html = "";
		this.cards.forEach((c) => {
			const strName = String(c.name);
			const isActive = this.activeCard && String(this.activeCard.name) === strName ? "is-active" : "";
			const currentBal = flt(c.current_balance || 0);
			const bal = formatMoney(currentBal);
			const cardNo = c.card_no_masked || c.card_code || "";
			const balClass = currentBal === 0 ? "balance-zero" : "";

			html += `
				<div class="oil-card-item ${isActive}" data-name="${strName}">
					<div class="card-item-top">
						<span class="card-item-name" title="${c.card_name}">${c.card_name}</span>
						<div class="card-top-right-group">
							<span class="card-item-badge">${c.card_type || "油卡"}</span>
							<button type="button" class="btn-delete-card" data-name="${strName}" data-title="${c.card_name}" title="删除油卡档案">
								<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
							</button>
						</div>
					</div>
					<div class="card-item-mid">
						<span>${cardNo}</span>
					</div>
					<div class="card-item-bot">
						<span class="card-item-supplier" title="${c.supplier || c.company || ''}">${c.supplier || c.company || ""}</span>
						<span class="card-item-balance ${balClass}">${bal}</span>
					</div>
				</div>
			`;
		});

		container.html(html);
	}

	filterCardsList(q) {
		this.wrapper.find(".oil-card-item").each(function () {
			const text = $(this).text().toLowerCase();
			if (!q || text.indexOf(q) !== -1) {
				$(this).show();
			} else {
				$(this).hide();
			}
		});
	}

	selectCard(cardName) {
		const strName = String(cardName);
		this.activeCard = this.cards.find((c) => String(c.name) === strName) || null;
		this.wrapper.find(".oil-card-item").removeClass("is-active");
		this.wrapper.find(`.oil-card-item[data-name="${strName}"]`).addClass("is-active");

		if (this.activeCard) {
			this.wrapper.find("#main-empty-placeholder").hide();
			this.wrapper.find("#main-content-pane").show();
			this.loadLedgerData();
		}
	}

	loadLedgerData() {
		if (!this.activeCard) return;

		const self = this;
		frappe.call({
			method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.get_unified_ledger_data",
			args: {
				oil_card: this.activeCard.name,
				year: this.selectedYear,
				month: this.selectedMonth,
			},
			callback: function (r) {
				const data = r.message || {};
				self.renderDashboard(data);
			},
		});
	}

	renderDashboard(data) {
		const card = data.card_info || {};
		const kpis = data.kpis || {};
		const txns = data.transactions || [];
		this.isManager = Boolean(data.is_manager);
		this.isLocked = Boolean(data.is_locked);
		this.currentEndingBalance = flt(kpis.ending_balance || 0);

		// Zone 1: 顶部油卡信息
		this.wrapper.find("#disp-card-name").text(card.card_name || card.name);
		this.wrapper.find("#disp-card-no").text(`卡号: ${card.card_no_masked || card.card_code || "--"}`);
		this.wrapper.find("#disp-card-status").text(card.status === "Active" ? "正常" : (card.status || "正常"));
		this.wrapper.find("#disp-card-supplier").text(`· ${card.supplier || ""}`);
		this.wrapper.find("#disp-ledger-subhead").text(`（${kpis.year}年${kpis.month}月 · 共 ${txns.length} 笔流水 · 实时结余 ${formatMoney(this.currentEndingBalance)}）`);

		// Zone 1: 4 大财务指标
		this.wrapper.find("#kpi-opening-bal").text(formatMoney(kpis.opening_balance || 0));
		this.wrapper.find("#kpi-recharge-total").text(formatMoney(kpis.period_recharge_total || 0));
		this.wrapper.find("#kpi-recharge-count").text(`${kpis.recharge_count || 0} 笔`);
		this.wrapper.find("#kpi-recharge-effective").text(`入卡: ${formatMoney(kpis.period_recharge_total || 0)}`);

		this.wrapper.find("#kpi-refuel-total").text(formatMoney(kpis.period_refuel_total || 0));
		this.wrapper.find("#kpi-refuel-count").text(`${kpis.refuel_count || 0} 次`);
		this.wrapper.find("#kpi-refuel-liters").text(`共 ${(kpis.period_liters || 0).toFixed(2)} L · ${kpis.period_distance || 0}km`);

		this.wrapper.find("#kpi-ending-bal").text(formatMoney(kpis.ending_balance || 0));

		// Zone 1: 月度核定状态卡片 & 中间工具栏操作按钮
		const lockCard = this.wrapper.find("#kpi-lock-card");
		const lockTitle = this.wrapper.find("#kpi-lock-title");
		const lockDesc = this.wrapper.find("#kpi-lock-desc");
		const lockBtnContainer = this.wrapper.find("#lock-action-container");
		const lockedBanner = this.wrapper.find("#locked-banner");

		if (this.isLocked) {
			lockCard.removeClass("is-unlocked").addClass("is-locked");
			lockTitle.text("🔒 已核定锁定").css("color", "#dc2626");
			lockDesc.text("单据受保护 (不可编辑)");
			lockedBanner.show();
			if (data.locked_info) {
				this.wrapper.find("#locked-meta-info").text(`核定人: ${data.locked_info.locked_by} (${data.locked_info.locked_at})`);
			}

			// 管理员可见解锁按钮
			if (this.isManager) {
				lockBtnContainer.html(`<button class="btn-cmd-unlock" id="btn-unlock-month-action"><span>🔓</span> 解除锁定</button>`);
			} else {
				lockBtnContainer.html(`<span class="status-pill-subtle status-pill-red" style="padding:4px 8px;">🔒 本月已锁定</span>`);
			}

			// 禁用快捷录入按钮
			this.wrapper.find("#btn-quick-refuel, #btn-quick-recharge").css("opacity", this.isManager ? "1" : "0.5");
		} else {
			lockCard.removeClass("is-locked").addClass("is-unlocked");
			lockTitle.text("🟢 正常进行中").css("color", "#15803d");
			lockDesc.text("可自由录入/编辑");
			lockedBanner.hide();

			// 管理员可见核定按钮
			if (this.isManager) {
				lockBtnContainer.html(`<button class="btn-cmd-lock" id="btn-lock-month-action"><span>🔒</span> 本月核定</button>`);
			} else {
				lockBtnContainer.html(`<span class="status-pill-subtle status-pill-green" style="padding:4px 8px;">🟢 未锁定</span>`);
			}
			this.wrapper.find("#btn-quick-refuel, #btn-quick-recharge").css("opacity", "1");
		}

		// 管理员高级模块展示
		if (this.isManager) {
			this.wrapper.find(".mgr-col").show();
		} else {
			this.wrapper.find(".mgr-col").hide();
		}

		// Zone 3: 渲染合流流水表格
		this.renderUnifiedTable(txns, kpis);
		this.wrapper.find(".oil-data-table-wrapper").scrollLeft(0);
	}

	renderUnifiedTable(txns, kpis) {
		const tbody = this.wrapper.find("#tbody-unified-ledger");
		const tfoot = this.wrapper.find("#tfoot-unified-ledger");
		const isMgr = this.isManager;
		const isLocked = this.isLocked;

		let html = "";

		// ===== 第 1 行：固定置顶上月结转行 =====
		const openingDate = `${kpis.year}-${String(kpis.month).padStart(2, "0")}-01`;
		const prevMonthDesc = `${kpis.year}年${kpis.month}月结转余额 (上月结转)`;
		const openingBalFmt = formatMoney(kpis.opening_balance || 0);

		html += `
			<tr class="row-opening-balance">
				<td><b>${openingDate}</b></td>
				<td><span class="status-pill-subtle status-pill-gray">期初结存</span></td>
				<td colspan="5"><b>💰 ${prevMonthDesc}</b></td>
				<td><b style="color:#1d4ed8; font-size:13px;">${openingBalFmt}</b></td>
				${isMgr ? '<td class="mgr-col">--</td><td class="mgr-col">--</td><td class="mgr-col">--</td>' : ""}
				<td style="color:#64748b;">月初结存</td>
				<td>--</td>
			</tr>
		`;

		// ===== 后续流水交易行 =====
		if (txns && txns.length > 0) {
			txns.forEach((t) => {
				const isRefuel = t.txn_type === "加油";
				const typePill = isRefuel
					? '<span class="status-pill-subtle status-pill-amber">⛽ 加油</span>'
					: '<span class="status-pill-subtle status-pill-green">💳 充值</span>';

				const amtFmt = isRefuel
					? `<span style="color:#b45309; font-weight:700;">- ${formatMoney(Math.abs(t.change_amount))}</span>`
					: `<span style="color:#047857; font-weight:700;">+ ${formatMoney(t.change_amount)}</span>`;

				const runningBalFmt = `<span style="font-weight:800; color:#0f172a;">${formatMoney(t.running_balance)}</span>`;
				const litersFmt = t.liters ? `${t.liters.toFixed(2)} L` : "--";
				const odoFmt = t.odometer ? `${t.odometer} km` : "--";
				const fuelGrade = t.fuel_grade && t.fuel_grade !== "--" ? `<span class="status-pill-subtle status-pill-blue">${t.fuel_grade}</span>` : "--";

				const targetLink = `<span>${t.target || "--"}</span>`;

				// 高级列内容
				const distFmt = t.distance ? `${t.distance} km` : "--";
				const consumFmt = t.consumption ? `${t.consumption.toFixed(2)} L` : "--";
				const invStatus = t.invoice_status === "已开票" || t.invoice_status === "Invoiced"
					? '<span class="status-pill-subtle status-pill-green">已开票</span>'
					: '<span class="status-pill-subtle status-pill-amber">未开票</span>';

				// 操作列（单页闭环：完全移除离开本页的查看链接，仅保留单页即时删除）
				let actionHtml = '<span style="color:#94a3b8;">--</span>';
				if (!isLocked || isMgr) {
					actionHtml = `<a href="javascript:void(0)" class="btn-delete-row" data-doctype="${t.doc_type}" data-name="${t.name}" style="color:#dc2626; font-weight:600; text-decoration:none; cursor:pointer;" title="删除记录">🗑️ 删除</a>`;
				}

				html += `
					<tr>
						<td>${t.posting_date}</td>
						<td>${typePill}</td>
						<td>${targetLink}</td>
						<td>${fuelGrade}</td>
						<td>${odoFmt}</td>
						<td>${litersFmt}</td>
						<td>${amtFmt}</td>
						<td>${runningBalFmt}</td>
						${isMgr ? `<td class="mgr-col">${distFmt}</td><td class="mgr-col">${consumFmt}</td><td class="mgr-col">${invStatus}</td>` : ""}
						<td style="max-width:120px; overflow:hidden; text-overflow:ellipsis;" title="${t.remark}">${t.remark || "--"}</td>
						<td>${actionHtml}</td>
					</tr>
				`;
			});
		}

		tbody.html(html);

		// ===== 合计行 (tfoot) =====
		const totalLitersFmt = `${(kpis.period_liters || 0).toFixed(2)} L`;
		const netChange = (kpis.period_recharge_total || 0) - (kpis.period_refuel_total || 0);
		const netChangeFmt = netChange >= 0
			? `<span style="color:#047857;">+ ${formatMoney(netChange)}</span>`
			: `<span style="color:#b45309;">- ${formatMoney(Math.abs(netChange))}</span>`;
		const endingBalFmt = formatMoney(kpis.ending_balance || 0);

		tfoot.html(`
			<tr>
				<td colspan="5"><b>本月合计 / 净变动</b></td>
				<td><b>${totalLitersFmt}</b></td>
				<td><b>${netChangeFmt}</b></td>
				<td><b style="color:#6d28d9; font-size:13px;">${endingBalFmt}</b></td>
				${isMgr ? `<td class="mgr-col"><b>${kpis.period_distance || 0} km</b></td><td class="mgr-col"><b>${kpis.avg_consumption || 0} L/100km</b></td><td class="mgr-col">--</td>` : ""}
				<td colspan="2" style="color:#64748b; font-size:11.5px;">充值 ${kpis.recharge_count || 0} 笔 / 加油 ${kpis.refuel_count || 0} 次</td>
			</tr>
		`);

		// 自适应高级列展示
		if (isMgr) {
			this.wrapper.find(".mgr-col").show();
		} else {
			this.wrapper.find(".mgr-col").hide();
		}
	}
}
