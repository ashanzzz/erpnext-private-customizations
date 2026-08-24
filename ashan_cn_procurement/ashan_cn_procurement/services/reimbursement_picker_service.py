# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from ashan_cn_procurement.services.authorization_service import assert_company_access
from ashan_cn_procurement.services.procurement_picker_service import (
    get_user_procurement_companies,
)


def _resolve_companies(company: str | None = None) -> list[str]:
    """Resolve accessible companies list with server-side permission checks."""
    user_comps = get_user_procurement_companies()["companies"]
    if not user_comps:
        frappe.throw(_("当前账号未获得任何公司的访问权限。"))

    if not company or company == "All" or company == "全部公司":
        return user_comps

    assert_company_access(company)
    return [company]


def _meta_has(doctype: str, fieldname: str) -> bool:
    """Safely check if DocType has a field."""
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


# =========================================================================
# 1. KPI Aggregation for 报销申请 (现金报销)
# =========================================================================

@frappe.whitelist()
def get_reimbursement_picker_overview_kpis(company: str | None = None) -> dict:
    """Return aggregated KPI counts for 报销申请 workflow."""
    companies = _resolve_companies(company)

    # 1. 报销申请统计 (Reimbursement Request with custom_biz_mode in ('现金报销', '报销申请'))
    rr_stats = frappe.db.sql("""
        SELECT
            COUNT(name),
            COALESCE(SUM(total_amount), 0),
            COALESCE(SUM(outstanding_amount), 0)
        FROM `tabReimbursement Request`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '现金报销' OR custom_biz_mode = '报销申请')
    """, (companies,))[0]

    rr_total_count = rr_stats[0] or 0
    rr_grand_total = flt(rr_stats[1] or 0)
    rr_outstanding = flt(rr_stats[2] or 0)

    # 待结款报销单数
    pending_rr_count = frappe.db.sql("""
        SELECT COUNT(name)
        FROM `tabReimbursement Request`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '现金报销' OR custom_biz_mode = '报销申请')
          AND outstanding_amount > 0.0001
    """, (companies,))[0][0] or 0

    # 2. 垫付采购发票数
    pi_count = frappe.db.sql("""
        SELECT COUNT(name)
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '现金报销' OR custom_biz_mode = '报销申请')
    """, (companies,))[0][0] or 0

    # 3. 关联采购入库数
    pr_count = frappe.db.sql("""
        SELECT COUNT(name)
        FROM `tabPurchase Receipt`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '现金报销' OR custom_biz_mode = '报销申请')
    """, (companies,))[0][0] or 0

    return {
        "pending_rr_count": pending_rr_count,
        "rr_total_count": rr_total_count,
        "rr_grand_total": rr_grand_total,
        "rr_outstanding": rr_outstanding,
        "pi_count": pi_count,
        "pr_count": pr_count,
    }


# =========================================================================
# 2. Query Detail & Doc Summary Rows for 报销申请
# =========================================================================

