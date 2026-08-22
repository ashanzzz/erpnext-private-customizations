# Copyright (c) 2026, Ashan CN Procurement
import frappe
from frappe.model.document import Document


class AshanInsuranceSetting(Document):
    def validate(self):
        from ashan_cn_procurement.services.housing_fund_policy_service import parse_contribution_months

        months = parse_contribution_months(self.hf_contribution_months or "1,4,7,10")
        self.hf_contribution_months = ",".join(str(x) for x in months)
        if (self.hf_off_month_action or "停缴") not in {"停缴", "继续缴纳"}:
            frappe.throw("公积金非计划月份处理只能选择“停缴”或“继续缴纳”。")
        self.hf_off_month_action = self.hf_off_month_action or "停缴"
