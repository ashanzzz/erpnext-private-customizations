# Copyright (c) 2026, Ashan CN Procurement
"""Automated regression & end-to-end test suite for Procurement Order Picker (5 Steps, Dual Views & Quick Creation)."""

import unittest
import frappe
from frappe.utils import nowdate, flt, random_string

from ashan_cn_procurement.services.procurement_picker_service import (
    get_user_procurement_companies,
    get_material_request_picker_rows,
    get_material_request_doc_rows,
    quick_create_material_request,
    get_item_master_picker_rows,
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

    def test_01_user_companies_and_kpis(self):
        """Verify get_user_procurement_companies and 5-step overview KPIs."""
        user_comps = get_user_procurement_companies()
        self.assertIn("companies", user_comps)
        self.assertTrue(len(user_comps["companies"]) >= 1)

        # Test KPI with "All"
        res_all = get_procurement_picker_overview_kpis("All")
        self.assertIn("kpis", res_all)
        self.assertIn("item_to_mr", res_all["kpis"])
        self.assertIn("mr_to_po", res_all["kpis"])
        self.assertIn("po_to_pr", res_all["kpis"])
        self.assertIn("pr_to_pi", res_all["kpis"])
        self.assertIn("pi_to_rr", res_all["kpis"])

    def test_02_query_endpoints_smoke(self):
        """Verify query endpoints execute without SQL or permission errors for All and single company."""
        for comp_scope in ["All", self.company]:
            mr_items = get_material_request_picker_rows(comp_scope)
            self.assertIn("rows", mr_items)

            mr_docs = get_material_request_doc_rows(comp_scope)
            self.assertIn("rows", mr_docs)

            mr_res = get_pending_material_request_items(comp_scope)
            self.assertIn("rows", mr_res)

            po_res = get_pending_purchase_order_items(comp_scope)
            self.assertIn("rows", po_res)

            pr_res = get_pending_purchase_receipt_items(comp_scope)
            self.assertIn("rows", pr_res)

            rr_res = get_pending_reimbursement_invoices(comp_scope)
            self.assertIn("rows", rr_res)

    def test_03_quick_create_and_full_lifecycle(self):
        """Test quick Material Request creation, dual view queries, and downstream flow."""
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

        # --- Step 1: Quick Create Material Request via Dialog RPC ---
        mr_res = quick_create_material_request(
            company=self.company,
            department="生产部",
            schedule_date=nowdate(),
            items=[{
                "item_code": item_code,
                "qty": 20.0,
                "description": "物料申请弹窗测试",
            }],
        )
        self.assertTrue(mr_res["success"])
        mr_name = mr_res["name"]

        # Verify Step 1 Detail View returns this MR item with mr_name
        detail_pool = get_material_request_picker_rows(self.company, {"mr_name": mr_name})
        self.assertTrue(len(detail_pool["rows"]) > 0)
        self.assertEqual(detail_pool["rows"][0]["mr_name"], mr_name)
        self.assertEqual(detail_pool["rows"][0]["qty"], 20.0)

        # Verify Step 1 Doc View returns this MR
        doc_pool = get_material_request_doc_rows(self.company, {"mr_name": mr_name})
        self.assertTrue(len(doc_pool["rows"]) > 0)
        self.assertEqual(doc_pool["rows"][0]["mr_name"], mr_name)

        # Submit MR
        mr_doc = frappe.get_doc("Material Request", mr_name)
        mr_doc.submit()
        mri_name = mr_doc.items[0].name

        try:
            # --- Step 2: Material Request -> Purchase Order ---
            mr_pool = get_pending_material_request_items(self.company)
            found_mr = [r for r in mr_pool["rows"] if r["mri_name"] == mri_name]
            self.assertTrue(len(found_mr) > 0, "Material request item should appear in pending order pool")
            self.assertEqual(found_mr[0]["pending_qty"], 20.0)

            po_gen = make_purchase_orders_from_mr_items(
                self.company,
                selected_items=[{"mri_name": mri_name, "this_qty": 20.0, "rate": 50.0}],
                supplier_override=supplier,
            )
            self.assertTrue(po_gen["success"])
            po_name = po_gen["orders"][0]["name"]

            po_doc = frappe.get_doc("Purchase Order", po_name)
            po_doc.submit()
            poi_name = po_doc.items[0].name

            # --- Step 3: Purchase Order -> Purchase Receipt ---
            po_pool = get_pending_purchase_order_items(self.company, {"supplier": supplier})
            found_po = [r for r in po_pool["rows"] if r["poi_name"] == poi_name]
            self.assertTrue(len(found_po) > 0, "PO item should appear in pending receipt pool")

            pr_gen = make_purchase_receipts_from_po_items(
                self.company,
                selected_items=[{"poi_name": poi_name, "this_qty": 20.0, "warehouse": warehouse}],
            )
            self.assertTrue(pr_gen["success"])
            pr_name = pr_gen["receipts"][0]["name"]

            pr_doc = frappe.get_doc("Purchase Receipt", pr_name)
            pr_doc.submit()
            pri_name = pr_doc.items[0].name

            # --- Step 4: Purchase Receipt -> Purchase Invoice ---
            pr_pool = get_pending_purchase_receipt_items(self.company, {"supplier": supplier})
            found_pr = [r for r in pr_pool["rows"] if r["pri_name"] == pri_name]
            self.assertTrue(len(found_pr) > 0, "PR item should appear in pending invoice pool")

            pi_gen = make_purchase_invoices_from_pr_items(
                self.company,
                selected_items=[{"pri_name": pri_name, "this_qty": 20.0}],
                bill_no="TEST-AUTO-INV-003",
                bill_date=nowdate(),
            )
            self.assertTrue(pi_gen["success"])
            pi_name = pi_gen["invoices"][0]["name"]

            pi_doc = frappe.get_doc("Purchase Invoice", pi_name)
            pi_doc.submit()

            # --- Step 5: Purchase Invoice -> Reimbursement Request ---
            pi_pool = get_pending_reimbursement_invoices(self.company)
            found_pi = [r for r in pi_pool["rows"] if r["pi_name"] == pi_name]
            self.assertTrue(len(found_pi) > 0, "PI should appear in pending reimbursement pool")

            rr_gen = make_reimbursement_from_invoices(
                self.company,
                selected_invoices=[pi_name],
                purpose="5步全流程端到端测试",
            )
            self.assertTrue(rr_gen["success"])
            rr_name = rr_gen["reimbursement_name"]
            self.assertTrue(bool(rr_name))

            # Verify reservation
            res_count = frappe.db.count("Reimbursement Source Reservation", {"reimbursement_request": rr_name})
            self.assertTrue(res_count > 0, "Source reservation records must exist")

        finally:
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
