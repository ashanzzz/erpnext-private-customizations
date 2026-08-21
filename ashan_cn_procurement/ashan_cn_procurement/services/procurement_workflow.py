"""Read-only procurement workflow summary for the Desk workbench.

This module never writes accounting or stock data. It only reads documents
that the current user is permitted to see and returns a compact workflow
summary for navigation.
"""

from __future__ import annotations

import frappe
from frappe.utils import flt


def _meta_has(doctype: str, fieldname: str) -> bool:
    try:
        return bool(frappe.get_meta(doctype).has_field(fieldname))
    except Exception:
        return False


def _resolve_company(company: str | None) -> str | None:
    company = (company or "").strip()
    if company:
        if frappe.db.exists("Company", company):
            return company
        frappe.throw(frappe._("公司不存在：{0}").format(company))

    default_company = frappe.defaults.get_user_default("Company")
    if default_company and frappe.db.exists("Company", default_company):
        return default_company

    companies = frappe.get_list(
        "Company",
        fields=["name"],
        order_by="name asc",
        page_length=1,
    )
    return companies[0].name if companies else None


def _safe_rows(
    doctype: str,
    company: str | None,
    extra_filters: dict | None = None,
    fields: list[str] | None = None,
) -> list:
    if not frappe.db.exists("DocType", doctype):
        return []
    if not frappe.has_permission(doctype, "read"):
        return []

    filters = dict(extra_filters or {})
    if company and _meta_has(doctype, "company"):
        filters["company"] = company

    requested_fields = ["name"]
    for fieldname in fields or []:
        if fieldname == "name" or _meta_has(doctype, fieldname):
            if fieldname not in requested_fields:
                requested_fields.append(fieldname)

    try:
        return frappe.get_list(
            doctype,
            filters=filters,
            fields=requested_fields,
            order_by="modified desc",
            page_length=5000,
        )
    except Exception:
        frappe.log_error(
            title=f"Procurement workflow read failed: {doctype}",
            message=frappe.get_traceback(),
        )
        return []


def _submitted_open_rows(
    doctype: str,
    company: str | None,
    progress_field: str | None = None,
    extra_filters: dict | None = None,
    amount_field: str | None = None,
) -> tuple[list, float]:
    filters = {"docstatus": 1}
    filters.update(extra_filters or {})

    if progress_field and _meta_has(doctype, progress_field):
        filters[progress_field] = ["<", 100]

    fields = [amount_field] if amount_field else []
    rows = _safe_rows(doctype, company, filters, fields)
    total = sum(flt(row.get(amount_field)) for row in rows) if amount_field else 0.0
    return rows, total


def _reimbursement_rows(company: str | None) -> tuple[list, float]:
    rows = _safe_rows(
        "Reimbursement Request",
        company,
        {},
        ["payment_status", "outstanding_amount", "total_amount"],
    )

    active = []
    amount = 0.0
    for row in rows:
        status = (row.get("payment_status") or "").strip()
        outstanding = flt(row.get("outstanding_amount"))
        total_amount = flt(row.get("total_amount"))

        if status == "已付款":
            continue
        if outstanding <= 0 and total_amount <= 0:
            continue

        active.append(row)
        amount += outstanding if outstanding > 0 else total_amount

    return active, amount


@frappe.whitelist()
def get_procurement_workflow_summary(company: str | None = None) -> dict:
    """Return permission-aware counts for the five-step procurement flow."""
    company = _resolve_company(company)

    mr_filters = {}
    if _meta_has("Material Request", "material_request_type"):
        mr_filters["material_request_type"] = "Purchase"

    mr_rows, _ = _submitted_open_rows(
        "Material Request",
        company,
        progress_field="per_ordered",
        extra_filters=mr_filters,
    )
    po_rows, _ = _submitted_open_rows(
        "Purchase Order",
        company,
        progress_field="per_received",
    )
    pr_rows, _ = _submitted_open_rows(
        "Purchase Receipt",
        company,
        progress_field="per_billed",
    )
    pi_rows, pi_outstanding = _submitted_open_rows(
        "Purchase Invoice",
        company,
        extra_filters={"outstanding_amount": [">", 0]}
        if _meta_has("Purchase Invoice", "outstanding_amount")
        else None,
        amount_field="outstanding_amount",
    )
    rr_rows, rr_outstanding = _reimbursement_rows(company)

    return {
        "company": company,
        "stages": [
            {
                "key": "material_request",
                "number": 1,
                "label": "采购申请",
                "doctype": "Material Request",
                "count": len(mr_rows),
                "count_label": "待转订单",
                "amount": None,
            },
            {
                "key": "purchase_order",
                "number": 2,
                "label": "采购订单",
                "doctype": "Purchase Order",
                "count": len(po_rows),
                "count_label": "待收货",
                "amount": None,
            },
            {
                "key": "purchase_receipt",
                "number": 3,
                "label": "采购入库",
                "doctype": "Purchase Receipt",
                "count": len(pr_rows),
                "count_label": "待开票",
                "amount": None,
            },
            {
                "key": "purchase_invoice",
                "number": 4,
                "label": "采购发票",
                "doctype": "Purchase Invoice",
                "count": len(pi_rows),
                "count_label": "待付款",
                "amount": pi_outstanding,
            },
            {
                "key": "reimbursement",
                "number": 5,
                "label": "报销申请",
                "doctype": "Reimbursement Request",
                "count": len(rr_rows),
                "count_label": "待处理",
                "amount": rr_outstanding,
            },
        ],
    }
