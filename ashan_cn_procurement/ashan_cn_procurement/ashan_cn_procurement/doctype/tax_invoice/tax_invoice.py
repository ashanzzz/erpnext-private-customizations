# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

class TaxInvoice(Document):
	def validate(self):
		self.normalize_fields()
		self.compute_totals_and_summary()
		self.check_red_invoice()

	def normalize_fields(self):
		if self.invoice_no:
			self.invoice_no = str(self.invoice_no).strip()
		if self.original_invoice_no:
			self.original_invoice_no = str(self.original_invoice_no).strip()

	def check_red_invoice(self):
		if flt(self.invoice_grand_total) < 0 or flt(self.amount_without_tax) < 0 or self.credit_note_no or self.original_invoice_no:
			self.is_red_invoice = 1

	def compute_totals_and_summary(self):
		# 自动计算实际应付合计
		if flt(self.remark_total) != 0:
			self.payable_total = flt(self.remark_total)
		else:
			self.payable_total = round(flt(self.invoice_grand_total) + flt(self.vehicle_vessel_tax) + flt(self.late_fee), 2)

		# 自动生成列表展示摘要
		items = self.get("items") or []
		if not self.display_summary and items:
			first_item = items[0].item_name or ""
			if len(items) == 1:
				if items[0].line_type == "通行费" and items[0].plate_number:
					self.display_summary = f"通行费 · {items[0].plate_number}"
				else:
					self.display_summary = first_item
			else:
				has_vv_tax = any(it.line_type == "车船税" or flt(it.vehicle_vessel_tax) > 0 for it in items)
				if has_vv_tax:
					self.display_summary = f"{first_item} + 车船税"
				else:
					self.display_summary = f"{first_item}… 等 {len(items)} 项"
