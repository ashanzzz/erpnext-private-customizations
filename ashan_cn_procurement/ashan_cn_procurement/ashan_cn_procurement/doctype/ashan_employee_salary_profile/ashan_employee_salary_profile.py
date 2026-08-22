# Copyright (c) 2026, Ashan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AshanEmployeeSalaryProfile(Document):
	"""Employee payroll master with one authoritative identity/retirement rule path.

	The workbench APIs, direct DocType edits, imports and future AI-assisted writes all
	pass through the same validation.  This prevents the UI from becoming the only
	place where ID-card derivation and retirement policy are enforced.
	"""

	def validate(self):
		from ashan_cn_procurement.services.retirement_policy_service import (
			calculate_retirement_details,
			validate_chinese_id_number,
		)

		if (self.housing_fund_policy or "").strip() not in {"跟随公司规则", "固定缴纳", "固定停缴"}:
			self.housing_fund_policy = "跟随公司规则"

		certificate_type = (self.certificate_type or "中国居民身份证").strip()
		certificate_number = (self.id_card or "").strip().upper()
		self.certificate_type = certificate_type
		self.id_card = certificate_number

		if certificate_type == "中国居民身份证" and certificate_number:
			identity = validate_chinese_id_number(certificate_number)
			if not identity.get("is_valid"):
				frappe.throw(f"身份证号码校验失败：{identity.get('message') or '格式或校验码错误'}")
			self.birth_date = identity.get("birth_date")
			self.gender = identity.get("gender")
		elif certificate_type != "中国居民身份证" and certificate_number:
			missing = []
			if not self.birth_date:
				missing.append("出生日期")
			if not self.gender:
				missing.append("性别")
			if missing:
				frappe.throw(f"{certificate_type}无法自动识别{'、'.join(missing)}，请人工填写后再保存。")

		calculated = calculate_retirement_details(
			certificate_type=certificate_type,
			certificate_number=certificate_number,
			birth_date=self.birth_date,
			gender=self.gender,
			retirement_category=self.retirement_category,
			original_retirement_age=self.original_retirement_age,
			delayed_retirement_age=self.delayed_retirement_age,
			job_title=self.job_title,
		)

		self.current_age = calculated.get("current_age") or 0
		self.retirement_policy_version = calculated.get("policy_version") or ""

		# Female 50/55 classification is a personnel-policy attribute. A legacy
		# job-title guess may be shown by the UI, but is never persisted as truth.
		if not calculated.get("needs_retirement_category_confirmation"):
			self.retirement_category = calculated.get("retirement_category") or self.retirement_category
			self.original_retirement_age = calculated.get("original_retirement_age") or 0
			self.delayed_retirement_age = calculated.get("delayed_retirement_age") or 0
			self.original_retirement_period = calculated.get("original_retire_period") or ""
			self.delayed_retirement_period = calculated.get("delayed_retire_period") or ""

			# Keep the legacy fields synchronized for older pages/reports while new
			# code uses the explicit original/delayed fields above.
			self.retirement_age = self.delayed_retirement_age
			self.retirement_date = calculated.get("delayed_retire_date") or None
