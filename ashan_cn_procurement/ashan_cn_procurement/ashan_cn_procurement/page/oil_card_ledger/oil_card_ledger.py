# -*- coding: utf-8 -*-
# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import calendar
import frappe
from frappe.utils import flt, getdate, nowdate, now_datetime


def is_oil_card_manager():
	"""
	判断当前用户是否具备【油卡管理员】权限
	"""
	if frappe.session.user == "Administrator":
		return True
	user_roles = set(frappe.get_roles())
	manager_roles = {"System Manager", "Oil Card Manager", "Accounts Manager", "Stock Manager"}
	return bool(user_roles & manager_roles)


@frappe.whitelist()
def get_all_oil_cards():
	"""
	获取所有有效油卡列表及其当前余额
	"""
	cards = frappe.get_all(
		"Oil Card",
		fields=[
			"name",
			"card_code",
			"card_name",
			"card_no_masked",
			"card_type",
			"supplier",
			"company",
			"status",
			"opening_balance",
			"current_balance",
			"uninvoiced_amount",
		],
		order_by="idx asc, modified desc",
	)
	return cards


def get_fuel_label(fuel_type):
	"""燃油动力类型纯中文转换"""
	if not fuel_type:
		return "汽油"
	f = str(fuel_type).strip()
	if f in ["Diesel", "柴油"]:
		return "柴油"
	if f in ["Petrol", "汽油"]:
		return "汽油"
	if "混动" in f or "Hybrid" in f:
		return "插电混动"
	if "纯电" in f or "Electric" in f:
		return "纯电动"
	if "气" in f or "Gas" in f:
		return "天然气"
	return f


@frappe.whitelist()
def get_quick_entry_meta():
	"""
	获取行内快速补录与新建油卡所需的车辆档案、付款方式、公司及供应商元数据
	"""
	vehicles = frappe.get_all(
		"Vehicle",
		fields=["name", "license_plate", "model", "make", "fuel_type", "last_odometer"],
		order_by="license_plate asc",
	)
	for v in vehicles:
		v["fuel_type_label"] = get_fuel_label(v.get("fuel_type"))

	modes = frappe.get_all("Mode of Payment", fields=["name"], filters={"enabled": 1})
	mode_names = [m.name for m in modes] if modes else ["Cheque", "Cash", "银行转账", "微信支付", "支付宝"]

	companies = frappe.get_all("Company", fields=["name", "company_name"])
	suppliers = frappe.get_all("Supplier", fields=["name", "supplier_name"], order_by="name asc", limit=100)
	default_company = frappe.defaults.get_user_default("Company") or (companies[0].name if companies else "")
	default_supplier = suppliers[0].name if suppliers else ""

	return {
		"vehicles": vehicles,
		"modes_of_payment": mode_names,
		"companies": companies,
		"suppliers": suppliers,
		"default_company": default_company,
		"default_supplier": default_supplier,
	}


@frappe.whitelist()
def quick_create_vehicle(license_plate, vehicle_category="货车", fuel_type="柴油", last_odometer=0, make=None, company=None):
	"""
	单页极速新建车辆档案（零跳转，纯中文）
	"""
	if not license_plate:
		frappe.throw("车牌号码为必填项！")

	plate = license_plate.strip().upper()
	if frappe.db.exists("Vehicle", plate):
		frappe.throw(f"车牌号为【{plate}】的车辆已存在！")

	if not company or not frappe.db.exists("Company", company):
		company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
		if not company or not frappe.db.exists("Company", company):
			companies = frappe.get_all("Company", fields=["name"], limit=1)
			company = companies[0].name if companies else None

	# 规范化 ERPNext 标准 fuel_type 字段
	fuel_norm = "Diesel"
	fuel_label = get_fuel_label(fuel_type)
	if fuel_label == "汽油" or fuel_label == "插电混动":
		fuel_norm = "Petrol"
	elif fuel_label == "纯电动":
		fuel_norm = "Electric"
	elif fuel_label == "天然气":
		fuel_norm = "Natural Gas"
	else:
		fuel_norm = "Diesel"

	# 规范化车型
	model_val = vehicle_category.split("/")[0].strip() if "/" in vehicle_category else vehicle_category.strip()

	doc = frappe.new_doc("Vehicle")
	doc.license_plate = plate
	doc.make = make or ""
	doc.model = model_val or "货车"
	doc.company = company
	doc.last_odometer = int(flt(last_odometer))
	doc.fuel_type = fuel_norm
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": "ok",
		"message": f"车辆【{doc.license_plate}】已成功创建！",
		"vehicle": {
			"name": doc.name,
			"license_plate": doc.license_plate,
			"model": doc.model,
			"fuel_type": doc.fuel_type,
			"fuel_type_label": fuel_label,
			"last_odometer": doc.last_odometer,
		},
	}


