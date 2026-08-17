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
		if (m.get("company") if isinstance(m, dict) else m.company) == company
	]

	# 过滤该公司相关的租赁费用
	company_leases = [
		l for l in doc_dict.get("lease_charges", [])
		if (l.get("company") if isinstance(l, dict) else l.company) == company
	]

	# 过滤该公司相关的调整项
	company_adjustments = []
	for adj in doc_dict.get("adjustments", []):
		adj_scope = adj.get("adjustment_scope") if isinstance(adj, dict) else adj.adjustment_scope
		adj_comp = adj.get("company") if isinstance(adj, dict) else adj.company
		adj_from = adj.get("from_company") if isinstance(adj, dict) else adj.from_company
		adj_to = adj.get("to_company") if isinstance(adj, dict) else adj.to_company
		adj_type = adj.get("adjustment_type") if isinstance(adj, dict) else adj.adjustment_type
		u_type = adj.get("utility_type") if isinstance(adj, dict) else adj.utility_type
		u_adj = adj.get("usage_adjustment") if isinstance(adj, dict) else adj.usage_adjustment
		amt_adj = adj.get("amount_adjustment") if isinstance(adj, dict) else adj.amount_adjustment
		eq_u = adj.get("equivalent_usage") if isinstance(adj, dict) else adj.equivalent_usage
		reason = adj.get("reason") if isinstance(adj, dict) else adj.reason

		if adj_scope == "单公司" and adj_comp == company:
			company_adjustments.append({
				"title": f"{u_type}调整",
				"type": adj_type,
				"scope": "本公司单项调整",
				"usage": u_adj,
				"amount": amt_adj,
				"reason": reason
			})
		elif adj_scope == "公司间转移":
			if adj_from == company:
				company_adjustments.append({
					"title": f"公司间{u_type}调出 (转至 {adj_to})",
					"type": adj_type,
					"scope": "公司间转出",
					"usage": -flt(eq_u),
					"amount": -flt(amt_adj),
					"reason": reason
				})
			elif adj_to == company:
				company_adjustments.append({
					"title": f"公司间{u_type}调入 (来自 {adj_from})",
					"type": adj_type,
					"scope": "公司间转入",
					"usage": flt(eq_u),
					"amount": flt(amt_adj),
					"reason": reason
				})

	# 汇总信息
	summary = next((s for s in doc_dict.get("company_summaries", []) if (s.get("company") if isinstance(s, dict) else s.company) == company), None)

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
