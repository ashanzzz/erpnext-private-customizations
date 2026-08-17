# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import calendar
import frappe
from frappe.utils import flt, cint, getdate, nowdate, now_datetime, formatdate


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
	# 查询在当前月份之前已结算或存在的月结抄表记录
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

	# 找不到历史月结，读取表的初始读数
	meter_doc = frappe.db.get_value("Utility Meter", meter_name, ["initial_reading"], as_dict=True)
	if meter_doc and meter_doc.initial_reading is not None:
		return flt(meter_doc.initial_reading)
	return 0.0


def calculate_settlement_matrix(data):
	"""
	核心集中计算引擎：重算电表、水表、调整项、租赁费及各公司汇总
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

	# 3. 重算租赁固定费用
	lease_charges = data.get("lease_charges") or []
	for l_chg in lease_charges:
		area = flt(l_chg.get("area"))
		b_method = l_chg.get("billing_method") or "年金额"
		t_rate = flt(l_chg.get("tax_rate") or 9.0)
		l_days = cint(l_chg.get("billing_days") or days_in_month)

		daily_rate = flt(l_chg.get("daily_rate_snapshot"))
		annual_amt = flt(l_chg.get("annual_amount_snapshot"))

		if b_method == "年金额" and annual_amt > 0:
			if area > 0:
				daily_rate = round(annual_amt / area / 365.0, 6)
				l_chg["daily_rate_snapshot"] = daily_rate
			amt_incl = round((annual_amt / 365.0) * l_days, 2)
		elif daily_rate > 0 and area > 0:
			amt_incl = round(area * daily_rate * l_days, 2)
		elif annual_amt > 0:
			amt_incl = round(annual_amt / 12.0, 2)
		else:
			amt_incl = flt(l_chg.get("amount_tax_incl"))

		amt_excl = round(amt_incl / (1.0 + (t_rate / 100.0)), 2)
		tax_amt = round(amt_incl - amt_excl, 2)

		l_chg["billing_days"] = l_days
		l_chg["amount_tax_incl"] = amt_incl
		l_chg["amount_tax_excl"] = amt_excl
		l_chg["tax_rate"] = t_rate
		l_chg["tax_amount"] = tax_amt

	# 4. 按公司聚合汇总
	# 收集所有涉及的公司
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

	# 保证吉众和祺富若存在则默认列入
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
			c_item = l.get("charge_item") or ""
			amt = flt(l.get("amount_tax_incl"))
			if "物业" in c_item and "房租" not in c_item:
				comp_summary_map[comp]["property_fee_amount"] += amt
			else:
				comp_summary_map[comp]["rent_amount"] += amt

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
			# 转出公司：费用减少 / 转入公司：费用增加
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
		fields=["name", "property_name", "company", "area", "charge_item", "billing_method"],
		order_by="company ASC, property_name ASC"
	)

	lease_charges = []
	for l in leases:
		rate = get_applicable_charge_rate(l.name, start_date)
		daily_rate = 0.0
		annual_amt = 0.0
		t_rate = 9.0

		if rate:
			daily_rate = flt(rate.daily_rate_tax_incl)
			annual_amt = flt(rate.annual_amount_tax_incl)
			t_rate = flt(rate.tax_rate or 9.0)

		lease_charges.append({
			"property_lease": l.name,
			"property_name": l.property_name,
			"company": l.company,
			"area": flt(l.area),
			"charge_item": l.charge_item,
			"billing_method": l.billing_method,
			"billing_days": days_in_month,
			"daily_rate_snapshot": daily_rate,
			"annual_amount_snapshot": annual_amt,
			"tax_rate": t_rate,
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
	doc.electricity_price = flt(calc_data.get("electricity_price"))
	doc.electricity_tax_rate = flt(calc_data.get("electricity_tax_rate"))
	doc.water_price = flt(calc_data.get("water_price"))
	doc.water_tax_rate = flt(calc_data.get("water_tax_rate"))
	doc.total_amount = flt(calc_data.get("total_amount"))
	doc.remark = calc_data.get("remark") or ""

	# 更新子表
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

	# 严格校验
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
