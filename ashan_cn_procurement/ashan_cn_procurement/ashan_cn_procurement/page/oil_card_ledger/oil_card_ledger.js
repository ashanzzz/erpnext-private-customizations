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

	new OilCardLedgerConsole(page);
};

class OilCardLedgerConsole {
	constructor(page) {
		this.page = page;
		this.wrapper = $(page.body);
		this.cards = [];
		this.activeCard = null;

		const now = new Date();
		this.selectedYear = now.getFullYear();
		this.selectedMonth = now.getMonth() + 1; // 1 - 12
		this.activeTab = "refuel"; // 'refuel' | 'recharge' | 'invoice'

		this.initLayout();
		this.bindEvents();
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
						<div style="font-size: 15px; font-weight: 700; margin-bottom: 6px;">请从左侧选择一张油卡查看对账台账</div>
						<div style="font-size: 12px;">或点击左侧“+ 新建油卡”录入您的第一张企业油卡</div>
					</div>

					<div id="main-content-pane" style="display: none; display: flex; flex-direction: column; gap: 16px;">
						<!-- 顶部标题与控制工具栏 -->
						<div class="console-header-bar">
							<div class="current-card-meta">
								<span class="meta-card-title" id="disp-card-name">--</span>
								<span class="meta-card-no" id="disp-card-no">--</span>
								<span class="status-pill-subtle status-pill-green" id="disp-card-status">正常</span>
							</div>

							<div class="console-actions-group">
								<select class="filter-select" id="sel-year"></select>
								<select class="filter-select" id="sel-month"></select>

								<button class="btn-action-primary" id="btn-quick-refuel">
									<span>⛽</span> 录入加油
								</button>
								<button class="btn-action-secondary" id="btn-quick-recharge">
									<span>💳</span> 录入充值
								</button>
								<button class="btn-action-secondary" id="btn-refresh-data" title="刷新数据">
									<span>🔄</span>
								</button>
							</div>
						</div>

						<!-- 4 大财务结转指标看板 -->
						<div class="kpi-cards-grid">
							<!-- 1. 期初结存 (上期结转) -->
							<div class="kpi-card kpi-blue">
								<div class="kpi-card-top">
									<span class="kpi-card-label">💰 上期结转余额</span>
									<span class="kpi-card-count" id="kpi-opening-date">期初</span>
								</div>
								<div class="kpi-card-value" id="kpi-opening-bal">¥ 0.00</div>
								<div class="kpi-card-desc">选定月初结存金额</div>
							</div>

							<!-- 2. 本期充值总额 -->
							<div class="kpi-card kpi-emerald">
								<div class="kpi-card-top">
									<span class="kpi-card-label">➕ 本期充值总额</span>
									<span class="kpi-card-count" id="kpi-recharge-count">0 笔</span>
								</div>
								<div class="kpi-card-value" id="kpi-recharge-total">¥ 0.00</div>
								<div class="kpi-card-desc" id="kpi-recharge-effective">实际入卡: ¥ 0.00</div>
							</div>

							<!-- 3. 本期加油消费总额 -->
							<div class="kpi-card kpi-amber">
								<div class="kpi-card-top">
									<span class="kpi-card-label">➖ 本期加油消费</span>
									<span class="kpi-card-count" id="kpi-refuel-count">0 次</span>
								</div>
								<div class="kpi-card-value" id="kpi-refuel-total">¥ 0.00</div>
								<div class="kpi-card-desc" id="kpi-refuel-liters">共 0.00 升 · 0 km</div>
							</div>

							<!-- 4. 期末结存余额 -->
							<div class="kpi-card kpi-purple">
								<div class="kpi-card-top">
									<span class="kpi-card-label">🏁 期末结存余额</span>
									<span class="kpi-card-count" id="kpi-ending-date">月末</span>
								</div>
								<div class="kpi-card-value" id="kpi-ending-bal">¥ 0.00</div>
								<div class="kpi-card-desc">期初 + 充值 - 消费</div>
							</div>
						</div>

						<!-- 标签页导航 -->
						<div class="tabs-header-nav">
							<button class="tab-nav-btn is-active" data-tab="refuel">
								⛽ 加油与能耗记录 (<span id="badge-refuel-count">0</span>)
							</button>
							<button class="tab-nav-btn" data-tab="recharge">
								💳 充值与资金流水 (<span id="badge-recharge-count">0</span>)
							</button>
							<button class="tab-nav-btn" data-tab="invoice">
								🧾 油票与发票开票
							</button>
						</div>

						<!-- 标签页 1：加油明细表格 -->
						<div class="tab-content-pane is-active" id="pane-refuel">
							<div class="oil-data-table-wrapper">
								<table class="oil-data-table" id="table-refuel">
									<thead>
										<tr>
											<th>加油日期</th>
											<th>加油车辆</th>
											<th>油品标号</th>
											<th>当前里程表</th>
											<th>行驶里程</th>
											<th>加油升数</th>
											<th>单价</th>
											<th>消费金额</th>
											<th>百公里油耗</th>
											<th>开票状态</th>
											<th>备注</th>
											<th>操作</th>
										</tr>
									</thead>
									<tbody id="tbody-refuel">
										<tr><td colspan="12" class="empty-placeholder">暂无加油记录</td></tr>
									</tbody>
									<tfoot id="tfoot-refuel" style="display: none;">
										<tr>
											<td colspan="4"><b>合计</b></td>
											<td id="tot-distance">0 km</td>
											<td id="tot-liters">0.00 L</td>
											<td>--</td>
											<td id="tot-amount" style="color:#b45309; font-weight:800;">¥ 0.00</td>
											<td id="tot-avg-consumption">0.00 L/100km</td>
											<td colspan="3"></td>
										</tr>
									</tfoot>
								</table>
							</div>
						</div>

						<!-- 标签页 2：充值流水表格 -->
						<div class="tab-content-pane" id="pane-recharge">
							<div class="oil-data-table-wrapper">
								<table class="oil-data-table" id="table-recharge">
									<thead>
										<tr>
											<th>充值日期</th>
											<th>交易类型</th>
											<th>充值金额</th>
											<th>赠送金额</th>
											<th>实际入卡</th>
											<th>付款方式</th>
											<th>流水凭证号</th>
											<th>状态</th>
											<th>备注</th>
											<th>操作</th>
										</tr>
									</thead>
									<tbody id="tbody-recharge">
										<tr><td colspan="10" class="empty-placeholder">暂无充值流水</td></tr>
									</tbody>
									<tfoot id="tfoot-recharge" style="display: none;">
										<tr>
											<td colspan="2"><b>合计</b></td>
											<td id="tot-recharge-amt" style="font-weight:800;">¥ 0.00</td>
											<td id="tot-bonus-amt">¥ 0.00</td>
											<td id="tot-effective-amt" style="color:#047857; font-weight:800;">¥ 0.00</td>
											<td colspan="5"></td>
										</tr>
									</tfoot>
								</table>
							</div>
						</div>

						<!-- 标签页 3：油票开票与发票关联 -->
						<div class="tab-content-pane" id="pane-invoice">
							<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; text-align: center;">
								<div style="font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 6px;">🧾 月度油票批量开票</div>
								<div style="font-size: 12px; color: #64748b; margin-bottom: 16px;">
									当前油卡未开票总额：<b id="disp-uninvoiced-amt" style="color:#dc2626; font-size:14px;">¥ 0.00</b>
								</div>
								<button class="btn-action-primary" id="btn-goto-batch-invoice" style="padding: 8px 18px; font-size: 13px;">
									<span>📑</span> 打开油票批量录入向导 ➔
								</button>
							</div>
						</div>

					</div>
				</div>
			</div>
		`);

		this.initFilterDropdowns();
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
		selMonth.append(`<option value="0">全年汇总</option>`);
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
			const cardName = $(this).data("name");
			self.selectCard(cardName);
		});

		// 新建油卡
		this.wrapper.on("click", "#btn-create-card", function () {
			frappe.new_doc("Oil Card");
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

		// 刷新按钮
		this.wrapper.on("click", "#btn-refresh-data", function () {
			self.loadLedgerData();
			frappe.show_alert({ message: "台账数据已更新", indicator: "green" }, 3);
		});

		// 录入加油
		this.wrapper.on("click", "#btn-quick-refuel", function () {
			if (!self.activeCard) return;
			frappe.new_doc("Oil Card Refuel Log", {
				oil_card: self.activeCard.name,
				company: self.activeCard.company,
				supplier: self.activeCard.supplier,
			});
		});

		// 录入充值
		this.wrapper.on("click", "#btn-quick-recharge", function () {
			if (!self.activeCard) return;
			frappe.new_doc("Oil Card Recharge", {
				oil_card: self.activeCard.name,
				company: self.activeCard.company,
				supplier: self.activeCard.supplier,
			});
		});

		// 标签页切换
		this.wrapper.on("click", ".tab-nav-btn", function () {
			const tab = $(this).data("tab");
			self.wrapper.find(".tab-nav-btn").removeClass("is-active");
			$(this).addClass("is-active");

			self.wrapper.find(".tab-content-pane").removeClass("is-active");
			self.wrapper.find(`#pane-${tab}`).addClass("is-active");
			self.activeTab = tab;
		});

		// 前往油票批量录入
		this.wrapper.on("click", "#btn-goto-batch-invoice", function () {
			if (self.activeCard) {
				frappe.set_route("List", "Oil Card Invoice Batch", { oil_card: self.activeCard.name });
			} else {
				frappe.set_route("List", "Oil Card Invoice Batch");
			}
		});
	}

	loadCards() {
		const self = this;
		frappe.call({
			method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.get_all_oil_cards",
			callback: function (r) {
				self.cards = r.message || [];
				self.renderCardsList();

				if (self.cards.length > 0) {
					if (!self.activeCard) {
						self.selectCard(self.cards[0].name);
					}
				} else {
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
			const isActive = this.activeCard && this.activeCard.name === c.name ? "is-active" : "";
			const bal = formatMoney(c.current_balance || 0);
			const cardNo = c.card_no_masked || c.card_code || "";

			html += `
				<div class="oil-card-item ${isActive}" data-name="${c.name}">
					<div class="card-item-top">
						<span class="card-item-name" title="${c.card_name}">${c.card_name}</span>
						<span class="card-item-badge">${c.card_type || "油卡"}</span>
					</div>
					<div class="card-item-mid">
						<span>${cardNo}</span>
					</div>
					<div class="card-item-bot">
						<span class="card-item-supplier">${c.supplier || ""}</span>
						<span class="card-item-balance">${bal}</span>
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
		this.activeCard = this.cards.find((c) => c.name === cardName) || null;
		this.wrapper.find(".oil-card-item").removeClass("is-active");
		this.wrapper.find(`.oil-card-item[data-name="${cardName}"]`).addClass("is-active");

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
			method: "ashan_cn_procurement.ashan_cn_procurement.page.oil_card_ledger.oil_card_ledger.get_oil_card_ledger_data",
			args: {
				oil_card: this.activeCard.name,
				year: this.selectedYear,
				month: this.selectedMonth,
			},
			callback: function (r) {
				const data = r.message || {};
				self.renderLedgerDashboard(data);
			},
		});
	}

	renderLedgerDashboard(data) {
		const card = data.card_info || {};
		const kpis = data.kpis || {};
		const refuels = data.refuels || [];
		const recharges = data.recharges || [];

		// 顶部卡片基本信息
		this.wrapper.find("#disp-card-name").text(card.card_name || card.name);
		this.wrapper.find("#disp-card-no").text(`卡号: ${card.card_no_masked || card.card_code || "--"}`);
		this.wrapper.find("#disp-card-status").text(card.status === "Active" ? "正常" : (card.status || "正常"));
		this.wrapper.find("#disp-uninvoiced-amt").text(formatMoney(card.uninvoiced_amount || 0));

		// 4 大 KPI
		this.wrapper.find("#kpi-opening-bal").text(formatMoney(kpis.opening_balance || 0));
		this.wrapper.find("#kpi-recharge-total").text(formatMoney(kpis.period_recharge_amount || 0));
		this.wrapper.find("#kpi-recharge-count").text(`${kpis.recharge_count || 0} 笔`);
		this.wrapper.find("#kpi-recharge-effective").text(`实际入卡: ${formatMoney(kpis.period_effective_recharge || 0)}`);

		this.wrapper.find("#kpi-refuel-total").text(formatMoney(kpis.period_refuel_amount || 0));
		this.wrapper.find("#kpi-refuel-count").text(`${kpis.refuel_count || 0} 次`);
		this.wrapper.find("#kpi-refuel-liters").text(`共 ${(kpis.period_liters || 0).toFixed(2)} L · ${kpis.period_distance || 0} km`);

		this.wrapper.find("#kpi-ending-bal").text(formatMoney(kpis.ending_balance || 0));

		// 标签数量
		this.wrapper.find("#badge-refuel-count").text(refuels.length);
		this.wrapper.find("#badge-recharge-count").text(recharges.length);

		// 渲染表格
		this.renderRefuelTable(refuels, kpis);
		this.renderRechargeTable(recharges, kpis);
	}

	renderRefuelTable(refuels, kpis) {
		const tbody = this.wrapper.find("#tbody-refuel");
		const tfoot = this.wrapper.find("#tfoot-refuel");

		if (!refuels || refuels.length === 0) {
			tbody.html(`<tr><td colspan="12" class="empty-placeholder">该月份暂无加油与能耗记录</td></tr>`);
			tfoot.hide();
			return;
		}

		let html = "";
		refuels.forEach((f) => {
			const amt = formatMoney(f.amount || 0);
			const unitPrice = f.unit_price ? `¥ ${f.unit_price.toFixed(2)}` : "--";
			const consumption = f.liter_per_100km ? `${f.liter_per_100km.toFixed(2)} L` : "--";
			const dist = f.distance_since_last ? `${f.distance_since_last} km` : "--";

			html += `
				<tr>
					<td><b>${f.posting_date || ""}</b></td>
					<td><a href="/desk/vehicle/${f.vehicle}" onclick="frappe.set_route('Form', 'Vehicle', '${f.vehicle}'); return false;">${f.vehicle || ""}</a></td>
					<td><span class="status-pill-subtle status-pill-blue">${f.fuel_grade || ""}</span></td>
					<td>${f.odometer || "--"} km</td>
					<td>${dist}</td>
					<td>${(f.liters || 0).toFixed(2)} L</td>
					<td>${unitPrice}</td>
					<td style="font-weight:700; color:#b45309;">${amt}</td>
					<td>${consumption}</td>
					<td>${f.invoice_status === "Invoiced" ? '<span class="status-pill-subtle status-pill-green">已开票</span>' : '<span class="status-pill-subtle status-pill-amber">未开票</span>'}</td>
					<td style="max-width:120px; overflow:hidden; text-overflow:ellipsis;" title="${f.remark || ""}">${f.remark || "--"}</td>
					<td>
						<a href="/desk/oil-card-refuel-log/${f.name}" style="color:#2563eb; font-weight:600;" onclick="frappe.set_route('Form', 'Oil Card Refuel Log', '${f.name}'); return false;">查看</a>
					</td>
				</tr>
			`;
		});

		tbody.html(html);

		// 合计行
		tfoot.show();
		this.wrapper.find("#tot-distance").text(`${kpis.period_distance || 0} km`);
		this.wrapper.find("#tot-liters").text(`${(kpis.period_liters || 0).toFixed(2)} L`);
		this.wrapper.find("#tot-amount").text(formatMoney(kpis.period_refuel_amount || 0));
		this.wrapper.find("#tot-avg-consumption").text(`${kpis.avg_liter_per_100km || 0} L/100km`);
	}

	renderRechargeTable(recharges, kpis) {
		const tbody = this.wrapper.find("#tbody-recharge");
		const tfoot = this.wrapper.find("#tfoot-recharge");

		if (!recharges || recharges.length === 0) {
			tbody.html(`<tr><td colspan="10" class="empty-placeholder">该月份暂无充值与资金流水</td></tr>`);
			tfoot.hide();
			return;
		}

		let html = "";
		recharges.forEach((r) => {
			const amt = formatMoney(r.recharge_amount || 0);
			const bonus = r.bonus_amount ? formatMoney(r.bonus_amount) : "¥ 0.00";
			const effective = formatMoney(r.effective_amount || r.recharge_amount || 0);

			html += `
				<tr>
					<td><b>${r.posting_date || ""}</b></td>
					<td><span class="status-pill-subtle status-pill-blue">${r.transaction_type || "充值"}</span></td>
					<td style="font-weight:700;">${amt}</td>
					<td>${bonus}</td>
					<td style="font-weight:700; color:#047857;">${effective}</td>
					<td>${r.mode_of_payment || "--"}</td>
					<td>${r.reference_no || "--"}</td>
					<td><span class="status-pill-subtle status-pill-green">${r.status || "已生效"}</span></td>
					<td style="max-width:120px; overflow:hidden; text-overflow:ellipsis;" title="${r.remark || ""}">${r.remark || "--"}</td>
					<td>
						<a href="/desk/oil-card-recharge/${r.name}" style="color:#2563eb; font-weight:600;" onclick="frappe.set_route('Form', 'Oil Card Recharge', '${r.name}'); return false;">查看</a>
					</td>
				</tr>
			`;
		});

		tbody.html(html);

		// 合计行
		tfoot.show();
		this.wrapper.find("#tot-recharge-amt").text(formatMoney(kpis.period_recharge_amount || 0));
		this.wrapper.find("#tot-bonus-amt").text(formatMoney(kpis.period_bonus_amount || 0));
		this.wrapper.find("#tot-effective-amt").text(formatMoney(kpis.period_effective_recharge || 0));
	}
}
