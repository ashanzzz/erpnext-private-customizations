# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import io
import json
import calendar
import frappe
from frappe.utils import flt, cint, getdate, nowdate, now_datetime, formatdate

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def get_month_range(year, month):
	"""获取指定年月的起始日期、截止日期与当月总天数"""
	year, month = cint(year), cint(month)
	_, last_day = calendar.monthrange(year, month)
	start_date = f"{year:04d}-{month:02d}-01"
	end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
	return start_date, end_date, last_day


def get_previous_month(year, month):
	"""获取上一个月份 (year, month)"""
	year, month = cint(year), cint(month)
	if month == 1:
		return year - 1, 12
	return year, month - 1


def get_applicable_charge_rate(property_lease_name, target_date):
	"""
	获取指定物业租赁在 target_date 当月生效的收费标准
	通过 effective_from <= target_date 排序取最近版本
	"""
	rates = frappe.get_all(
		"Property Charge Rate",
		filters={
			"property_lease": property_lease_name,
			"enabled": 1,
			"effective_from": ["<=", target_date]
		},
		fields=["*"],
		order_by="effective_from DESC",
		limit=1
	)
	if rates:
		return rates[0]
	return None


def get_previous_meter_reading(meter_name, current_month_start):
	"""
	获取指定水电表在上个月或历史最近一次月结中的本期读数
	如果没有历史月结，则返回该表设置的初始表底数
	"""
	sql = """
		SELECT r.current_reading
		FROM `tabProperty Meter Reading` r
		JOIN `tabProperty Monthly Settlement` s ON r.parent = s.name
		WHERE r.utility_meter = %s
		  AND s.settlement_month < %s
		  AND s.status != '已作废'
		ORDER BY s.settlement_month DESC
		LIMIT 1
	"""
	res = frappe.db.sql(sql, (meter_name, current_month_start), as_dict=True)
	if res and res[0].current_reading is not None:
		return flt(res[0].current_reading)

	meter_doc = frappe.db.get_value("Utility Meter", meter_name, ["initial_reading"], as_dict=True)
	if meter_doc and meter_doc.initial_reading is not None:
		return flt(meter_doc.initial_reading)
	return 0.0