@frappe.whitelist()
def get_reimbursement_picker_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query item detail rows for 报销申请."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    match_status = filters.get("match_status") or "pending"

    conditions = [
        "rr.docstatus = 1",
        "rr.company IN %(companies)s",
        "(rr.custom_biz_mode = '现金报销' OR rr.custom_biz_mode = '报销申请')",
    ]
    params: dict[str, Any] = {"companies": companies}

    if match_status == "pending":
        conditions.append("rr.outstanding_amount > 0.0001")
    elif match_status == "completed":
        conditions.append("rr.outstanding_amount <= 0.0001")

    if filters.get("employee"):
        conditions.append("(rr.employee LIKE %(employee)s OR rr.employee_name LIKE %(employee)s)")
        params["employee"] = f"%{filters['employee']}%"

    if filters.get("supplier"):
        conditions.append("rii.supplier LIKE %(supplier)s")
        params["supplier"] = f"%{filters['supplier']}%"

    if filters.get("invoice_no"):
        conditions.append("rii.invoice_no LIKE %(invoice_no)s")
        params["invoice_no"] = f"%{filters['invoice_no']}%"

    if filters.get("item_code"):
        conditions.append("(rii.item_name LIKE %(item_code)s OR rii.description LIKE %(item_code)s)")
        params["item_code"] = f"%{filters['item_code']}%"

    if filters.get("owner"):
        conditions.append("rr.owner LIKE %(owner)s")
        params["owner"] = f"%{filters['owner']}%"

    where_clause = " AND ".join(conditions)

    has_inv_type = _meta_has("Reimbursement Invoice Item", "invoice_type")
    inv_type_col = "COALESCE(rii.invoice_type, '专用发票')" if has_inv_type else "'专用发票'"
    has_inv_date = _meta_has("Reimbursement Invoice Item", "invoice_date")
    inv_date_col = "COALESCE(rii.invoice_date, rr.posting_date)" if has_inv_date else "rr.posting_date"
    has_tax_rate = _meta_has("Reimbursement Invoice Item", "tax_rate")
    tax_rate_col = "COALESCE(rii.tax_rate, 13.0)" if has_tax_rate else "13.0"
    has_tax_amt = _meta_has("Reimbursement Invoice Item", "tax_amount")
    tax_amt_col = "COALESCE(rii.tax_amount, 0)" if has_tax_amt else "0"
    has_remark = _meta_has("Reimbursement Invoice Item", "custom_line_remark")
    remark_col = "COALESCE(rii.custom_line_remark, '')" if has_remark else "''"

    sql = f"""
        SELECT
            rii.name AS rii_name,
            rr.name AS rr_name,
            rr.company,
            COALESCE(rr.employee, '') AS employee,
            COALESCE(rr.employee_name, '') AS employee_name,
            COALESCE(rii.supplier, '') AS supplier,
            COALESCE(rii.invoice_no, '') AS invoice_no,
            {inv_type_col} AS invoice_type,
            {inv_date_col} AS invoice_date,
            rr.posting_date,
            rr.owner,
            rr.outstanding_amount,
            rr.total_amount AS rr_total_amount,
            rii.item_name,
            COALESCE(rii.description, '') AS description,
            {remark_col} AS remarks,
            COALESCE(rii.qty, 1) AS qty,
            COALESCE(rii.rate, 0) AS rate,
            COALESCE(rii.amount, 0) AS amount,
            {tax_rate_col} AS tax_rate,
            {tax_amt_col} AS tax_amount,
            COALESCE(rii.source_pi, '') AS source_pi
        FROM `tabReimbursement Invoice Item` rii
        INNER JOIN `tabReimbursement Request` rr ON rr.name = rii.parent
        WHERE {where_clause}
        ORDER BY rr.posting_date DESC, rr.name DESC, rii.idx ASC
        LIMIT 1000
    """

    raw_items = frappe.db.sql(sql, params, as_dict=True)

    rows = []
    for idx, it in enumerate(raw_items, 1):
        outstanding = flt(it.outstanding_amount)
        status_label = "🟡 待结款" if outstanding > 0.0001 else "🟢 已结清"
        amt = flt(it.amount, 2)

        rows.append({
            "idx": idx,
            "rii_name": it.rii_name,
            "rr_name": it.rr_name,
            "company": it.company,
            "employee": it.employee,
            "employee_name": it.employee_name,
            "supplier": it.supplier,
            "invoice_no": it.invoice_no,
            "invoice_type": it.invoice_type,
            "invoice_date": str(it.invoice_date or "")[:10],
            "posting_date": str(it.posting_date or "")[:10],
            "owner": it.owner,
            "status_label": status_label,
            "item_name": it.item_name,
            "spec": it.description or "",
            "remarks": it.remarks or "",
            "qty": flt(it.qty, 4),
            "rate": flt(it.rate, 2),
            "amount": amt,
            "tax_rate": flt(it.tax_rate, 2),
            "tax_amount": flt(it.tax_amount, 2),
            "total_amount": amt,
            "source_pi": it.source_pi or "-",
            "outstanding_amount": outstanding,
        })

    return {
        "rows": rows,
        "total_count": len(rows),
        "total_qty": sum(r["qty"] for r in rows),
        "total_amount": sum(r["amount"] for r in rows),
        "total_tax": sum(r["tax_amount"] for r in rows),
        "total_outstanding": sum(r["outstanding_amount"] for r in rows),
    }


