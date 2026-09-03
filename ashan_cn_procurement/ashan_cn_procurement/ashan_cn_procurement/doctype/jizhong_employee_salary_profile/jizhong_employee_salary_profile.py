# Copyright (c) 2026, Ashan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class JizhongEmployeeSalaryProfile(Document):
	def validate(self):
		self.validate_company()
		self.calculate_special_additional_deductions()

	def validate_company(self):
		if not self.company:
			self.company = "天津吉众科技有限公司"

	def calculate_special_additional_deductions(self):
		self.special_additional_deductions_total = (
			flt(self.deduction_child_education)
			+ flt(self.deduction_continuing_education)
			+ flt(self.deduction_serious_illness)
			+ flt(self.deduction_housing_loan)
			+ flt(self.deduction_housing_rent)
			+ flt(self.deduction_elderly_care)
			+ flt(self.deduction_infant_care)
		)