def calculate_settlement_matrix(data):
	"""
	核心集中计算引擎：重算电表、水表、调整项、租赁费（房租+单独物业费多周期）及各公司汇总
	"""
	elec_price = flt(data.get("electricity_price") or 1.1957)
	elec_tax_rate = flt(data.get("electricity_tax_rate") or 13.0)
	water_price = flt(data.get("water_price") or 5.5)
	water_tax_rate = flt(data.get("water_tax_rate") or 9.0)

	settlement_month = str(data.get("settlement_month") or nowdate())
	s_year, s_month = cint(settlement_month.split("-")[0]), cint(settlement_month.split("-")[1])
	_, _, days_in_month = get_month_range(s_year, s_month)

	# 1. 重算抄表明细
	meter_readings = data.get("meter_readings") or []
	for r in meter_readings:
		prev = flt(r.get("previous_reading"))
		curr = flt(r.get("current_reading"))
		mult = flt(r.get("multiplier") or 1.0)
		u_type = r.get("utility_type") or "电"

		raw = max(0.0, curr - prev)
		calc_u = round(raw * mult, 2)

		if u_type == "电":
			price = elec_price
			tax_r = elec_tax_rate
		else:
			price = water_price
			tax_r = water_tax_rate

		amt_incl = round(calc_u * price, 2)
		amt_excl = round(amt_incl / (1.0 + (tax_r / 100.0)), 2)
		tax_amt = round(amt_incl - amt_excl, 2)

		r["raw_usage"] = raw
		r["multiplier"] = mult
		r["calculated_usage"] = calc_u
		r["unit_price"] = price
		r["tax_rate"] = tax_r
		r["amount_tax_incl"] = amt_incl
		r["amount_tax_excl"] = amt_excl
		r["tax_amount"] = tax_amt

	# 2. 重算费用调整明细
	adjustments = data.get("adjustments") or []
	for adj in adjustments:
		adj_type = adj.get("adjustment_type") or "按金额"
		u_type = adj.get("utility_type") or "电费"

		if u_type == "电费":
			curr_price = elec_price
		elif u_type == "水费":
			curr_price = water_price
		else:
			curr_price = 1.0

		if adj_type == "按用量":
			u_adj = flt(adj.get("usage_adjustment"))
			amt_adj = round(u_adj * curr_price, 2)
			eq_u = u_adj
		else:
			amt_adj = flt(adj.get("amount_adjustment"))
			eq_u = round(amt_adj / curr_price, 2) if curr_price > 0 else 0.0

		adj["usage_adjustment"] = flt(adj.get("usage_adjustment"))
		adj["amount_adjustment"] = amt_adj
		adj["equivalent_usage"] = eq_u
		adj["unit_price_snapshot"] = curr_price

	# 3. 重算租赁固定费用 (房租 + 物业费，支持日/月/年多周期自选)
	lease_charges = data.get("lease_charges") or []
	for l_chg in lease_charges:
		area = flt(l_chg.get("area"))
		t_rate = flt(l_chg.get("tax_rate") or 9.0)
		l_days = cint(l_chg.get("billing_days") or days_in_month)

		# 房租核算
		r_ann_amt = flt(l_chg.get("rent_annual_amount"))
		r_daily = flt(l_chg.get("rent_daily_rate"))
		r_mon_amt = flt(l_chg.get("rent_monthly_amount"))

		if r_ann_amt > 0:
			rent_amt = round((r_ann_amt / 365.0) * l_days, 2)
			if area > 0 and not r_daily:
				r_daily = round(r_ann_amt / area / 365.0, 6)
		elif r_daily > 0 and area > 0:
			rent_amt = round(area * r_daily * l_days, 2)
		elif r_mon_amt > 0:
			rent_amt = round(r_mon_amt * (l_days / float(days_in_month)), 2)
		else:
			rent_amt = flt(l_chg.get("rent_amount_tax_incl"))

		# 物业费核算 (若单独计收物业费)
		prop_mode = l_chg.get("property_fee_mode") or "房租含物业"
		p_ann_amt = flt(l_chg.get("property_fee_annual_amount"))
		p_daily = flt(l_chg.get("property_fee_daily_rate"))
		p_mon_amt = flt(l_chg.get("property_fee_monthly_amount"))

		if prop_mode == "单独计收物业费":
			if p_ann_amt > 0:
				prop_fee_amt = round((p_ann_amt / 365.0) * l_days, 2)
				if area > 0 and not p_daily:
					p_daily = round(p_ann_amt / area / 365.0, 6)
			elif p_daily > 0 and area > 0:
				prop_fee_amt = round(area * p_daily * l_days, 2)
			elif p_mon_amt > 0:
				prop_fee_amt = round(p_mon_amt * (l_days / float(days_in_month)), 2)
			else:
				prop_fee_amt = flt(l_chg.get("property_fee_amount_tax_incl"))
		else:
			prop_fee_amt = 0.0

		tot_lease_amt = round(rent_amt + prop_fee_amt, 2)
		amt_excl = round(tot_lease_amt / (1.0 + (t_rate / 100.0)), 2)
		tax_amt = round(tot_lease_amt - amt_excl, 2)

		l_chg["billing_days"] = l_days
		l_chg["rent_amount_tax_incl"] = rent_amt
		l_chg["property_fee_amount_tax_incl"] = prop_fee_amt
		l_chg["amount_tax_incl"] = tot_lease_amt
		l_chg["amount_tax_excl"] = amt_excl
		l_chg["tax_rate"] = t_rate
		l_chg["tax_amount"] = tax_amt

	# 4. 按公司聚合汇总
	all_companies = set()
	for l in lease_charges:
		if l.get("company"):
			all_companies.add(l.get("company"))
	for m in meter_readings:
		if m.get("company"):
			all_companies.add(m.get("company"))
	for a in adjustments:
		if a.get("company"):
			all_companies.add(a.get("company"))
		if a.get("from_company"):
			all_companies.add(a.get("from_company"))
		if a.get("to_company"):
			all_companies.add(a.get("to_company"))

	existing_companies = frappe.get_all("Company", fields=["name"], order_by="name ASC")
	for ec in existing_companies:
		if "吉众" in ec.name or "祺富" in ec.name:
			all_companies.add(ec.name)

	comp_summary_map = {}
	for comp in sorted(all_companies):
		comp_summary_map[comp] = {
			"company": comp,
			"rent_amount": 0.0,
			"property_fee_amount": 0.0,
			"electricity_usage": 0.0,
			"electricity_amount": 0.0,
			"water_usage": 0.0,
			"water_amount": 0.0,
			"adjustment_amount": 0.0,
			"total_amount": 0.0
		}

	# 累加租赁费用
	for l in lease_charges:
		comp = l.get("company")
		if comp in comp_summary_map:
			r_amt = flt(l.get("rent_amount_tax_incl"))
			p_amt = flt(l.get("property_fee_amount_tax_incl"))
			comp_summary_map[comp]["rent_amount"] += r_amt
			comp_summary_map[comp]["property_fee_amount"] += p_amt

	# 累加抄表水电费用
	for m in meter_readings:
		comp = m.get("company")
		if comp in comp_summary_map:
			u_type = m.get("utility_type") or "电"
			u_val = flt(m.get("calculated_usage"))
			amt_val = flt(m.get("amount_tax_incl"))
			if u_type == "电":
				comp_summary_map[comp]["electricity_usage"] += u_val
				comp_summary_map[comp]["electricity_amount"] += amt_val
			else:
				comp_summary_map[comp]["water_usage"] += u_val
				comp_summary_map[comp]["water_amount"] += amt_val

	# 累加调整费用
	for a in adjustments:
		scope = a.get("adjustment_scope") or "公司间转移"
		amt = flt(a.get("amount_adjustment"))
		eq_u = flt(a.get("equivalent_usage"))
		u_type = a.get("utility_type") or "电费"

		if scope == "单公司":
			comp = a.get("company")
			if comp in comp_summary_map:
				comp_summary_map[comp]["adjustment_amount"] += amt
				if u_type == "电费":
					comp_summary_map[comp]["electricity_usage"] += eq_u
					comp_summary_map[comp]["electricity_amount"] += amt
				elif u_type == "水费":
					comp_summary_map[comp]["water_usage"] += eq_u
					comp_summary_map[comp]["water_amount"] += amt
		elif scope == "公司间转移":
			from_c = a.get("from_company")
			to_c = a.get("to_company")
			if from_c in comp_summary_map:
				comp_summary_map[from_c]["adjustment_amount"] -= amt
				if u_type == "电费":
					comp_summary_map[from_c]["electricity_usage"] -= eq_u
					comp_summary_map[from_c]["electricity_amount"] -= amt
				elif u_type == "水费":
					comp_summary_map[from_c]["water_usage"] -= eq_u
					comp_summary_map[from_c]["water_amount"] -= amt
			if to_c in comp_summary_map:
				comp_summary_map[to_c]["adjustment_amount"] += amt
				if u_type == "电费":
					comp_summary_map[to_c]["electricity_usage"] += eq_u
					comp_summary_map[to_c]["electricity_amount"] += amt
				elif u_type == "水费":
					comp_summary_map[to_c]["water_usage"] += eq_u
					comp_summary_map[to_c]["water_amount"] += amt

	company_summaries = []
	grand_total = 0.0
	for comp, s in comp_summary_map.items():
		s["rent_amount"] = round(s["rent_amount"], 2)
		s["property_fee_amount"] = round(s["property_fee_amount"], 2)
		s["electricity_usage"] = round(s["electricity_usage"], 2)
		s["electricity_amount"] = round(s["electricity_amount"], 2)
		s["water_usage"] = round(s["water_usage"], 2)
		s["water_amount"] = round(s["water_amount"], 2)
		s["adjustment_amount"] = round(s["adjustment_amount"], 2)

		tot = round(s["rent_amount"] + s["property_fee_amount"] + s["electricity_amount"] + s["water_amount"], 2)
		s["total_amount"] = tot
		grand_total += tot
		company_summaries.append(s)

	data["meter_readings"] = meter_readings
	data["adjustments"] = adjustments
	data["lease_charges"] = lease_charges
	data["company_summaries"] = company_summaries
	data["total_amount"] = round(grand_total, 2)
	data["property_management_company"] = data.get("property_management_company") or "天津金利达物业管理有限公司"

	return data