@frappe.whitelist()
def quick_create_oil_card(card_name, card_no, card_code=None, card_type="主卡", company=None, supplier=None, opening_balance=0):
	"""
	单页模态对话框极速新建油卡档案（零跳转）
	"""
	if not card_name or not card_no:
		frappe.throw("油卡名称与卡号为必填项！")

	if not company or not frappe.db.exists("Company", company):
		company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
		if not company or not frappe.db.exists("Company", company):
			companies = frappe.get_all("Company", fields=["name"], limit=1)
			company = companies[0].name if companies else None

	if not supplier or not frappe.db.exists("Supplier", supplier):
		suppliers = frappe.get_all("Supplier", fields=["name"], limit=1)
		supplier = suppliers[0].name if suppliers else None

	# 若未指定系统卡号/编码，则按序号或规则自动生成
	if not card_code:
		count = frappe.db.count("Oil Card") + 1
		card_code = f"CARD-{count:03d}"
		while frappe.db.exists("Oil Card", card_code):
			count += 1
			card_code = f"CARD-{count:03d}"

	# 生成脱敏卡号
	clean_no = str(card_no).strip()
	if len(clean_no) >= 10:
		masked_no = clean_no[:6] + "******" + clean_no[-4:]
	else:
		masked_no = clean_no

	op_bal = flt(opening_balance)

	doc = frappe.new_doc("Oil Card")
	doc.card_code = card_code
	doc.card_name = card_name.strip()
	doc.card_no = clean_no
	doc.card_no_masked = masked_no
	doc.card_type = card_type or "主卡"
	doc.company = company
	doc.supplier = supplier
	doc.status = "Active"
	doc.opening_balance = op_bal
	doc.current_balance = op_bal
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"status": "ok", "message": f"油卡【{doc.card_name}】已成功创建！", "name": doc.name}


@frappe.whitelist()
def delete_oil_card(oil_card):
	"""
	单页极速删除油卡档案（零跳转）
	"""
	if not is_oil_card_manager():
		frappe.throw("权限不足：只有管理员才可以删除油卡档案！")

	if not oil_card or not frappe.db.exists("Oil Card", oil_card):
		frappe.throw("指定的油卡不存在或已被删除！")

	card_name = frappe.db.get_value("Oil Card", oil_card, "card_name") or oil_card
	frappe.delete_doc("Oil Card", oil_card, ignore_permissions=True)
	frappe.db.commit()

	return {"status": "ok", "message": f"油卡【{card_name}】已成功删除！"}