@frappe.whitelist()
def get_reimbursement_picker_doc_summary_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query document level summary rows for 报销申请."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    match_status = filters.get("match_status") or "pending"

    conditions = [
        "rr.docstatus = 1",
        "rr.company IN %(companies)s",
        "(rr.custom_biz_mode = '现金报销' OR rr.custom_biz_mode = '报销申请')",
    ]
    params: dict[str, Any] = {"companies": companies}

    if match_status == "pending":
        conditions.append("rr.outstanding_amount > 0.0001")
    elif match_status == "completed":
        conditions.append("rr.outstanding_amount <= 0.0001")

    if filters.get("employee"):
        conditions.append("(rr.employee LIKE %(employee)s OR rr.employee_name LIKE %(employee)s)")
        params["employee"] = f"%{filters['employee']}%"

    if filters.get("supplier"):
        conditions.append("""
            EXISTS (
                SELECT 1 FROM `tabReimbursement Invoice Item` rii_s
                WHERE rii_s.parent = rr.name AND rii_s.supplier LIKE %(supplier)s
            )
        """)
        params["supplier"] = f"%{filters['supplier']}%"

    if filters.get("invoice_no"):
        conditions.append("""
            EXISTS (
                SELECT 1 FROM `tabReimbursement Invoice Item` rii_s
                WHERE rii_s.parent = rr.name AND rii_s.invoice_no LIKE %(invoice_no)s
            )
        """)
        params["invoice_no"] = f"%{filters['invoice_no']}%"

    if filters.get("owner"):
        conditions.append("rr.owner LIKE %(owner)s")
        params["owner"] = f"%{filters['owner']}%"

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            rr.name AS rr_name,
            rr.company,
            COALESCE(rr.employee, '') AS employee,
            COALESCE(rr.employee_name, '') AS employee_name,
            rr.posting_date,
            rr.owner,
            rr.total_amount,
            rr.outstanding_amount,
            COALESCE(rr.custom_doc_details, '') AS doc_details,
            (
                SELECT COUNT(rii.name)
                FROM `tabReimbursement Invoice Item` rii
                WHERE rii.parent = rr.name
            ) AS item_count,
            (
                SELECT GROUP_CONCAT(DISTINCT rii.supplier ORDER BY rii.supplier DESC SEPARATOR '、')
                FROM `tabReimbursement Invoice Item` rii
                WHERE rii.parent = rr.name AND rii.supplier IS NOT NULL AND rii.supplier != ''
            ) AS suppliers,
            (
                SELECT GROUP_CONCAT(DISTINCT rii.invoice_no ORDER BY rii.invoice_no DESC SEPARATOR '、')
                FROM `tabReimbursement Invoice Item` rii
                WHERE rii.parent = rr.name AND rii.invoice_no IS NOT NULL AND rii.invoice_no != ''
            ) AS invoice_nos,
            (
                SELECT GROUP_CONCAT(DISTINCT rii.source_pi ORDER BY rii.source_pi DESC SEPARATOR '、')
                FROM `tabReimbursement Invoice Item` rii
                WHERE rii.parent = rr.name AND rii.source_pi IS NOT NULL AND rii.source_pi != ''
            ) AS linked_pis
        FROM `tabReimbursement Request` rr
        WHERE {where_clause}
        ORDER BY rr.posting_date DESC, rr.name DESC
        LIMIT 500
    """

    raw_docs = frappe.db.sql(sql, params, as_dict=True)

    rows = []
    for idx, d in enumerate(raw_docs, 1):
        outstanding = flt(d.outstanding_amount)
        status_label = "🟡 待结款" if outstanding > 0.0001 else "🟢 已结清"

        rows.append({
            "idx": idx,
            "rr_name": d.rr_name,
            "company": d.company,
            "employee": d.employee,
            "employee_name": d.employee_name,
            "suppliers": d.suppliers or "-",
            "invoice_nos": d.invoice_nos or "-",
            "status_label": status_label,
            "posting_date": str(d.posting_date or ""),
            "owner": d.owner,
            "item_count": int(d.item_count or 0),
            "total_amount": flt(d.total_amount, 2),
            "outstanding_amount": outstanding,
            "paid_amount": max(0.0, flt(d.total_amount) - outstanding),
            "doc_details": d.doc_details or "-",
            "linked_pis": d.linked_pis or "-",
        })

    return {
        "rows": rows,
        "total_count": len(rows),
        "total_amount": sum(r["total_amount"] for r in rows),
        "total_outstanding": sum(r["outstanding_amount"] for r in rows),
    }


# =========================================================================
# 3. Reimbursement Fast Creation Engine (PO + PR + PI + RR Auto Bundle)
# =========================================================================

def _ensure_supplier(supplier_name: str) -> str:
    """Ensure supplier exists in ERPNext Supplier DocType, create if missing."""
    supplier_name = (supplier_name or "").strip()
    if not supplier_name:
        return "其它供应商"
    if not frappe.db.exists("Supplier", supplier_name):
        supp_doc = frappe.new_doc("Supplier")
        supp_doc.supplier_name = supplier_name
        supp_doc.supplier_group = "All Supplier Groups"
        supp_doc.flags.ignore_permissions = True
        supp_doc.insert()
        return supp_doc.name
    return supplier_name


@frappe.whitelist(methods=["POST"])
def create_self_service_reimbursement_bundle(
    company: str,
    employee: str | None = None,
    supplier: str | None = None,
    bill_no: str | None = None,
    bill_date: str | None = None,
    invoice_type: str | None = "专用发票",
    warehouse: str | None = None,
    auto_receive_stock: int | bool = 1,
    items: list[dict] | str | None = None,
) -> dict:
    """Reimbursement-driven fast creation of PO + PR(stock items) + PI + RR with custom_biz_mode='现金报销'."""
    assert_company_access(company)

    if isinstance(items, str):
        items = json.loads(items) or []
    if not items:
        frappe.throw(_("请录入至少一行有效的报销物料明细。"))

    auto_receive_stock = bool(int(auto_receive_stock))
    bill_date_str = bill_date or nowdate()
    supplier_val = _ensure_supplier(supplier)
    bill_no_val = bill_no.strip() if bill_no else f"REIM-INV-{nowdate().replace('-', '')}"

    # Resolve Employee
    emp_doc_name = None
    if employee:
        emp_match = frappe.db.get_value("Employee", {"name": employee}, "name") or frappe.db.get_value("Employee", {"employee_name": employee}, "name")
        if emp_match:
            emp_doc_name = emp_match

    if not emp_doc_name:
        user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "company": company}, "name")
        emp_doc_name = user_emp or frappe.db.get_value("Employee", {"company": company}, "name") or ""

    employee_name = ""
    if emp_doc_name:
        employee_name = frappe.db.get_value("Employee", emp_doc_name, "employee_name") or ""

    # Resolve Default Warehouse
    if not warehouse:
        if frappe.db.exists("Warehouse", f"Goods In Transit - {company}"):
            warehouse = f"Goods In Transit - {company}"
        elif frappe.db.exists("Warehouse", f"Stores - {company}"):
            warehouse = f"Stores - {company}"
        else:
            wh_list = frappe.get_all("Warehouse", filters={"company": company, "is_group": 0}, limit=1)
            warehouse = wh_list[0].name if wh_list else ""

    # Validate items
    validated_items = []
    has_stock_items = False

    for idx, row in enumerate(items, 1):
        item_code = (row.get("item_code") or "").strip()
        if not item_code:
            frappe.throw(_("第 {0} 行物料编码不能为空。").format(idx))

        item_meta = frappe.db.get_value(
            "Item",
            item_code,
            ["item_name", "stock_uom", "is_stock_item", "item_group", "description"],
            as_dict=True,
        )
        if not item_meta:
            frappe.throw(_("第 {0} 行物料 [{1}] 在系统中不存在。").format(idx, item_code))

        qty = flt(row.get("qty") or 0.0)
        rate = flt(row.get("rate") or 0.0)
        amount = flt(row.get("amount") or (qty * rate))

        if qty <= 0 or rate <= 0 or amount <= 0:
            frappe.throw(
                _("第 {0} 行物料 [{1}] 的数量({2})、单价(¥{3:.2f})或金额(¥{4:.2f})必须大于0！根据财务纪律，单价与金额严禁为0。").format(
                    idx, item_code, qty, rate, amount
                )
            )

        tax_rate = flt(row.get("tax_rate") or 13.0)
        tax_amount = flt(row.get("tax_amount") or (amount * (tax_rate / 100.0)))
        total_amount = flt(row.get("total_amount") or (amount + tax_amount))

        item_wh = (row.get("warehouse") or "").strip() or warehouse

        is_stock = bool(item_meta.is_stock_item)
        if is_stock:
            has_stock_items = True

        validated_items.append({
            "idx": idx,
            "item_code": item_code,
            "item_name": (row.get("item_name") or "").strip() or item_meta.item_name,
            "spec": (row.get("spec") or "").strip(),
            "uom": (row.get("uom") or "").strip() or item_meta.stock_uom or "Nos",
            "qty": qty,
            "rate": rate,
            "amount": amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "warehouse": item_wh,
            "remarks": (row.get("remarks") or "").strip(),
            "is_stock_item": is_stock,
        })

    # 1. Create Purchase Order (Submitted)
    po = frappe.new_doc("Purchase Order")
    po.company = company
    po.supplier = supplier_val
    po.transaction_date = bill_date_str
    po.schedule_date = bill_date_str
    po.custom_biz_mode = "现金报销"

    for it in validated_items:
        po_row = po.append("items", {
            "item_code": it["item_code"],
            "item_name": it["item_name"],
            "uom": it["uom"],
            "stock_uom": it["uom"],
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": it["amount"],
            "schedule_date": bill_date_str,
            "warehouse": it["warehouse"],
            "description": it["remarks"] or it["item_name"],
        })
        if _meta_has("Purchase Order Item", "custom_spec_model"):
            po_row.custom_spec_model = it["spec"]
        if _meta_has("Purchase Order Item", "custom_line_remark"):
            po_row.custom_line_remark = it["remarks"]
        if _meta_has("Purchase Order Item", "custom_tax_rate"):
            po_row.custom_tax_rate = it["tax_rate"]
        if _meta_has("Purchase Order Item", "custom_tax_amount"):
            po_row.custom_tax_amount = it["tax_amount"]
        if _meta_has("Purchase Order Item", "custom_total_amount"):
            po_row.custom_total_amount = it["total_amount"]

    po.flags.ignore_permissions = True
    po.insert()
    po.submit()

    # 2. Create Purchase Receipt (Submitted, if stock items present and auto_receive_stock is True)
    pr_name = None
    pr_item_map = {}
    if auto_receive_stock and has_stock_items:
        pr = frappe.new_doc("Purchase Receipt")
        pr.company = company
        pr.supplier = supplier_val
        pr.posting_date = bill_date_str
        pr.custom_biz_mode = "现金报销"

        for idx, it in enumerate(validated_items):
            if not it["is_stock_item"]:
                continue
            po_item_row = po.items[idx]
            pr_row = pr.append("items", {
                "item_code": it["item_code"],
                "item_name": it["item_name"],
                "uom": it["uom"],
                "stock_uom": it["uom"],
                "qty": it["qty"],
                "rate": it["rate"],
                "amount": it["amount"],
                "warehouse": it["warehouse"],
                "purchase_order": po.name,
                "purchase_order_item": po_item_row.name,
                "description": it["remarks"] or it["item_name"],
            })
            if _meta_has("Purchase Receipt Item", "custom_spec_model"):
                pr_row.custom_spec_model = it["spec"]
            if _meta_has("Purchase Receipt Item", "custom_line_remark"):
                pr_row.custom_line_remark = it["remarks"]
            if _meta_has("Purchase Receipt Item", "custom_tax_rate"):
                pr_row.custom_tax_rate = it["tax_rate"]
            if _meta_has("Purchase Receipt Item", "custom_tax_amount"):
                pr_row.custom_tax_amount = it["tax_amount"]
            if _meta_has("Purchase Receipt Item", "custom_total_amount"):
                pr_row.custom_total_amount = it["total_amount"]

        if pr.items:
            pr.flags.ignore_permissions = True
            pr.insert()
            pr.submit()
            pr_name = pr.name
            for p_item in pr.items:
                pr_item_map[p_item.item_code] = p_item.name

    # 3. Create Purchase Invoice (Submitted)
    pi = frappe.new_doc("Purchase Invoice")
    pi.company = company
    pi.supplier = supplier_val
    pi.bill_no = bill_no_val
    pi.bill_date = bill_date_str
    pi.posting_date = bill_date_str
    pi.custom_biz_mode = "现金报销"
    if _meta_has("Purchase Invoice", "custom_invoice_type"):
        pi.custom_invoice_type = invoice_type or "专用发票"

    for idx, it in enumerate(validated_items):
        po_item_row = po.items[idx]
        pi_row = pi.append("items", {
            "item_code": it["item_code"],
            "item_name": it["item_name"],
            "uom": it["uom"],
            "stock_uom": it["uom"],
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": it["amount"],
            "purchase_order": po.name,
            "po_detail": po_item_row.name,
            "purchase_receipt": pr_name if (it["is_stock_item"] and pr_name) else None,
            "pr_detail": pr_item_map.get(it["item_code"]) if (it["is_stock_item"] and pr_name) else None,
            "description": it["remarks"] or it["item_name"],
        })
        if _meta_has("Purchase Invoice Item", "custom_spec_model"):
            pi_row.custom_spec_model = it["spec"]
        if _meta_has("Purchase Invoice Item", "custom_line_remark"):
            pi_row.custom_line_remark = it["remarks"]
        if _meta_has("Purchase Invoice Item", "custom_tax_rate"):
            pi_row.custom_tax_rate = it["tax_rate"]
        if _meta_has("Purchase Invoice Item", "custom_tax_amount"):
            pi_row.custom_tax_amount = it["tax_amount"]
        if _meta_has("Purchase Invoice Item", "custom_total_amount"):
            pi_row.custom_total_amount = it["total_amount"]

    pi.flags.ignore_permissions = True
    pi.insert()
    pi.submit()

    # 4. Create Reimbursement Request (Submitted)
    rr = frappe.new_doc("Reimbursement Request")
    rr.company = company
    rr.title = f"报销申请-{employee_name or '员工'}-{bill_no_val}"
    if emp_doc_name:
        rr.employee = emp_doc_name
    if employee_name:
        rr.employee_name = employee_name
    rr.posting_date = bill_date_str
    rr.custom_biz_mode = "现金报销"

    for it in validated_items:
        row_dict = {
            "item_name": it["item_name"],
            "description": it["spec"],
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": it["total_amount"],  # 报销金额为价税合计
            "invoice_no": bill_no_val,
            "supplier": supplier_val,
            "source_pi": pi.name,
        }
        if _meta_has("Reimbursement Invoice Item", "custom_line_remark"):
            row_dict["custom_line_remark"] = it["remarks"]
        if _meta_has("Reimbursement Invoice Item", "invoice_type"):
            row_dict["invoice_type"] = invoice_type or "专用发票"
        if _meta_has("Reimbursement Invoice Item", "invoice_date"):
            row_dict["invoice_date"] = bill_date_str
        if _meta_has("Reimbursement Invoice Item", "tax_rate"):
            row_dict["tax_rate"] = it["tax_rate"]
        if _meta_has("Reimbursement Invoice Item", "tax_amount"):
            row_dict["tax_amount"] = it["tax_amount"]

        rr.append("invoice_items", row_dict)

    rr.flags.ignore_permissions = True
    rr.insert()
    rr.submit()

    # Refresh custom_doc_details
    try:
        from ashan_cn_procurement.overrides.document_details import update_doc_details
        update_doc_details(po)
        if po.get("custom_doc_details"):
            frappe.db.set_value("Purchase Order", po.name, "custom_doc_details", po.custom_doc_details, update_modified=False)
        if pr_name:
            pr_doc = frappe.get_doc("Purchase Receipt", pr_name)
            update_doc_details(pr_doc)
            if pr_doc.get("custom_doc_details"):
                frappe.db.set_value("Purchase Receipt", pr_name, "custom_doc_details", pr_doc.custom_doc_details, update_modified=False)
        update_doc_details(pi)
        if pi.get("custom_doc_details"):
            frappe.db.set_value("Purchase Invoice", pi.name, "custom_doc_details", pi.custom_doc_details, update_modified=False)
        update_doc_details(rr)
        if rr.get("custom_doc_details"):
            frappe.db.set_value("Reimbursement Request", rr.name, "custom_doc_details", rr.custom_doc_details, update_modified=False)
    except Exception:
        pass

    return {
        "success": True,
        "po_name": po.name,
        "pr_name": pr_name,
        "pi_name": pi.name,
        "rr_name": rr.name,
        "company": company,
        "supplier": supplier_val,
        "employee": employee,
        "grand_total": flt(rr.total_amount, 2),
    }
