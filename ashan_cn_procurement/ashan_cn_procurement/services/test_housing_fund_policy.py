import unittest

import sys
import types
from datetime import date, datetime

try:
    import frappe  # noqa: F401
except ModuleNotFoundError:
    frappe = types.ModuleType("frappe")
    frappe.throw = lambda message: (_ for _ in ()).throw(ValueError(message))
    frappe.db = types.SimpleNamespace()
    frappe.get_all = lambda *args, **kwargs: []
    frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn) if not (args and callable(args[0])) else args[0]
    sys.modules["frappe"] = frappe

    utils = types.ModuleType("frappe.utils")
    utils.cint = lambda value=0: int(float(value or 0))
    utils.flt = lambda value=0: float(value or 0)
    utils.today = lambda: date.today().isoformat()
    def _getdate(value=None):
        if value is None:
            return date.today()
        if isinstance(value, date):
            return value
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    utils.getdate = _getdate
    sys.modules["frappe.utils"] = utils

from ashan_cn_procurement.services.housing_fund_policy_service import (
    OVERRIDE_OFF,
    OVERRIDE_ON,
    POLICY_FIXED_OFF,
    POLICY_FIXED_ON,
    POLICY_FOLLOW,
    evaluate_housing_fund_policy,
)


class TestHousingFundPolicy(unittest.TestCase):
    def employee(self, policy=POLICY_FOLLOW, base=2320, employee_type="正式工"):
        return {
            "employee_no": "T001",
            "employee_name": "测试员工",
            "employee_type": employee_type,
            "housing_fund_base": base,
            "housing_fund_policy": policy,
        }

    def setting(self, months="1,4,7,10", enabled=1, off="停缴"):
        return {
            "hf_auto_rule_enabled": enabled,
            "hf_contribution_months": months,
            "hf_off_month_action": off,
        }

    def test_quarter_first_month_schedule(self):
        emp = self.employee()
        for month in (1, 4, 7, 10):
            result = evaluate_housing_fund_policy(emp, f"2026-{month:02d}", self.setting())
            self.assertTrue(result["is_contributing"])
            self.assertEqual(result["effective_base"], 2320)
        for month in (2, 3, 5, 6, 8, 9, 11, 12):
            result = evaluate_housing_fund_policy(emp, f"2026-{month:02d}", self.setting())
            self.assertFalse(result["is_contributing"])
            self.assertEqual(result["effective_base"], 0)

    def test_fixed_on_is_exempt_from_off_month(self):
        result = evaluate_housing_fund_policy(self.employee(POLICY_FIXED_ON), "2026-08", self.setting())
        self.assertTrue(result["is_contributing"])
        self.assertEqual(result["decision_code"], "FIXED_ON")

    def test_fixed_off_stops_even_in_scheduled_month(self):
        result = evaluate_housing_fund_policy(self.employee(POLICY_FIXED_OFF), "2026-07", self.setting())
        self.assertFalse(result["is_contributing"])
        self.assertEqual(result["decision_code"], "FIXED_OFF")

    def test_monthly_override_has_highest_policy_priority(self):
        on = evaluate_housing_fund_policy(self.employee(POLICY_FIXED_OFF), "2026-08", self.setting(), OVERRIDE_ON)
        off = evaluate_housing_fund_policy(self.employee(POLICY_FIXED_ON), "2026-07", self.setting(), OVERRIDE_OFF)
        self.assertTrue(on["is_contributing"])
        self.assertFalse(off["is_contributing"])

    def test_master_base_is_never_mutated(self):
        emp = self.employee(POLICY_FOLLOW, 20000)
        result = evaluate_housing_fund_policy(emp, "2026-08", self.setting())
        self.assertEqual(emp["housing_fund_base"], 20000)
        self.assertEqual(result["master_base"], 20000)
        self.assertEqual(result["effective_base"], 0)

    def test_ineligible_type_cannot_be_forced_on(self):
        result = evaluate_housing_fund_policy(self.employee(POLICY_FIXED_ON, employee_type="临时工"), "2026-07", self.setting(), OVERRIDE_ON)
        self.assertFalse(result["is_contributing"])
        self.assertEqual(result["decision_code"], "INELIGIBLE_TYPE")


if __name__ == "__main__":
    unittest.main()
