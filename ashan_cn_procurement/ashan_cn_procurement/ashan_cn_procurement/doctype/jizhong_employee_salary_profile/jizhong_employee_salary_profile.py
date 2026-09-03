# Copyright (c) 2026, Ashan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class JizhongEmployeeSalaryProfile(Document):
	def validate(self):
		self.validate_company()
		self.parse_id_card_info()
		self.calculate_special_additional_deductions()

	def validate_company(self):
		if not self.company:
			self.company = "天津吉众科技有限公司"

	def parse_id_card_info(self):
		cert_type = (self.certificate_type or "居民身份证").strip()
		if cert_type == "居民身份证" and self.id_card:
			id_clean = str(self.id_card).strip().upper()
			if len(id_clean) == 18 and id_clean[:17].isdigit():
				year = id_clean[6:10]
				month = id_clean[10:12]
				day = id_clean[12:14]
				if not self.birth_date:
					self.birth_date = f"{year}-{month}-{day}"
				if not self.gender:
					gender_code = int(id_clean[16])
					self.gender = "男" if gender_code % 2 == 1 else "女"

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