def get_month_settlement_data(year, month):
	"""
	获取或构建指定月份的物业月结数据（优先读取数据库，无则自动带出基准并构建草稿视图）
	"""
	year, month = cint(year), cint(month)
	start_date, end_date, days_in_month = get_month_range(year, month)

	doc_name = f"PROP-SET-{start_date}"
	if frappe.db.exists("Property Monthly Settlement", doc_name):
		doc = frappe.get_doc("Property Monthly Settlement", doc_name)
		d = doc.as_dict()
		return calculate_settlement_matrix(d)

	# 数据库中尚无此月份记录，构建新月份草稿数据
	elec_price = 1.1957
	water_price = 5.5

	# 1. 水电表列表及上期表数
	meters = frappe.get_all(
		"Utility Meter",
		filters={"enabled": 1},
		fields=["name", "meter_no", "meter_name", "utility_type", "company", "multiplier", "unit", "initial_reading"],
		order_by="utility_type ASC, meter_no ASC"
	)

	meter_readings = []
	for m in meters:
		prev_reading = get_previous_meter_reading(m.name, start_date)
		meter_readings.append({
			"utility_meter": m.name,
			"meter_no": m.meter_no,
			"utility_type": m.utility_type,
			"company": m.company,
			"previous_reading": prev_reading,
			"current_reading": prev_reading,
			"raw_usage": 0.0,
			"multiplier": flt(m.multiplier or 1.0),
			"calculated_usage": 0.0,
			"unit_price": elec_price if m.utility_type == "电" else water_price,
			"tax_rate": 13.0 if m.utility_type == "电" else 9.0,
			"amount_tax_incl": 0.0,
			"amount_tax_excl": 0.0,
			"tax_amount": 0.0,
			"remark": ""
		})

	# 2. 租赁固定费用及收费标准
	leases = frappe.get_all(
		"Property Lease",
		filters={"enabled": 1},
		fields=["name", "property_name", "company", "area", "property_fee_mode"],
		order_by="company ASC, property_name ASC"
	)

	lease_charges = []
	for l in leases:
		rate = get_applicable_charge_rate(l.name, start_date)
		rent_mode = "按年总金额 (元/年)"
		prop_mode = l.get("property_fee_mode") or "房租含物业"
		r_ann_amt = 0.0
		r_daily = 0.0
		r_mon_amt = 0.0
		r_rate_snap = ""
		p_rate_snap = ""
		p_ann_amt = 0.0
		p_daily = 0.0
		t_rate = 9.0

		if rate:
			rent_mode = rate.rent_pricing_mode or "按年总金额 (元/年)"
			prop_mode = rate.property_fee_mode or "房租含物业"
			r_ann_amt = flt(rate.rent_annual_amount)
			r_daily = flt(rate.rent_daily_rate)
			r_mon_amt = flt(rate.rent_monthly_amount)
			t_rate = flt(rate.rent_tax_rate or 9.0)

			if rent_mode == "按日单价 (元/㎡·天)":
				r_rate_snap = f"¥ {r_daily}/㎡·天"
			elif rent_mode == "按月单价 (元/㎡·月)":
				r_rate_snap = f"¥ {rate.rent_monthly_rate}/㎡·月"
			elif rent_mode == "按年单价 (元/㎡·年)":
				r_rate_snap = f"¥ {rate.rent_annual_rate}/㎡·年"
			elif rent_mode == "按月总金额 (元/月)":
				r_rate_snap = f"¥ {r_mon_amt}/月"
			else:
				r_rate_snap = f"¥ {r_ann_amt}/年"

			if prop_mode == "单独计收物业费":
				p_ann_amt = flt(rate.property_fee_annual_amount)
				p_daily = flt(rate.property_fee_daily_rate)
				p_mode = rate.property_fee_pricing_mode or "按月单价 (元/㎡·月)"
				if p_mode == "按日单价 (元/㎡·天)":
					p_rate_snap = f"¥ {p_daily}/㎡·天"
				elif p_mode == "按月单价 (元/㎡·月)":
					p_rate_snap = f"¥ {rate.property_fee_monthly_rate}/㎡·月"
				elif p_mode == "按年单价 (元/㎡·年)":
					p_rate_snap = f"¥ {rate.property_fee_annual_rate}/㎡·年"
				else:
					p_rate_snap = f"¥ {p_ann_amt}/年"
			else:
				p_rate_snap = "含在房租中"

		lease_charges.append({
			"property_lease": l.name,
			"property_name": l.property_name,
			"company": l.company,
			"area": flt(l.area),
			"property_fee_mode": prop_mode,
			"rent_pricing_mode": rent_mode,
			"billing_days": days_in_month,
			"rent_rate_snapshot": r_rate_snap,
			"property_fee_rate_snapshot": p_rate_snap,
			"rent_annual_amount": r_ann_amt,
			"rent_daily_rate": r_daily,
			"rent_monthly_amount": r_mon_amt,
			"property_fee_annual_amount": p_ann_amt,
			"property_fee_daily_rate": p_daily,
			"tax_rate": t_rate,
			"rent_amount_tax_incl": 0.0,
			"property_fee_amount_tax_incl": 0.0,
			"amount_tax_incl": 0.0,
			"amount_tax_excl": 0.0,
			"tax_amount": 0.0,
			"remark": ""
		})

	data = {
		"name": doc_name,
		"settlement_month": start_date,
		"status": "草稿",
		"is_new": True,
		"property_management_company": "天津金利达物业管理有限公司",
		"electricity_price": elec_price,
		"electricity_tax_rate": 13.0,
		"water_price": water_price,
		"water_tax_rate": 9.0,
		"meter_readings": meter_readings,
		"adjustments": [],
		"lease_charges": lease_charges,
		"company_summaries": [],
		"total_amount": 0.0,
		"remark": ""
	}

	return calculate_settlement_matrix(data)


