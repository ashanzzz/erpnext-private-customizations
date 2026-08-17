# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import flt, nowdate

from ashan_cn_procurement.services.property_settlement import (
	get_month_settlement_data,
	save_draft_settlement,
	finalize_monthly_settlement,
	revert_settlement_to_draft,
	calculate_settlement_matrix
)


class TestPropertySettlement(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		# 确保公司存在
		if not frappe.db.exists("Company", "天津吉众机电设备有限公司"):
			c1 = frappe.new_doc("Company")
			c1.company_name = "天津吉众机电设备有限公司"
			c1.abbr = "吉众"
			c1.default_currency = "CNY"
			c1.insert(ignore_permissions=True)

		if not frappe.db.exists("Company", "天津祺富机械加工有限公司"):
			c2 = frappe.new_doc("Company")
			c2.company_name = "天津祺富机械加工有限公司"
			c2.abbr = "祺富"
			c2.default_currency = "CNY"
			c2.insert(ignore_permissions=True)

		# 准备测试表具
		cls.comp_jz = "天津吉众机电设备有限公司"
		cls.comp_qf = "天津祺富机械加工有限公司"

	def test_01_meter_multiplier_and_usage(self):
		"""测试 Case 1: 正常电表倍率与用量核算 (2711 -> 2780, 倍率 120 -> 核定 8280 kWh)"""
		mock_data = {
			"settlement_month": "2026-08-01",
			"electricity_price": 1.1957,
			"electricity_tax_rate": 13.0,
			"water_price": 5.5,
			"water_tax_rate": 9.0,
			"meter_readings": [
				{
					"utility_meter": "1号电表",
					"meter_no": "1",
					"utility_type": "电",
					"company": self.comp_jz,
					"previous_reading": 2711.0,
					"current_reading": 2780.0,
					"multiplier": 120.0
				}
			],
			"adjustments": [],
			"lease_charges": []
		}
		res = calculate_settlement_matrix(mock_data)
		r0 = res["meter_readings"][0]

		self.assertEqual(r0["raw_usage"], 69.0)
		self.assertEqual(r0["calculated_usage"], 8280.0)
		# 8280 * 1.1957 = 9900.396 -> 9900.40
		self.assertEqual(r0["amount_tax_incl"], 9900.40)

	def test_02_usage_adjustment(self):
		"""测试 Case 2: 按用量调整 (-100 kWh -> 自动计算金额 -119.57)"""
		mock_data = {
			"settlement_month": "2026-08-01",
			"electricity_price": 1.1957,
			"adjustments": [
				{
					"adjustment_type": "按用量",
					"utility_type": "电费",
					"adjustment_scope": "单公司",
					"company": self.comp_jz,
					"usage_adjustment": -100.0,
					"reason": "4号表修正"
				}
			]
		}
		res = calculate_settlement_matrix(mock_data)
		adj = res["adjustments"][0]
		self.assertEqual(adj["amount_adjustment"], -119.57)
		self.assertEqual(adj["equivalent_usage"], -100.0)

	def test_03_company_transfer_amount_adjustment(self):
		"""测试 Case 3: 公司间电费金额调整 (吉众 -> 祺富 8000 元，吉众 -8000，祺富 +8000，等效电量 8000 / 1.1957)"""
		mock_data = {
			"settlement_month": "2026-08-01",
			"electricity_price": 1.1957,
			"adjustments": [
				{
					"adjustment_type": "按金额",
					"utility_type": "电费",
					"adjustment_scope": "公司间转移",
					"from_company": self.comp_jz,
					"to_company": self.comp_qf,
					"amount_adjustment": 8000.0,
					"reason": "公司间电费分摊调整"
				}
			],
			"meter_readings": [],
			"lease_charges": []
		}
		res = calculate_settlement_matrix(mock_data)
		adj = res["adjustments"][0]

		# 8000 / 1.1957 = 6690.64
		expected_eq_usage = round(8000.0 / 1.1957, 2)
		self.assertEqual(adj["equivalent_usage"], expected_eq_usage)

		# 汇总检验
		summary_jz = next(s for s in res["company_summaries"] if s["company"] == self.comp_jz)
		summary_qf = next(s for s in res["company_summaries"] if s["company"] == self.comp_qf)

		self.assertEqual(summary_jz["adjustment_amount"], -8000.0)
		self.assertEqual(summary_qf["adjustment_amount"], 8000.0)
		self.assertEqual(summary_jz["electricity_amount"], -8000.0)
		self.assertEqual(summary_qf["electricity_amount"], 8000.0)

	def test_04_lease_charge_365_days_calculation(self):
		"""测试 Case 4: 房租物业年金额按 365 天标准日单价核算"""
		mock_data = {
			"settlement_month": "2026-08-01", # 8月共31天
			"lease_charges": [
				{
					"property_name": "大车间+3楼办公",
					"company": self.comp_jz,
					"area": 3338.0,
					"charge_item": "房租含物业",
					"billing_method": "年金额",
					"annual_amount_snapshot": 240000.0,
					"tax_rate": 9.0,
					"billing_days": 31
				}
			]
		}
		res = calculate_settlement_matrix(mock_data)
		l0 = res["lease_charges"][0]

		# 日单价 = 240000 / 3338 / 365 = 0.196985
		# 31天含税金额 = 3338 * 0.196985 * 31 = 20383.56
		expected_amt = round(3338.0 * (240000.0 / 3338.0 / 365.0) * 31, 2)
		self.assertEqual(l0["amount_tax_incl"], expected_amt)

	def test_05_validation_on_finalize(self):
		"""测试 Case 5: 结算完成校验 (异常本期读数与未填原因拒绝通过)"""
		invalid_data = {
			"settlement_month": "2026-08-01",
			"meter_readings": [
				{
					"utility_meter": "TEST-1",
					"meter_no": "1",
					"company": self.comp_jz,
					"previous_reading": 3000.0,
					"current_reading": 2000.0, # 本期 < 上期且无备注
					"remark": ""
				}
			],
			"adjustments": [],
			"lease_charges": []
		}
		with self.assertRaises(frappe.ValidationError):
			finalize_monthly_settlement(invalid_data)
