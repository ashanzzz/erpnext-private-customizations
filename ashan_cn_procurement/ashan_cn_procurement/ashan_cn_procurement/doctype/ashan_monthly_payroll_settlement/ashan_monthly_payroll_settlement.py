# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AshanMonthlyPayrollSettlement(Document):
	def validate(self):
		if self.locked and not frappe.flags.ignore_lock:
			frappe.throw("该月度薪酬核定表已核定锁定，禁止直接修改！如需调整请先申请反审核解锁。")