@frappe.whitelist()
def get_unified_ledger_data(oil_card, year=None, month=None):
	"""
	获取油卡单一合流流水总账数据：
	1. 首行固定：XXXX年X月结转余额 (上月结转)
	2. 加油与充值按发生时间合流，逐行计算实时结余余额 (running_balance)
	3. 检查月度核定锁定状态
	4. 判定当前用户是否为管理员 (用于高级列自适应控制)
	"""
	if not oil_card:
		return {}

	card = frappe.get_doc("Oil Card", oil_card)
	today = getdate(nowdate())
	y = int(year) if year else today.year
	m = int(month) if (month and str(month).isdigit() and int(month) > 0) else today.month

	_, last_day = calendar.monthrange(y, m)
	start_date = f"{y}-{m:02d}-01"
	end_date = f"{y}-{m:02d}-{last_day:02d}"

	# 1. 计算【上期结转余额】
	prior_recharges = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(COALESCE(effective_amount, recharge_amount)), 0) as total
		FROM `tabOil Card Recharge`
		WHERE oil_card = %s AND posting_date < %s AND docstatus != 2
	""",
		(oil_card, start_date),
		as_dict=True,
	)[0].total

	prior_refuels = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(amount), 0) as total
		FROM `tabOil Card Refuel Log`
		WHERE oil_card = %s AND posting_date < %s AND docstatus != 2
	""",
		(oil_card, start_date),
		as_dict=True,
	)[0].total

	opening_balance = flt(card.opening_balance) + flt(prior_recharges) - flt(prior_refuels)

	# 2. 拉取本月【充值记录】
	recharges = frappe.get_all(
		"Oil Card Recharge",
		filters={"oil_card": oil_card, "posting_date": ["between", [start_date, end_date]], "docstatus": ["!=", 2]},
		fields=[
			"name",
			"posting_date",
			"transaction_type",
			"recharge_amount",
			"bonus_amount",
			"effective_amount",
			"mode_of_payment",
			"reference_no",
			"status",
			"remark",
			"creation",
		],
	)

	# 3. 拉取本月【加油记录】
	refuels = frappe.get_all(
		"Oil Card Refuel Log",
		filters={"oil_card": oil_card, "posting_date": ["between", [start_date, end_date]], "docstatus": ["!=", 2]},
		fields=[
			"name",
			"posting_date",
			"vehicle",
			"fuel_grade",
			"odometer",
			"distance_since_last",
			"liters",
			"unit_price",
			"amount",
			"km_per_liter",
			"liter_per_100km",
			"invoice_status",
			"remark",
			"creation",
		],
	)

	# 4. 合流并按日期与创建时间正序排序
	raw_txns = []
	for r in recharges:
		raw_txns.append({
			"doc_type": "Oil Card Recharge",
			"name": r.name,
			"posting_date": str(r.posting_date),
			"txn_type": "充值",
			"target": r.mode_of_payment or "银行充值",
			"fuel_grade": "--",
			"odometer": None,
			"liters": None,
			"change_amount": flt(r.effective_amount or r.recharge_amount),
			"recharge_amount": flt(r.recharge_amount),
			"bonus_amount": flt(r.bonus_amount),
			"effective_amount": flt(r.effective_amount or r.recharge_amount),
			"distance": None,
			"consumption": None,
			"invoice_status": "--",
			"remark": r.remark or "",
			"creation": str(r.creation),
		})

	for f in refuels:
		raw_txns.append({
			"doc_type": "Oil Card Refuel Log",
			"name": f.name,
			"posting_date": str(f.posting_date),
			"txn_type": "加油",
			"target": f.vehicle or "车辆加油",
			"fuel_grade": f.fuel_grade or "",
			"odometer": f.odometer,
			"liters": flt(f.liters),
			"unit_price": flt(f.unit_price),
			"change_amount": -flt(f.amount),
			"recharge_amount": None,
			"bonus_amount": None,
			"effective_amount": None,
			"distance": f.distance_since_last,
			"consumption": flt(f.liter_per_100km),
			"invoice_status": f.invoice_status or "未开票",
			"remark": f.remark or "",
			"creation": str(f.creation),
		})

	# 排序：日期升序，创建时间升序
	raw_txns.sort(key=lambda x: (x["posting_date"], x["creation"]))

	# 5. 逐行计算实时结余余额 (Running Balance)
	running_bal = opening_balance
	txns = []
	for t in raw_txns:
		running_bal += t["change_amount"]
		t["running_balance"] = running_bal
		txns.append(t)

	ending_balance = running_bal

	# 6. 汇总指标
	period_recharges = sum(flt(r.effective_amount or r.recharge_amount) for r in recharges)
	period_refuels = sum(flt(f.amount) for f in refuels)
	period_liters = sum(flt(f.liters) for f in refuels)
	period_distance = sum(flt(f.distance_since_last) for f in refuels)
	avg_consumption = round((period_liters / period_distance) * 100, 2) if period_distance else 0

	# 7. 检查【月度核定与锁定状态】
	closing_name = f"{oil_card}-{y}-{m}"
	is_locked = False
	locked_info = None

	if frappe.db.exists("Oil Card Monthly Closing", closing_name):
		closing_doc = frappe.get_doc("Oil Card Monthly Closing", closing_name)
		if closing_doc.is_locked:
			is_locked = True
			locked_info = {
				"locked_by": closing_doc.locked_by,
				"locked_at": str(closing_doc.locked_at),
				"closing_balance": flt(closing_doc.closing_balance),
				"remark": closing_doc.remark or "",
			}

	is_mgr = is_oil_card_manager()

	return {
		"card_info": {
			"name": card.name,
			"card_code": card.card_code,
			"card_name": card.card_name,
			"card_no": card.card_no,
			"card_no_masked": card.card_no_masked,
			"card_type": card.card_type,
			"supplier": card.supplier,
			"company": card.company,
			"status": card.status,
			"current_balance": flt(card.current_balance),
			"uninvoiced_amount": flt(card.uninvoiced_amount),
		},
		"kpis": {
			"year": y,
			"month": m,
			"start_date": start_date,
			"end_date": end_date,
			"opening_balance": opening_balance,
			"period_recharge_total": period_recharges,
			"recharge_count": len(recharges),
			"period_refuel_total": period_refuels,
			"refuel_count": len(refuels),
			"period_liters": period_liters,
			"period_distance": period_distance,
			"avg_consumption": avg_consumption,
			"ending_balance": ending_balance,
		},
		"transactions": txns,
		"is_locked": is_locked,
		"locked_info": locked_info,
		"is_manager": is_mgr,
	}