def save_draft_settlement(data):
	"""
	保存物业月结草稿
	"""
	settlement_month = data.get("settlement_month")
	if not settlement_month:
		frappe.throw("结算月份不能为空")

	doc_name = f"PROP-SET-{settlement_month}"
	calc_data = calculate_settlement_matrix(data)

	if frappe.db.exists("Property Monthly Settlement", doc_name):
		doc = frappe.get_doc("Property Monthly Settlement", doc_name)
		if doc.status == "已结算":
			frappe.throw("当前月份已完成月结锁定，如需修改请先取消结算！")
	else:
		doc = frappe.new_doc("Property Monthly Settlement")
		doc.name = doc_name
		doc.settlement_month = settlement_month

	doc.status = "草稿"
	doc.property_management_company = calc_data.get("property_management_company") or "天津金利达物业管理有限公司"
	doc.electricity_price = flt(calc_data.get("electricity_price"))
	doc.electricity_tax_rate = flt(calc_data.get("electricity_tax_rate"))
	doc.water_price = flt(calc_data.get("water_price"))
	doc.water_tax_rate = flt(calc_data.get("water_tax_rate"))
	doc.total_amount = flt(calc_data.get("total_amount"))
	doc.remark = calc_data.get("remark") or ""

	doc.set("meter_readings", calc_data.get("meter_readings") or [])
	doc.set("adjustments", calc_data.get("adjustments") or [])
	doc.set("lease_charges", calc_data.get("lease_charges") or [])
	doc.set("company_summaries", calc_data.get("company_summaries") or [])

	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"data": calculate_settlement_matrix(doc.as_dict()),
		"message": "物业月结草稿已保存！"
	}


def finalize_monthly_settlement(data):
	"""
	完成本月结算并锁定单据
	"""
	save_res = save_draft_settlement(data)
	doc = frappe.get_doc("Property Monthly Settlement", save_res["name"])

	for r in doc.meter_readings:
		if r.current_reading is None:
			frappe.throw(f"表号 {r.meter_no} ({r.company}) 尚未录入本期读数！")
		if flt(r.current_reading) < flt(r.previous_reading):
			if not r.remark:
				frappe.throw(f"表号 {r.meter_no} 本期读数 ({r.current_reading}) 小于上期读数 ({r.previous_reading})，请在备注中说明换表或修正原因！")

	for adj in doc.adjustments:
		if not adj.reason:
			frappe.throw(f"调整项「{adj.utility_type}」必须填写调整原因！")
		if adj.adjustment_scope == "公司间转移":
			if not adj.from_company or not adj.to_company:
				frappe.throw("公司间转移必须指定转出公司和转入公司！")
			if adj.from_company == adj.to_company:
				frappe.throw("公司间转移的转出公司和转入公司不能相同！")

	doc.status = "已结算"
	doc.settled_by = frappe.session.user
	doc.settled_at = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"data": calculate_settlement_matrix(doc.as_dict()),
		"message": f"🎉 {doc.settlement_month[:7]} 物业月结已成功核定并锁定！"
	}


def revert_settlement_to_draft(name):
	"""
	管理员解锁/取消结算，退回草稿状态
	"""
	doc = frappe.get_doc("Property Monthly Settlement", name)
	doc.status = "草稿"
	doc.settled_by = None
	doc.settled_at = None
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	return {
		"success": True,
		"name": doc.name,
		"data": calculate_settlement_matrix(doc.as_dict()),
		"message": "已解锁并恢复为草稿状态，可重新编辑读数与调整！"
	}


# ─────────────────────────────────────────────────────────────
# Excel 单证导出引擎 (完美对齐《抄表记录.xlsx》祺富单证/吉众单证/合计单证)
# ─────────────────────────────────────────────────────────────

