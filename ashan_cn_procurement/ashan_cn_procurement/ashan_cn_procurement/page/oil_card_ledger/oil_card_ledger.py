# -*- coding: utf-8 -*-
# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import calendar
import frappe
from frappe.utils import flt, getdate, nowdate


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


@frappe.whitelist()
def get_oil_card_ledger_data(oil_card, year=None, month=None):
	"""
	计算指定油卡在指定年月的财务结转与明细流水：
	- 上期结转余额 (期初)
	- 本期充值总额与流水
	- 本期加油消费总额与流水
	- 期末结存余额
	"""
	if not oil_card:
		return {}

	card = frappe.get_doc("Oil Card", oil_card)

	today = getdate(nowdate())
	y = int(year) if year else today.year
	m = int(month) if (month and str(month).isdigit() and int(month) > 0) else None

	if m:
		_, last_day = calendar.monthrange(y, m)
		start_date = f"{y}-{m:02d}-01"
		end_date = f"{y}-{m:02d}-{last_day:02d}"
	else:
		start_date = f"{y}-01-01"
		end_date = f"{y}-12-31"

	# 1. 计算【上期结转余额】
	# 期初结转 = 油卡初始期初余额 + (start_date之前的充值总额) - (start_date之前的加油扣款总额)
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

	# 2. 拉取【本期充值流水】
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
		],
		order_by="posting_date asc, creation asc",
	)

	period_recharge_amount = sum(flt(r.recharge_amount) for r in recharges)
	period_bonus_amount = sum(flt(r.bonus_amount) for r in recharges)
	period_effective_recharge = sum(flt(r.effective_amount or r.recharge_amount) for r in recharges)

	# 3. 拉取【本期加油与能耗记录】
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
		],
		order_by="posting_date asc, creation asc",
	)

	period_refuel_amount = sum(flt(f.amount) for f in refuels)
	period_liters = sum(flt(f.liters) for f in refuels)
	period_distance = sum(flt(f.distance_since_last) for f in refuels)
	avg_liter_per_100km = (
		round((period_liters / period_distance) * 100, 2) if period_distance and period_distance > 0 else 0
	)

	# 4. 计算【期末结存余额】
	ending_balance = opening_balance + period_effective_recharge - period_refuel_amount

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
			"period_recharge_amount": period_recharge_amount,
			"period_bonus_amount": period_bonus_amount,
			"period_effective_recharge": period_effective_recharge,
			"recharge_count": len(recharges),
			"period_refuel_amount": period_refuel_amount,
			"period_liters": period_liters,
			"period_distance": period_distance,
			"avg_liter_per_100km": avg_liter_per_100km,
			"refuel_count": len(refuels),
			"ending_balance": ending_balance,
		},
		"recharges": recharges,
		"refuels": refuels,
	}