# 兼容旧版本 API 调用
@frappe.whitelist()
def get_oil_card_ledger_data(oil_card, year=None, month=None):
	"""
	兼容旧版接口别名
	"""
	return get_unified_ledger_data(oil_card, year, month)


@frappe.whitelist()
def quick_add_refuel(oil_card, posting_date, vehicle, odometer, liters, amount, fuel_grade=None, unit_price=None, remark=None):
	"""
	行内快速录入加油记录
	"""
	if not oil_card or not posting_date or not vehicle:
		frappe.throw("油卡、日期和车辆为必填项！")

	dt = getdate(posting_date)
	closing_name = f"{oil_card}-{dt.year}-{dt.month}"
	if frappe.db.exists("Oil Card Monthly Closing", closing_name):
		closing_doc = frappe.get_doc("Oil Card Monthly Closing", closing_name)
		if closing_doc.is_locked and not is_oil_card_manager():
			frappe.throw(f"该月份 ({dt.year}年{dt.month}月) 已被核定锁定，非管理员禁止录入记录！")

	card = frappe.get_doc("Oil Card", oil_card)
	veh = frappe.get_doc("Vehicle", vehicle)

	odo = flt(odometer)
	lit = flt(liters)
	amt = flt(amount)
	u_price = flt(unit_price) or (round(amt / lit, 2) if lit > 0 else 0)

	dist = odo - flt(veh.last_odometer) if odo > flt(veh.last_odometer) else 0
	consum = round((lit / dist) * 100, 2) if dist > 0 and lit > 0 else 0

	# 油品标号标准化映射与容错 (支持92, 92#, 92# 汽油, 0, 0#, 0# 柴油, -10#, -20#, -35#, 柴油, 汽油, CNG天然气等任意自由输入)
	grade_map = {
		"92#": "92", "92": "92", "92# 汽油": "92", "92号": "92", "92号汽油": "92",
		"95#": "95", "95": "95", "95# 汽油": "95", "95号": "95", "95号汽油": "95",
		"98#": "98", "98": "98", "98# 汽油": "98", "98号": "98", "98号汽油": "98",
		"0#": "0#", "0": "0#", "0# 柴油": "0#", "0号": "0#", "0号柴油": "0#",
		"-10#": "-10#", "-10": "-10#", "-10# 柴油": "-10#", "-10号柴油": "-10#",
		"-20#": "-20#", "-20": "-20#", "-20# 柴油": "-20#", "-20号柴油": "-20#",
		"-35#": "-35#", "-35": "-35#", "-35# 柴油": "-35#", "-35号柴油": "-35#",
		"CNG": "CNG", "CNG 天然气": "CNG", "天然气": "CNG", "LNG": "LNG", "LNG 液化天然气": "LNG",
		"Petrol": "95", "Diesel": "0#", "汽油": "95", "柴油": "0#"
	}
	clean_grade = str(fuel_grade).strip() if fuel_grade else ""
	norm_grade = grade_map.get(clean_grade) or grade_map.get(clean_grade.upper()) or grade_map.get(veh.fuel_type, "95")

	doc = frappe.new_doc("Oil Card Refuel Log")
	doc.naming_series = "OCRL-.YYYY.-.#####"
	doc.oil_card = oil_card
	doc.company = card.company
	doc.supplier = card.supplier
	doc.posting_date = posting_date
	doc.vehicle = vehicle
	doc.odometer = odo
	doc.fuel_grade = norm_grade
	doc.liters = lit
	doc.unit_price = u_price
	doc.amount = amt
	doc.invoice_status = "未开票"
	doc.remark = remark or ""
	doc.insert(ignore_permissions=True)

	# 更新只读派生字段
	frappe.db.set_value("Oil Card Refuel Log", doc.name, {
		"distance_since_last": dist,
		"liter_per_100km": consum
	}, update_modified=False)

	# 同步更新车辆最新里程
	if odo > flt(veh.last_odometer):
		frappe.db.set_value("Vehicle", vehicle, "last_odometer", odo, update_modified=True)

	# 重新计算卡内当前总余额
	recharges_sum = frappe.db.sql(
		"SELECT COALESCE(SUM(COALESCE(effective_amount, recharge_amount)), 0) as total FROM `tabOil Card Recharge` WHERE oil_card = %s AND docstatus != 2",
		oil_card,
		as_dict=True,
	)[0].total
	refuels_sum = frappe.db.sql(
		"SELECT COALESCE(SUM(amount), 0) as total FROM `tabOil Card Refuel Log` WHERE oil_card = %s AND docstatus != 2",
		oil_card,
		as_dict=True,
	)[0].total
	new_card_bal = flt(card.opening_balance) + flt(recharges_sum) - flt(refuels_sum)
	frappe.db.set_value("Oil Card", oil_card, "current_balance", new_card_bal, update_modified=True)

	frappe.db.commit()
	return {"status": "ok", "message": "加油记录已成功保存并实时核算！", "name": doc.name}


