// Copyright (c) 2026, Ashan CN Procurement and contributors
// For license information, please see license.txt

frappe.ui.form.on("Special Equipment", {
	refresh(frm) {
		render_equipment_header_and_cards(frm);
		setup_custom_buttons(frm);
	},
});

function get_status_badge(status) {
	let color = "gray";
	let bg = "#edf2f7";
	let textColor = "#4a5568";

	if (status === "正常") {
		bg = "#c6f6d5";
		textColor = "#22543d";
	} else if (status === "注意") {
		bg = "#feebc8";
		textColor = "#7b341e";
	} else if (status === "即将到期") {
		bg = "#feebc8";
		textColor = "#c05621";
	} else if (status === "今日到期" || status === "已逾期") {
		bg = "#fed7d7";
		textColor = "#9b2c2c";
	} else if (status === "待录入" || status === "待检查") {
		bg = "#edf2f7";
		textColor = "#4a5568";
	}

	return `<span style="display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:bold; background:${bg}; color:${textColor};">${status || "未知"}</span>`;
}

function render_equipment_header_and_cards(frm) {
	if (frm.is_new()) {
		frm.dashboard.clear_headline();
		return;
	}

	const doc = frm.doc;
	const plate = doc.plate_number || doc.internal_number || doc.name;
	const variety = doc.equipment_variety ? ` / ${doc.equipment_variety}` : "";
	const category = doc.equipment_category || "特种设备";
	const eqName = doc.equipment_name || "";
	const statusBadge = doc.equipment_status === "在用"
		? `<span style="color:#38a169; font-weight:bold; font-size:14px;">● 在用</span>`
		: `<span style="color:#e53e3e; font-weight:bold; font-size:14px;">● ${doc.equipment_status || "停用"}</span>`;

	// 法定检验卡数据
	let inspValidity = doc.inspection_valid_until || "未录入";
	if (doc.inspection_due_date_precision === "仅到月份" && doc.inspection_valid_until_month) {
		inspValidity = `报告载明：${doc.inspection_valid_until_month}<br><small style="color:#718096;">系统提醒基准：${doc.inspection_reminder_due_date || ""}</small>`;
	}
	const inspDays = doc.inspection_days_remaining !== undefined && doc.inspection_days_remaining !== null
		? (doc.inspection_days_remaining < 0
			? `<span style="color:#e53e3e; font-weight:bold;">已逾期 ${Math.abs(doc.inspection_days_remaining)} 天</span>`
			: `<span style="font-weight:bold;">${doc.inspection_days_remaining} 天</span>`)
		: "—";

	let inspReportBtn = "";
	if (doc.latest_inspection_attachment) {
		inspReportBtn = `<a href="${doc.latest_inspection_attachment}" target="_blank" class="btn btn-xs btn-default" style="margin-right:6px;">📄 查看报告</a>`;
	}

	// 年度检查卡数据
	const annualDue = doc.annual_check_due_date || "未录入";
	const annualDays = doc.annual_days_remaining !== undefined && doc.annual_days_remaining !== null
		? (doc.annual_days_remaining < 0
			? `<span style="color:#e53e3e; font-weight:bold;">已逾期 ${Math.abs(doc.annual_days_remaining)} 天</span>`
			: `<span style="font-weight:bold;">${doc.annual_days_remaining} 天</span>`)
		: "—";

	let annualReportBtn = "";
	if (doc.latest_annual_check_attachment) {
		annualReportBtn = `<a href="${doc.latest_annual_check_attachment}" target="_blank" class="btn btn-xs btn-default" style="margin-right:6px;">📋 查看记录</a>`;
	}

	const html = `
	<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:16px; margin-bottom:15px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
		<!-- 设备身份标题行 -->
		<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #edf2f7; padding-bottom:10px; margin-bottom:14px;">
			<div>
				<div style="font-size:18px; font-weight:bold; color:#1a202c; display:flex; align-items:center; gap:8px;">
					<span>🚗 ${plate}</span>
					<span style="color:#4a5568; font-weight:normal; font-size:15px;">${doc.internal_number ? doc.internal_number + ' · ' : ''}${eqName}</span>
				</div>
				<div style="font-size:12px; color:#718096; margin-top:2px;">
					${category}${variety} &nbsp;|&nbsp; 所属公司: <b>${doc.company || ""}</b> &nbsp;|&nbsp; 使用地点: ${doc.use_location || "未指定"}
				</div>
			</div>
			<div>
				${statusBadge}
			</div>
		</div>

		<!-- 双状态核心卡片 -->
		<div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
			<!-- 法定检验卡 -->
			<div style="background:#f7fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px 14px; position:relative;">
				<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
					<span style="font-weight:bold; color:#2b6cb0; font-size:14px;">🛡️ 法定检验 (特检院/机构)</span>
					${get_status_badge(doc.inspection_status)}
				</div>
				<div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:12px; color:#4a5568; margin-bottom:10px;">
					<div>最近检验：<b>${doc.latest_inspection_date || "无记录"}</b></div>
					<div>剩余天数：<b>${inspDays}</b></div>
					<div style="grid-column: span 2;">有效期至：<b>${inspValidity}</b></div>
				</div>
				<div style="display:flex; justify-content:flex-end; gap:6px; border-top:1px dashed #e2e8f0; padding-top:8px;">
					${inspReportBtn}
					<button class="btn btn-xs btn-primary btn-add-inspection">➕ 新增检验</button>
				</div>
			</div>

			<!-- 年度检查卡 -->
			<div style="background:#f7fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px 14px; position:relative;">
				<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
					<span style="font-weight:bold; color:#2c7a7b; font-size:14px;">📋 年度检查 (企业自查)</span>
					${get_status_badge(doc.annual_check_status)}
				</div>
				<div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; font-size:12px; color:#4a5568; margin-bottom:10px;">
					<div>最近检查：<b>${doc.latest_annual_check_date || "无记录"}</b></div>
					<div>剩余天数：<b>${annualDays}</b></div>
					<div style="grid-column: span 2;">下次检查：<b>${annualDue}</b></div>
				</div>
				<div style="display:flex; justify-content:flex-end; gap:6px; border-top:1px dashed #e2e8f0; padding-top:8px;">
					${annualReportBtn}
					<button class="btn btn-xs btn-primary btn-add-annual">➕ 新增年检</button>
				</div>
			</div>
		</div>
	</div>
	`;

	frm.dashboard.set_headline(html);

	// 绑定卡片内按钮事件
	frm.dashboard.wrapper.find(".btn-add-inspection").on("click", function() {
		frappe.new_doc("Special Equipment Inspection", {
			special_equipment: frm.doc.name,
			company: frm.doc.company,
		});
	});

	frm.dashboard.wrapper.find(".btn-add-annual").on("click", function() {
		frappe.new_doc("Special Equipment Annual Inspection", {
			special_equipment: frm.doc.name,
			company: frm.doc.company,
			inspection_year: new Date().getFullYear(),
		});
	});
}

function setup_custom_buttons(frm) {
	if (frm.is_new()) return;

	frm.add_custom_button(__("➕ 新增法定检验"), function() {
		frappe.new_doc("Special Equipment Inspection", {
			special_equipment: frm.doc.name,
			company: frm.doc.company,
		});
	}, __("业务操作"));

	frm.add_custom_button(__("➕ 新增年度检查"), function() {
		frappe.new_doc("Special Equipment Annual Inspection", {
			special_equipment: frm.doc.name,
			company: frm.doc.company,
			inspection_year: new Date().getFullYear(),
		});
	}, __("业务操作"));

	frm.add_custom_button(__("📜 查看法定检验历史"), function() {
		frappe.set_route("List", "Special Equipment Inspection", {
			special_equipment: frm.doc.name,
		});
	}, __("历史记录"));

	frm.add_custom_button(__("📑 查看年度检查历史"), function() {
		frappe.set_route("List", "Special Equipment Annual Inspection", {
			special_equipment: frm.doc.name,
		});
	}, __("历史记录"));
}
