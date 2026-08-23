# Copyright (c) 2026, Ashan CN Procurement
"""Automated regression & end-to-end test suite for Procurement Order Picker."""

import unittest
import frappe
from frappe.utils import nowdate, flt, random_string

from ashan_cn_procurement.services.procurement_picker_service import (
    get_pending_material_request_items,
    make_purchase_orders_from_mr_items,
    get_pending_purchase_order_items,
    make_purchase_receipts_from_po_items,
    get_pending_purchase_receipt_items,
    make_purchase_invoices_from_pr_items,
    get_pending_reimbursement_invoices,
    make_reimbursement_from_invoices,
    get_procurement_picker_overview_kpis,
)


class TestProcurementPicker(unittest.TestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.company = frappe.db.get_value("Company", {}, "name") or "天津祺富机械加工有限公司"

    def test_01_overview_kpis_smoke(self):
        """Verify get_procurement_picker_overview_kpis returns valid schema."""
        res = get_procurement_picker_overview_kpis(self.company)
        self.assertIn("kpis", res)
        self.assertIn("mr_to_po", res["kpis"])
        self.assertIn("po_to_pr", res["kpis"])
        self.assertIn("pr_to_pi", res["kpis"])
        self.assertIn("pi_to_rr", res["kpis"])
        self.assertIsInstance(res["kpis"]["mr_to_po"]["count"], int)

    def test_02_query_endpoints_smoke(self):
        """Verify query endpoints execute without SQL or permission errors."""
        mr_res = get_pending_material_request_items(self.company)
        self.assertIn("rows", mr_res)
        self.assertIn("count", mr_res)

        po_res = get_pending_purchase_order_items(self.company)
        self.assertIn("rows", po_res)
        self.assertIn("count", po_res)

        pr_res = get_pending_purchase_receipt_items(self.company)
        self.assertIn("rows", pr_res)
        self.assertIn("count", pr_res)

        rr_res = get_pending_reimbursement_invoices(self.company)
        self.assertIn("rows", rr_res)
        self.assertIn("count", rr_res)

    def test_03_full_chain_procurement_flow(self):
        """Test full 4-stage end-to-end selection & generation flow."""
        # Find or create a test item, supplier, and warehouse
        supplier = frappe.db.get_value("Supplier", {}, "name")
        if not supplier:
            sup_doc = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": "测试选单供应商_" + random_string(4),
                "supplier_group": "All Supplier Groups",
            }).insert()
            supplier = sup_doc.name

        warehouse = frappe.db.get_value("Warehouse", {"company": self.company, "is_group": 0}, "name")
        uom = frappe.db.get_value("UOM", {}, "name") or "Nos"
        item_code = frappe.db.get_value("Item", {"is_stock_item": 1, "has_variants": 0}, "name")
        if not item_code:
            item_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": "TEST-PICKER-ITEM-" + random_string(4),
                "item_name": "测试选单物料",
                "item_group": "All Item Groups",
                "stock_uom": uom,
                "is_stock_item": 1,
            }).insert()
            item_code = item_doc.name

        # --- Stage 1: Create Material Request & Submit ---
        mr = frappe.new_doc("Material Request")
        mr.company = self.company
        mr.material_request_type = "Purchase"
        mr.transaction_date = nowdate()
        mr.schedule_date = nowdate()
        mr.append("items", {
            "item_code": item_code,
            "qty": 10.0,
            "uom": uom,
            "stock_uom": uom,
            "rate": 50.0,
            "schedule_date": nowdate(),
            "warehouse": warehouse,
        })
        mr.insert()
        mr.submit()

        try:
            mri_name = mr.items[0].name

            # Query MR pool
            mr_pool = get_pending_material_request_items(self.company)
            found_mr = [r for r in mr_pool["rows"] if r["mri_name"] == mri_name]
            self.assertTrue(len(found_mr) > 0, "Material request item should appear in pending pool")
            self.assertEqual(found_mr[0]["pending_qty"], 10.0)

            # Generate PO
            po_gen = make_purchase_orders_from_mr_items(
                self.company,
                selected_items=[{"mri_name": mri_name, "this_qty": 10.0, "rate": 50.0}],
                supplier_override=supplier,
            )
            self.assertTrue(po_gen["success"])
            self.assertEqual(po_gen["created_count"], 1)
            po_name = po_gen["orders"][0]["name"]

            # Submit generated PO
            po_doc = frappe.get_doc("Purchase Order", po_name)
            po_doc.submit()

            poi_name = po_doc.items[0].name

            # --- Stage 2: Query PO pool & Generate PR ---
            po_pool = get_pending_purchase_order_items(self.company, {"supplier": supplier})
            found_po = [r for r in po_pool["rows"] if r["poi_name"] == poi_name]
            self.assertTrue(len(found_po) > 0, "PO item should appear in pending receipt pool")
            self.assertEqual(found_po[0]["pending_qty"], 10.0)

            pr_gen = make_purchase_receipts_from_po_items(
                self.company,
                selected_items=[{"poi_name": poi_name, "this_qty": 10.0, "warehouse": warehouse}],
            )
            self.assertTrue(pr_gen["success"])
            pr_name = pr_gen["receipts"][0]["name"]

            # Submit generated PR
            pr_doc = frappe.get_doc("Purchase Receipt", pr_name)
            pr_doc.submit()

            pri_name = pr_doc.items[0].name

            # --- Stage 3: Query PR pool & Generate PI ---
            pr_pool = get_pending_purchase_receipt_items(self.company, {"supplier": supplier})
            found_pr = [r for r in pr_pool["rows"] if r["pri_name"] == pri_name]
            self.assertTrue(len(found_pr) > 0, "PR item should appear in pending invoice pool")

            pi_gen = make_purchase_invoices_from_pr_items(
                self.company,
                selected_items=[{"pri_name": pri_name, "this_qty": 10.0}],
                bill_no="TEST-INV-001",
                bill_date=nowdate(),
            )
            self.assertTrue(pi_gen["success"])
            pi_name = pi_gen["invoices"][0]["name"]

            # Submit generated PI
            pi_doc = frappe.get_doc("Purchase Invoice", pi_name)
            pi_doc.submit()

            # --- Stage 4: Query PI pool & Generate Reimbursement Request ---
            pi_pool = get_pending_reimbursement_invoices(self.company)
            found_pi = [r for r in pi_pool["rows"] if r["pi_name"] == pi_name]
            self.assertTrue(len(found_pi) > 0, "PI should appear in pending reimbursement pool")

            rr_gen = make_reimbursement_from_invoices(
                self.company,
                selected_invoices=[pi_name],
                purpose="选单全流程回归测试",
            )
            self.assertTrue(rr_gen["success"])
            rr_name = rr_gen["reimbursement_name"]
            self.assertTrue(bool(rr_name))

            # Verify reservation was made
            res_count = frappe.db.count("Reimbursement Source Reservation", {"reimbursement_request": rr_name})
            self.assertTrue(res_count > 0, "Reservation rows should be recorded")

        finally:
            # Rollback all test documents created in this transaction
            frappe.db.rollback()


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProcurementPicker)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