@frappe.whitelist()
def quick_add_recharge(oil_card, posting_date, recharge_amount, mode_of_payment=None, bonus_amount=None, remark=None):
	"""
	行内快速录入充值记录
	"""
	if not oil_card or not posting_date:
		frappe.throw("油卡和日期为必填项！")

	dt = getdate(posting_date)
	closing_name = f"{oil_card}-{dt.year}-{dt.month}"
	if frappe.db.exists("Oil Card Monthly Closing", closing_name):
		closing_doc = frappe.get_doc("Oil Card Monthly Closing", closing_name)
		if closing_doc.is_locked and not is_oil_card_manager():
			frappe.throw(f"该月份 ({dt.year}年{dt.month}月) 已被核定锁定，非管理员禁止录入充值！")

	card = frappe.get_doc("Oil Card", oil_card)
	rec_amt = flt(recharge_amount)
	bonus = flt(bonus_amount)
	eff_amt = rec_amt + bonus

	# 付款方式校验与容错
	if not mode_of_payment or not frappe.db.exists("Mode of Payment", mode_of_payment):
		default_mode = frappe.db.get_value("Mode of Payment", {"enabled": 1}, "name")
		mode_of_payment = default_mode or "Cheque"

	doc = frappe.new_doc("Oil Card Recharge")
	doc.naming_series = "OCR-.YYYY.-.#####"
	doc.oil_card = oil_card
	doc.company = card.company
	doc.supplier = card.supplier
	doc.posting_date = posting_date
	doc.transaction_type = "主卡充值"
	doc.mode_of_payment = mode_of_payment
	doc.recharge_amount = rec_amt
	doc.bonus_amount = bonus
	doc.effective_amount = eff_amt
	doc.status = "Submitted"
	doc.remark = remark or ""
	doc.insert(ignore_permissions=True)

	# 重新计算卡内当前总余额
	recharges_sum = frappe.db.sql(
		"SELECT COALESCE(SUM(COALESCE(effective_amount, recharge_amount)), 0) as total FROM `tabOil Card Recharge` WHERE oil_card = %s AND docstatus != 2",
		oil_card,
		as_dict=True,
	)[0].total
	refuels_sum = frappe.db.sql(
		"SELECT COALESCE(SUM(amount), 0) as total FROM `tabOil Card Refuel Log` WHERE oil_card = %s AND docstatus != 2",
		oil_card,
		as_dict=True,
	)[0].total
	new_card_bal = flt(card.opening_balance) + flt(recharges_sum) - flt(refuels_sum)
	frappe.db.set_value("Oil Card", oil_card, "current_balance", new_card_bal, update_modified=True)

	frappe.db.commit()
	return {"status": "ok", "message": "充值记录已成功保存并实时核算！", "name": doc.name}


