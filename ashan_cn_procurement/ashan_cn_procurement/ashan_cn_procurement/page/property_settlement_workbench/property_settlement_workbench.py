# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.utils import flt, cint

from ashan_cn_procurement.services.property_settlement import (
	get_month_settlement_data,
	save_draft_settlement,
	finalize_monthly_settlement,
	revert_settlement_to_draft,
	export_settlement_excel
)


@frappe.whitelist()
def get_settlement(year, month):
	"""获取指定年月的物业月结全量数据（包含水电抄表、调整项、租赁费与公司汇总）"""
	return get_month_settlement_data(year, month)


@frappe.whitelist()
def save_settlement(data):
	"""保存草稿月结"""
	if isinstance(data, str):
		data = json.loads(data)
	return save_draft_settlement(data)


@frappe.whitelist()
def finalize_settlement(data):
	"""完成并锁定本月结算"""
	if isinstance(data, str):
		data = json.loads(data)
	return finalize_monthly_settlement(data)


@frappe.whitelist()
def revert_settlement(name):
	"""取消结算并退回草稿"""
	return revert_settlement_to_draft(name)


@frappe.whitelist()
def get_company_bill_data(settlement_name, company):
	"""
	获取指定月结单中特定公司的结算单明细数据（用于弹窗预览与打印）
	"""
	doc = frappe.get_doc("Property Monthly Settlement", settlement_name)
	doc_dict = doc.as_dict()

	# 过滤该公司相关的抄表
	company_meters = [
		m for m in doc_dict.get("meter_readings", [])
		if m.company == company
	]

	# 过滤该公司相关的租赁费用
	company_leases = [
		l for l in doc_dict.get("lease_charges", [])
		if l.company == company
	]

	# 过滤该公司相关的调整项
	company_adjustments = []
	for adj in doc_dict.get("adjustments", []):
		if adj.adjustment_scope == "单公司" and adj.company == company:
			company_adjustments.append({
				"title": f"{adj.utility_type}调整",
				"type": adj.adjustment_type,
				"scope": "本公司单项调整",
				"usage": adj.usage_adjustment,
				"amount": adj.amount_adjustment,
				"reason": adj.reason
			})
		elif adj.adjustment_scope == "公司间转移":
			if adj.from_company == company:
				company_adjustments.append({
					"title": f"公司间{adj.utility_type}调出 (转至 {adj.to_company})",
					"type": adj.adjustment_type,
					"scope": "公司间转出",
					"usage": -flt(adj.equivalent_usage),
					"amount": -flt(adj.amount_adjustment),
					"reason": adj.reason
				})
			elif adj.to_company == company:
				company_adjustments.append({
					"title": f"公司间{adj.utility_type}调入 (来自 {adj.from_company})",
					"type": adj.adjustment_type,
					"scope": "公司间转入",
					"usage": flt(adj.equivalent_usage),
					"amount": flt(adj.amount_adjustment),
					"reason": adj.reason
				})

	# 汇总信息
	summary = next((s for s in doc_dict.get("company_summaries", []) if s.company == company), None)

	return {
		"settlement_name": doc.name,
		"settlement_month": doc.settlement_month,
		"status": doc.status,
		"company": company,
		"electricity_price": doc.electricity_price,
		"water_price": doc.water_price,
		"meters": company_meters,
		"leases": company_leases,
		"adjustments": company_adjustments,
		"summary": summary
	}