def render_excel_bill_sheet(ws, sheet_title, company_name, settlement_month, prop_mgmt_co, meters, leases, adjustments, summary):
	"""
	渲染符合《抄表记录.xlsx》标准样式的物业明细（单价含税）Sheet
	"""
	ws.title = sheet_title
	ws.views.sheetView[0].showGridLines = True

	font_title = Font(name="微软雅黑", size=14, bold=True)
	font_subtitle = Font(name="微软雅黑", size=11, bold=True)
	font_sec = Font(name="微软雅黑", size=11, bold=True)
	font_header = Font(name="微软雅黑", size=10, bold=True)
	font_data = Font(name="微软雅黑", size=10)
	font_bold = Font(name="微软雅黑", size=10, bold=True)

	fill_header = PatternFill(start_color="F2F4F7", end_color="F2F4F7", fill_type="solid")
	fill_total = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
	fill_grand = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")

	thin_border = Border(
		left=Side(style='thin', color='D0D5DD'),
		right=Side(style='thin', color='D0D5DD'),
		top=Side(style='thin', color='D0D5DD'),
		bottom=Side(style='thin', color='D0D5DD')
	)

	align_center = Alignment(horizontal="center", vertical="center")
	align_left = Alignment(horizontal="left", vertical="center")
	align_right = Alignment(horizontal="right", vertical="center")

	curr_row = 1

	# 1. 标题区
	ws.cell(curr_row, 1, company_name).font = font_title
	curr_row += 1

	ws.cell(curr_row, 1, "物业明细（单价含税）").font = font_subtitle
	curr_row += 1

	# 元数据行
	s_date_str = str(settlement_month)[:10]
	ws.cell(curr_row, 1, "上期日期").font = font_bold
	ws.cell(curr_row, 2, s_date_str)
	ws.cell(curr_row, 3, "本期日期").font = font_bold
	ws.cell(curr_row, 4, s_date_str)
	ws.cell(curr_row, 5, "核定日期").font = font_bold
	ws.cell(curr_row, 6, s_date_str)
	ws.cell(curr_row, 7, "物业公司").font = font_bold
	ws.cell(curr_row, 8, prop_mgmt_co or "天津金利达物业管理有限公司").font = font_bold
	for c in range(1, 9):
		ws.cell(curr_row, c).alignment = align_center if c in [2,4,6] else align_left
	curr_row += 2

	# 2. 电费明细表
	ws.cell(curr_row, 1, "电费").font = font_sec
	curr_row += 1

	elec_headers = ["表号", "上期表数", "本期表数", "本期用电", "倍率", "核定度数", "单价", "总价"]
	for c_idx, h in enumerate(elec_headers, start=1):
		cell = ws.cell(curr_row, c_idx, h)
		cell.font = font_header
		cell.fill = fill_header
		cell.border = thin_border
		cell.alignment = align_center if c_idx in [1, 5] else (align_right if c_idx > 1 else align_left)
	curr_row += 1

	elec_start_row = curr_row
	elec_meters = [m for m in meters if m.get("utility_type") in ["电", "电费"]]
	for m in elec_meters:
		ws.cell(curr_row, 1, str(m.get("meter_no"))).alignment = align_center
		ws.cell(curr_row, 2, float(m.get("previous_reading", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 3, float(m.get("current_reading", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 4, float(m.get("raw_usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 5, float(m.get("multiplier", 1))).alignment = align_center
		ws.cell(curr_row, 6, float(m.get("calculated_usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 7, float(m.get("unit_price", 0))).number_format = "0.0000"
		ws.cell(curr_row, 8, float(m.get("amount_tax_incl", 0))).number_format = "#,##0.00"
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
			if c in [2, 3, 4, 6, 7, 8]:
				ws.cell(curr_row, c).alignment = align_right
		curr_row += 1

	# 电费调整项
	elec_adjs = [a for a in adjustments if a.get("utility_type") in ["电费", "电"]]
	for a in elec_adjs:
		title = a.get("title") or "电费调整"
		ws.cell(curr_row, 1, title).alignment = align_left
		ws.cell(curr_row, 2, "—").alignment = align_center
		ws.cell(curr_row, 3, "—").alignment = align_center
		ws.cell(curr_row, 4, float(a.get("usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 5, 1).alignment = align_center
		ws.cell(curr_row, 6, float(a.get("usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 7, "—").alignment = align_center
		ws.cell(curr_row, 8, float(a.get("amount", 0))).number_format = "#,##0.00"
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
			if c in [4, 6, 8]:
				ws.cell(curr_row, c).alignment = align_right
		curr_row += 1

	if curr_row == elec_start_row:
		# 无数据占位行
		ws.cell(curr_row, 1, "—").alignment = align_center
		for c in range(2, 9):
			ws.cell(curr_row, c, 0).number_format = "#,##0.00"
			ws.cell(curr_row, c).alignment = align_right
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
		curr_row += 1

	# 电费合计行
	ws.cell(curr_row, 1, "合计").alignment = align_center
	ws.cell(curr_row, 4, f"=SUM(D{elec_start_row}:D{curr_row-1})").number_format = "#,##0.00"
	ws.cell(curr_row, 6, f"=SUM(F{elec_start_row}:F{curr_row-1})").number_format = "#,##0.00"
	ws.cell(curr_row, 8, f"=SUM(H{elec_start_row}:H{curr_row-1})").number_format = "#,##0.00"
	for c in range(1, 9):
		ws.cell(curr_row, c).font = font_bold
		ws.cell(curr_row, c).fill = fill_total
		ws.cell(curr_row, c).border = thin_border
		if c in [4, 6, 8]:
			ws.cell(curr_row, c).alignment = align_right
	elec_total_row = curr_row
	curr_row += 2

	# 3. 水费明细表
	ws.cell(curr_row, 1, "水费").font = font_sec
	curr_row += 1

	water_headers = ["表号", "上期表数", "本期表数", "本期用水", "倍率", "核定m³", "单价", "总价"]
	for c_idx, h in enumerate(water_headers, start=1):
		cell = ws.cell(curr_row, c_idx, h)
		cell.font = font_header
		cell.fill = fill_header
		cell.border = thin_border
		cell.alignment = align_center if c_idx in [1, 5] else (align_right if c_idx > 1 else align_left)
	curr_row += 1

	water_start_row = curr_row
	water_meters = [m for m in meters if m.get("utility_type") in ["水", "水费"]]
	for m in water_meters:
		ws.cell(curr_row, 1, str(m.get("meter_no"))).alignment = align_center
		ws.cell(curr_row, 2, float(m.get("previous_reading", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 3, float(m.get("current_reading", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 4, float(m.get("raw_usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 5, float(m.get("multiplier", 1))).alignment = align_center
		ws.cell(curr_row, 6, float(m.get("calculated_usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 7, float(m.get("unit_price", 0))).number_format = "0.0000"
		ws.cell(curr_row, 8, float(m.get("amount_tax_incl", 0))).number_format = "#,##0.00"
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
			if c in [2, 3, 4, 6, 7, 8]:
				ws.cell(curr_row, c).alignment = align_right
		curr_row += 1

	# 水费调整项
	water_adjs = [a for a in adjustments if a.get("utility_type") in ["水费", "水"]]
	for a in water_adjs:
		title = a.get("title") or "水费调整"
		ws.cell(curr_row, 1, title).alignment = align_left
		ws.cell(curr_row, 2, "—").alignment = align_center
		ws.cell(curr_row, 3, "—").alignment = align_center
		ws.cell(curr_row, 4, float(a.get("usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 5, 1).alignment = align_center
		ws.cell(curr_row, 6, float(a.get("usage", 0))).number_format = "#,##0.00"
		ws.cell(curr_row, 7, "—").alignment = align_center
		ws.cell(curr_row, 8, float(a.get("amount", 0))).number_format = "#,##0.00"
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
			if c in [4, 6, 8]:
				ws.cell(curr_row, c).alignment = align_right
		curr_row += 1

	if curr_row == water_start_row:
		ws.cell(curr_row, 1, "—").alignment = align_center
		for c in range(2, 9):
			ws.cell(curr_row, c, 0).number_format = "#,##0.00"
			ws.cell(curr_row, c).alignment = align_right
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
		curr_row += 1

	# 水费合计行
	ws.cell(curr_row, 1, "合计").alignment = align_center
	ws.cell(curr_row, 4, f"=SUM(D{water_start_row}:D{curr_row-1})").number_format = "#,##0.00"
	ws.cell(curr_row, 6, f"=SUM(F{water_start_row}:F{curr_row-1})").number_format = "#,##0.00"
	ws.cell(curr_row, 8, f"=SUM(H{water_start_row}:H{curr_row-1})").number_format = "#,##0.00"
	for c in range(1, 9):
		ws.cell(curr_row, c).font = font_bold
		ws.cell(curr_row, c).fill = fill_total
		ws.cell(curr_row, c).border = thin_border
		if c in [4, 6, 8]:
			ws.cell(curr_row, c).alignment = align_right
	water_total_row = curr_row
	curr_row += 2

	# 4. 房租与物业费明细 (若有)
	lease_total_row = None
	if leases:
		ws.cell(curr_row, 1, "房租与物业费").font = font_sec
		curr_row += 1

		lease_headers = ["场地名称", "面积(㎡)", "计费天数", "房租单价", "物业费计收", "房租金额", "物业费金额", "含税合计"]
		for c_idx, h in enumerate(lease_headers, start=1):
			cell = ws.cell(curr_row, c_idx, h)
			cell.font = font_header
			cell.fill = fill_header
			cell.border = thin_border
			cell.alignment = align_center if c_idx in [3] else (align_right if c_idx in [2, 6, 7, 8] else align_left)
		curr_row += 1

		lease_start_row = curr_row
		for l in leases:
			ws.cell(curr_row, 1, l.get("property_name", "")).alignment = align_left
			ws.cell(curr_row, 2, float(l.get("area", 0))).number_format = "#,##0.00"
			r_snap = l.get("rent_rate_snapshot")
			if not r_snap or str(r_snap).strip() == "None":
				r_snap = "—"
			p_snap = l.get("property_fee_rate_snapshot")
			if not p_snap or str(p_snap).strip() == "None":
				p_snap = "已含在房租中" if l.get("property_fee_mode") != "单独计收物业费" else "—"

			ws.cell(curr_row, 4, str(r_snap)).alignment = align_left
			ws.cell(curr_row, 5, str(p_snap)).alignment = align_left
			ws.cell(curr_row, 6, float(l.get("rent_amount_tax_incl") or 0)).number_format = "#,##0.00"
			ws.cell(curr_row, 7, float(l.get("property_fee_amount_tax_incl") or 0)).number_format = "#,##0.00"
			ws.cell(curr_row, 8, float(l.get("amount_tax_incl") or 0)).number_format = "#,##0.00"
			for c in range(1, 9):
				ws.cell(curr_row, c).font = font_data
				ws.cell(curr_row, c).border = thin_border
				if c in [2, 6, 7, 8]:
					ws.cell(curr_row, c).alignment = align_right
			curr_row += 1

		# 房租合计行
		ws.cell(curr_row, 1, "合计").alignment = align_center
		ws.cell(curr_row, 2, f"=SUM(B{lease_start_row}:B{curr_row-1})").number_format = "#,##0.00"
		ws.cell(curr_row, 6, f"=SUM(F{lease_start_row}:F{curr_row-1})").number_format = "#,##0.00"
		ws.cell(curr_row, 7, f"=SUM(G{lease_start_row}:G{curr_row-1})").number_format = "#,##0.00"
		ws.cell(curr_row, 8, f"=SUM(H{lease_start_row}:H{curr_row-1})").number_format = "#,##0.00"
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_bold
			ws.cell(curr_row, c).fill = fill_total
			ws.cell(curr_row, c).border = thin_border
			if c in [2, 6, 7, 8]:
				ws.cell(curr_row, c).alignment = align_right
		lease_total_row = curr_row
		curr_row += 2

	# 5. 水电与物业综合汇总表
	summary_title = f"{company_name} 合计水电与物业费"
	ws.cell(curr_row, 1, summary_title).font = font_sec
	curr_row += 1

	sum_headers = ["项目", "金额(不含税)", "税率", "税额", "合计(含税)", "数量", "单位", "综合单价"]
	for c_idx, h in enumerate(sum_headers, start=1):
		cell = ws.cell(curr_row, c_idx, h)
		cell.font = font_header
		cell.fill = fill_header
		cell.border = thin_border
		cell.alignment = align_center if c_idx in [3, 7] else (align_right if c_idx in [2, 4, 5, 6, 8] else align_left)
	curr_row += 1

	sum_start_row = curr_row

	# 电费汇总行
	ws.cell(curr_row, 1, "电费").alignment = align_left
	ws.cell(curr_row, 5, f"=H{elec_total_row}").number_format = "#,##0.00"
	ws.cell(curr_row, 3, 0.13).number_format = "0%"
	ws.cell(curr_row, 2, f"=E{curr_row}/(1+C{curr_row})").number_format = "#,##0.00"
	ws.cell(curr_row, 4, f"=E{curr_row}-B{curr_row}").number_format = "#,##0.00"
	ws.cell(curr_row, 6, f"=F{elec_total_row}").number_format = "#,##0.00"
	ws.cell(curr_row, 7, "kWh").alignment = align_center
	ws.cell(curr_row, 8, f"=IF(F{curr_row}>0,E{curr_row}/F{curr_row},0)").number_format = "0.0000"
	for c in range(1, 9):
		ws.cell(curr_row, c).font = font_data
		ws.cell(curr_row, c).border = thin_border
		if c in [2, 4, 5, 6, 8]:
			ws.cell(curr_row, c).alignment = align_right
	curr_row += 1

	# 水费汇总行
	ws.cell(curr_row, 1, "水费").alignment = align_left
	ws.cell(curr_row, 5, f"=H{water_total_row}").number_format = "#,##0.00"
	ws.cell(curr_row, 3, 0.09).number_format = "0%"
	ws.cell(curr_row, 2, f"=E{curr_row}/(1+C{curr_row})").number_format = "#,##0.00"
	ws.cell(curr_row, 4, f"=E{curr_row}-B{curr_row}").number_format = "#,##0.00"
	ws.cell(curr_row, 6, f"=F{water_total_row}").number_format = "#,##0.00"
	ws.cell(curr_row, 7, "m³").alignment = align_center
	ws.cell(curr_row, 8, f"=IF(F{curr_row}>0,E{curr_row}/F{curr_row},0)").number_format = "0.0000"
	for c in range(1, 9):
		ws.cell(curr_row, c).font = font_data
		ws.cell(curr_row, c).border = thin_border
		if c in [2, 4, 5, 6, 8]:
			ws.cell(curr_row, c).alignment = align_right
	curr_row += 1

	# 房租汇总行 (若有)
	if lease_total_row:
		ws.cell(curr_row, 1, "房租").alignment = align_left
		ws.cell(curr_row, 5, f"=F{lease_total_row}").number_format = "#,##0.00"
		ws.cell(curr_row, 3, 0.09).number_format = "0%"
		ws.cell(curr_row, 2, f"=E{curr_row}/(1+C{curr_row})").number_format = "#,##0.00"
		ws.cell(curr_row, 4, f"=E{curr_row}-B{curr_row}").number_format = "#,##0.00"
		ws.cell(curr_row, 6, f"=B{lease_total_row}").number_format = "#,##0.00"
		ws.cell(curr_row, 7, "㎡").alignment = align_center
		ws.cell(curr_row, 8, "—").alignment = align_center
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
			if c in [2, 4, 5, 6]:
				ws.cell(curr_row, c).alignment = align_right
		curr_row += 1

		# 物业费汇总行
		ws.cell(curr_row, 1, "物业费").alignment = align_left
		ws.cell(curr_row, 5, f"=G{lease_total_row}").number_format = "#,##0.00"
		ws.cell(curr_row, 3, 0.09).number_format = "0%"
		ws.cell(curr_row, 2, f"=E{curr_row}/(1+C{curr_row})").number_format = "#,##0.00"
		ws.cell(curr_row, 4, f"=E{curr_row}-B{curr_row}").number_format = "#,##0.00"
		ws.cell(curr_row, 6, f"=B{lease_total_row}").number_format = "#,##0.00"
		ws.cell(curr_row, 7, "㎡").alignment = align_center
		ws.cell(curr_row, 8, "—").alignment = align_center
		for c in range(1, 9):
			ws.cell(curr_row, c).font = font_data
			ws.cell(curr_row, c).border = thin_border
			if c in [2, 4, 5, 6]:
				ws.cell(curr_row, c).alignment = align_right
		curr_row += 1

	# 应付总计行
	ws.cell(curr_row, 1, "应付总计").alignment = align_center
	ws.cell(curr_row, 2, f"=SUM(B{sum_start_row}:B{curr_row-1})").number_format = "#,##0.00"
	ws.cell(curr_row, 3, "—").alignment = align_center
	ws.cell(curr_row, 4, f"=SUM(D{sum_start_row}:D{curr_row-1})").number_format = "#,##0.00"
	ws.cell(curr_row, 5, f"=SUM(E{sum_start_row}:E{curr_row-1})").number_format = "#,##0.00"
	ws.cell(curr_row, 6, "—").alignment = align_center
	ws.cell(curr_row, 7, "—").alignment = align_center
	ws.cell(curr_row, 8, "—").alignment = align_center
	for c in range(1, 9):
		ws.cell(curr_row, c).font = font_bold
		ws.cell(curr_row, c).fill = fill_grand
		ws.cell(curr_row, c).border = thin_border
		if c in [2, 4, 5]:
			ws.cell(curr_row, c).alignment = align_right

	# 自动设置列宽
	col_widths = {1: 18, 2: 14, 3: 14, 4: 14, 5: 12, 6: 15, 7: 15, 8: 16}
	for col_idx, width in col_widths.items():
		col_letter = get_column_letter(col_idx)
		ws.column_dimensions[col_letter].width = width


def generate_settlement_excel_workbook(data, company=None, property_management_company=None, mode="single"):
	"""
	根据月结数据与指定模式生成 openpyxl Workbook
	mode: "company" (单公司) | "total" (全公司合计) | "all" (包含所有分公司与合计的多Sheet工作簿)
	"""
	data = calculate_settlement_matrix(data)
	wb = openpyxl.Workbook()
	# 移除默认第一个空白 sheet
	default_ws = wb.active

	settlement_month = data.get("settlement_month") or nowdate()
	prop_mgmt = property_management_company or data.get("property_management_company") or "天津金利达物业管理有限公司"

	def get_company_data(comp):
		comp_meters = [m for m in (data.get("meter_readings") or []) if m.get("company") == comp]
		comp_leases = [l for l in (data.get("lease_charges") or []) if l.get("company") == comp]
		comp_summary = next((s for s in (data.get("company_summaries") or []) if s.get("company") == comp), {})

		comp_adjs = []
		for a in (data.get("adjustments") or []):
			if a.get("adjustment_scope") == "单公司" and a.get("company") == comp:
				comp_adjs.append({
					"title": f"{a.get('utility_type')}调整",
					"utility_type": a.get("utility_type"),
					"usage": flt(a.get("usage_adjustment")),
					"amount": flt(a.get("amount_adjustment")),
					"reason": a.get("reason")
				})
			elif a.get("adjustment_scope") == "公司间转移":
				if a.get("from_company") == comp:
					comp_adjs.append({
						"title": f"{a.get('utility_type')}调出 (转至 {a.get('to_company')})",
						"utility_type": a.get("utility_type"),
						"usage": -flt(a.get("equivalent_usage")),
						"amount": -flt(a.get("amount_adjustment")),
						"reason": a.get("reason")
					})
				elif a.get("to_company") == comp:
					comp_adjs.append({
						"title": f"{a.get('utility_type')}调入 (来自 {a.get('from_company')})",
						"utility_type": a.get("utility_type"),
						"usage": flt(a.get("equivalent_usage")),
						"amount": flt(a.get("amount_adjustment")),
						"reason": a.get("reason")
					})
		return comp_meters, comp_leases, comp_adjs, comp_summary

	if mode == "company" and company:
		comp_meters, comp_leases, comp_adjs, comp_summary = get_company_data(company)
		sheet_title = f"{company[:2]}单证" if len(company) <= 4 else f"{company}单证"
		render_excel_bill_sheet(default_ws, sheet_title, company, settlement_month, prop_mgmt, comp_meters, comp_leases, comp_adjs, comp_summary)

	elif mode == "total":
		all_meters = data.get("meter_readings") or []
		all_leases = data.get("lease_charges") or []
		# 合计模式下，公司间转移调整两端对冲为 0，单公司调整保留
		total_adjs = []
		for a in (data.get("adjustments") or []):
			if a.get("adjustment_scope") == "单公司":
				total_adjs.append({
					"title": f"{a.get('utility_type')}单项调整 ({a.get('company')})",
					"utility_type": a.get("utility_type"),
					"usage": flt(a.get("usage_adjustment")),
					"amount": flt(a.get("amount_adjustment")),
					"reason": a.get("reason")
				})
		render_excel_bill_sheet(default_ws, "合计单证", "全公司合计", settlement_month, prop_mgmt, all_meters, all_leases, total_adjs, {})

	else: # mode == "all"
		companies = [s.get("company") for s in (data.get("company_summaries") or []) if s.get("company")]
		first_sheet = True
		for comp in companies:
			ws = default_ws if first_sheet else wb.create_sheet()
			first_sheet = False
			sheet_title = f"{comp[:2]}单证" if len(comp) <= 4 else f"{comp}单证"
			comp_meters, comp_leases, comp_adjs, comp_summary = get_company_data(comp)
			render_excel_bill_sheet(ws, sheet_title, comp, settlement_month, prop_mgmt, comp_meters, comp_leases, comp_adjs, comp_summary)

		# 增加合计单证 Sheet
		ws_tot = default_ws if first_sheet else wb.create_sheet()
		all_meters = data.get("meter_readings") or []
		all_leases = data.get("lease_charges") or []
		total_adjs = []
		for a in (data.get("adjustments") or []):
			if a.get("adjustment_scope") == "单公司":
				total_adjs.append({
					"title": f"{a.get('utility_type')}单项调整 ({a.get('company')})",
					"utility_type": a.get("utility_type"),
					"usage": flt(a.get("usage_adjustment")),
					"amount": flt(a.get("amount_adjustment")),
					"reason": a.get("reason")
				})
		render_excel_bill_sheet(ws_tot, "合计单证", "全公司合计", settlement_month, prop_mgmt, all_meters, all_leases, total_adjs, {})

	return wb


@frappe.whitelist()
def export_settlement_excel(settlement_month, company=None, property_management_company=None, mode="company"):
	"""
	Whitelisted API: 下载物业结算明细 Excel
	"""
	settlement_month = str(settlement_month).strip()
	year, month = cint(settlement_month.split("-")[0]), cint(settlement_month.split("-")[1])
	data = get_month_settlement_data(year, month)

	if property_management_company:
		data["property_management_company"] = property_management_company

	wb = generate_settlement_excel_workbook(data, company=company, property_management_company=property_management_company, mode=mode)

	bio = io.BytesIO()
	wb.save(bio)
	bio.seek(0)

	month_str = settlement_month[:7]
	if mode == "company" and company:
		fname = f"{company}_{month_str}_物业明细（单价含税）.xlsx"
	elif mode == "total":
		fname = f"全公司合计_{month_str}_物业明细（单价含税）.xlsx"
	else:
		fname = f"{month_str}_物业及水电结算全套明细（单价含税）.xlsx"

	frappe.response['filename'] = fname
	frappe.response['filecontent'] = bio.getvalue()
	frappe.response['type'] = 'binary'