@frappe.whitelist()
def lock_monthly_ledger(oil_card, year, month, remark=None):
	"""
	【本月核定 / 锁定月度】：
	仅油卡管理员可执行。核定后锁定该月所有加油与充值记录，不可编辑或删除。
	"""
	if not is_oil_card_manager():
		frappe.throw("权限不足：只有【油卡管理员】才可以执行月度核定与锁定操作。")

	y = int(year)
	m = int(month)
	closing_name = f"{oil_card}-{y}-{m}"

	# 计算当前期末余额
	data = get_unified_ledger_data(oil_card, y, m)
	closing_bal = data.get("kpis", {}).get("ending_balance", 0)

	if frappe.db.exists("Oil Card Monthly Closing", closing_name):
		doc = frappe.get_doc("Oil Card Monthly Closing", closing_name)
		doc.is_locked = 1
		doc.closing_balance = closing_bal
		doc.locked_by = frappe.session.user
		doc.locked_at = now_datetime()
		if remark:
			doc.remark = remark
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({
			"doctype": "Oil Card Monthly Closing",
			"oil_card": oil_card,
			"fiscal_year": y,
			"fiscal_month": m,
			"is_locked": 1,
			"closing_balance": closing_bal,
			"locked_by": frappe.session.user,
			"locked_at": now_datetime(),
			"remark": remark or "管理员月度核定锁定",
		})
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
	return {"status": "ok", "message": f"{y}年{m}月已成功核定并锁定！"}


@frappe.whitelist()
def unlock_monthly_ledger(oil_card, year, month):
	"""
	【解除月度锁定】：
	仅油卡管理员可执行。
	"""
	if not is_oil_card_manager():
		frappe.throw("权限不足：只有【油卡管理员】才可以解除月度锁定。")

	y = int(year)
	m = int(month)
	closing_name = f"{oil_card}-{y}-{m}"

	if frappe.db.exists("Oil Card Monthly Closing", closing_name):
		doc = frappe.get_doc("Oil Card Monthly Closing", closing_name)
		doc.is_locked = 0
		doc.save(ignore_permissions=True)
		frappe.db.commit()

	return {"status": "ok", "message": f"{y}年{m}月已解除锁定，恢复可编辑状态。"}


@frappe.whitelist()
def delete_ledger_record(doc_type, name, oil_card, year, month):
	"""
	删除单笔充值或加油流水（检查月度锁定）
	"""
	y = int(year)
	m = int(month)
	closing_name = f"{oil_card}-{y}-{m}"

	if frappe.db.exists("Oil Card Monthly Closing", closing_name):
		closing_doc = frappe.get_doc("Oil Card Monthly Closing", closing_name)
		if closing_doc.is_locked and not is_oil_card_manager():
			frappe.throw(f"该月份 ({y}年{m}月) 已被核定锁定，非管理员禁止删除记录！")

	if doc_type not in ["Oil Card Recharge", "Oil Card Refuel Log"]:
		frappe.throw("非法的单据类型")

	frappe.delete_doc(doc_type, name)
	frappe.db.commit()
	return {"status": "ok"}
