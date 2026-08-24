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
# 1. KPI Aggregation for 自办电汇
# =========================================================================

@frappe.whitelist()
def get_wire_transfer_overview_kpis(company: str | None = None) -> dict:
    """Return aggregated KPI counts for 自办电汇 workflow."""
    companies = _resolve_companies(company)

    # 1. 自办发票总数 (Purchase Invoice with custom_biz_mode = '自办电汇' or related)
    pi_stats = frappe.db.sql("""
        SELECT COUNT(name), COALESCE(SUM(outstanding_amount), 0), COALESCE(SUM(grand_total), 0)
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '自办电汇' OR custom_biz_mode = '电汇申请')
    """, (companies,))[0]

    pi_total_count = pi_stats[0] or 0
    pi_outstanding = flt(pi_stats[1] or 0)
    pi_grand_total = flt(pi_stats[2] or 0)

    # 扣除报销预占
    active_res = []
    if frappe.db.exists("DocType", "Reimbursement Source Reservation"):
        active_res = frappe.get_all(
            "Reimbursement Source Reservation",
            filters={"status": ["in", ["Draft", "Submitted"]]},
            fields=["source_purchase_invoice", "reserved_amount"],
        )
    reserved_by_pi = defaultdict(float)
    for res in active_res:
        reserved_by_pi[res.source_purchase_invoice] += flt(res.reserved_amount)

    raw_pis = frappe.db.sql("""
        SELECT name, outstanding_amount
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '自办电汇' OR custom_biz_mode = '电汇申请')
          AND outstanding_amount > 0.0001
    """, (companies,), as_dict=True)

    pi_pending_pay_count = 0
    pi_pending_pay_amount = 0.0
    for pi_row in raw_pis:
        net_outstanding = max(0.0, flt(pi_row.outstanding_amount) - reserved_by_pi.get(pi_row.name, 0.0))
        if net_outstanding > 0.0001:
            pi_pending_pay_count += 1
            pi_pending_pay_amount += net_outstanding

    # 2. 采购订单数 (Purchase Order with custom_biz_mode = '自办电汇')
    po_count = frappe.db.sql("""
        SELECT COUNT(name)
        FROM `tabPurchase Order`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '自办电汇' OR custom_biz_mode = '电汇申请')
    """, (companies,))[0][0] or 0

    # 3. 采购入库单数 (Purchase Receipt with custom_biz_mode = '自办电汇')
    pr_count = frappe.db.sql("""
        SELECT COUNT(name)
        FROM `tabPurchase Receipt`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '自办电汇' OR custom_biz_mode = '电汇申请')
    """, (companies,))[0][0] or 0

    # 4. 电汇付款申请数 (Reimbursement Request with custom_biz_mode = '自办电汇')
    rr_count = frappe.db.sql("""
        SELECT COUNT(name)
        FROM `tabReimbursement Request`
        WHERE docstatus < 2
          AND company IN %s
          AND (custom_biz_mode = '自办电汇' OR custom_biz_mode = '电汇申请')
    """, (companies,))[0][0] or 0

    return {
        "companies": companies,
        "kpis": {
            "invoice": {"count": pi_total_count, "pending_count": pi_pending_pay_count, "label": "自办发票"},
            "order": {"count": po_count, "label": "自办订单"},
            "receipt": {"count": pr_count, "label": "自动入库"},
            "payment": {"count": pi_pending_pay_count, "amount": pi_pending_pay_amount, "label": "待电汇付款"},
        }
    }


# =========================================================================
# 2. Query Detail & Doc Summary Rows for 自办电汇
# =========================================================================

@frappe.whitelist()
def get_wire_transfer_picker_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query item detail rows for 自办电汇."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    match_status = filters.get("match_status") or "pending"

    conditions = [
        "pi.docstatus = 1",
        "pi.company IN %(companies)s",
        "(pi.custom_biz_mode = '自办电汇' OR pi.custom_biz_mode = '电汇申请')",
    ]
    params: dict[str, Any] = {"companies": companies}

    if match_status == "pending":
        conditions.append("pi.outstanding_amount > 0")
    elif match_status == "completed":
        conditions.append("pi.outstanding_amount <= 0.0001")

    if filters.get("supplier"):
        conditions.append("pi.supplier LIKE %(supplier)s")
        params["supplier"] = f"%{filters['supplier']}%"

    if filters.get("bill_no"):
        conditions.append("pi.bill_no LIKE %(bill_no)s")
        params["bill_no"] = f"%{filters['bill_no']}%"

    if filters.get("item_code"):
        conditions.append("(pii.item_code LIKE %(item_code)s OR pii.item_name LIKE %(item_code)s)")
        params["item_code"] = f"%{filters['item_code']}%"

    if filters.get("owner"):
        conditions.append("pi.owner LIKE %(owner)s")
        params["owner"] = f"%{filters['owner']}%"

    where_clause = " AND ".join(conditions)

    has_inv_type = _meta_has("Purchase Invoice", "custom_invoice_type")
    type_col = "COALESCE(pi.custom_invoice_type, '专用发票')" if has_inv_type else "'专用发票'"
    has_spec = _meta_has("Purchase Invoice Item", "custom_spec_model")
    spec_col = "COALESCE(pii.custom_spec_model, '')" if has_spec else "''"
    has_remark = _meta_has("Purchase Invoice Item", "custom_line_remark")
    remark_col = "COALESCE(pii.custom_line_remark, '')" if has_remark else "''"
    has_tax_rate = _meta_has("Purchase Invoice Item", "custom_tax_rate")
    tax_rate_col = "COALESCE(pii.custom_tax_rate, 13.0)" if has_tax_rate else "13.0"
    has_tax_amount = _meta_has("Purchase Invoice Item", "custom_tax_amount")
    tax_amount_col = "COALESCE(pii.custom_tax_amount, 0)" if has_tax_amount else "0"
    has_total_amount = _meta_has("Purchase Invoice Item", "custom_total_amount")
    total_amount_col = "COALESCE(pii.custom_total_amount, pii.amount, 0)" if has_total_amount else "COALESCE(pii.amount, 0)"

    sql = f"""
        SELECT
            pii.name AS pii_name,
            pi.name AS pi_name,
            pi.company,
            pi.supplier,
            COALESCE(pi.bill_no, '') AS bill_no,
            {type_col} AS invoice_type,
            pi.bill_date,
            pi.posting_date,
            pi.owner,
            pi.outstanding_amount,
            pi.grand_total,
            pii.item_code,
            pii.item_name,
            pii.description,
            {spec_col} AS spec,
            {remark_col} AS remarks,
            COALESCE(pii.uom, pii.stock_uom, '') AS uom,
            COALESCE(pii.qty, 1) AS qty,
            COALESCE(pii.rate, 0) AS rate,
            COALESCE(pii.amount, 0) AS amount,
            {tax_rate_col} AS tax_rate,
            {tax_amount_col} AS tax_amount,
            {total_amount_col} AS total_amount,
            COALESCE(pii.warehouse, '') AS warehouse,
            COALESCE(pii.purchase_order, '') AS purchase_order,
            COALESCE(pii.purchase_receipt, '') AS purchase_receipt,
            (
                SELECT GROUP_CONCAT(DISTINCT rii.parent ORDER BY rii.parent DESC SEPARATOR '、')
                FROM `tabReimbursement Invoice Item` rii
                INNER JOIN `tabReimbursement Request` rr_inner ON rr_inner.name = rii.parent
                WHERE rii.source_pi = pi.name AND rr_inner.docstatus < 2
            ) AS linked_rr_names
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pii.parent
        WHERE {where_clause}
        ORDER BY pi.posting_date DESC, pi.name DESC, pii.idx ASC
        LIMIT 1000
    """

    raw_items = frappe.db.sql(sql, params, as_dict=True)

    active_res = []
    if frappe.db.exists("DocType", "Reimbursement Source Reservation"):
        active_res = frappe.get_all(
            "Reimbursement Source Reservation",
            filters={"status": ["in", ["Draft", "Submitted"]]},
            fields=["source_purchase_invoice", "reserved_amount"],
        )
    reserved_by_pi = defaultdict(float)
    for res in active_res:
        reserved_by_pi[res.source_purchase_invoice] += flt(res.reserved_amount)

    rows = []
    for it in raw_items:
        reserved = reserved_by_pi.get(it.pi_name, 0.0)
        net_outstanding = max(0.0, flt(it.outstanding_amount) - reserved)
        if match_status == "pending" and net_outstanding <= 0.0001:
            continue

        rows.append({
            "pii_name": it.pii_name,
            "pi_name": it.pi_name,
            "company": it.company,
            "supplier": it.supplier,
            "bill_no": it.bill_no,
            "invoice_type": it.invoice_type,
            "bill_date": str(it.bill_date) if it.bill_date else "",
            "posting_date": str(it.posting_date) if it.posting_date else "",
            "item_code": it.item_code,
            "item_name": it.item_name or it.item_code,
            "spec": it.spec or (it.description if it.description and it.description != it.item_name else "") or "",
            "remarks": it.remarks or "",
            "uom": it.uom,
            "qty": flt(it.qty, 2),
            "rate": flt(it.rate, 2),
            "amount": flt(it.amount, 2),
            "tax_rate": flt(it.tax_rate, 2),
            "tax_amount": flt(it.tax_amount, 2),
            "total_amount": flt(it.total_amount, 2),
            "warehouse": it.warehouse,
            "purchase_order": it.purchase_order,
            "purchase_receipt": it.purchase_receipt,
            "net_available_amount": flt(net_outstanding, 2),
            "owner": it.owner or "",
            "linked_rr_names": it.linked_rr_names or "",
        })

    return {
        "companies": companies,
        "count": len(rows),
        "rows": rows,
    }


@frappe.whitelist()
def get_wire_transfer_doc_summary_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query doc-level summary rows for 自办电汇."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    match_status = filters.get("match_status") or "pending"

    conditions = [
        "pi.company IN %(companies)s",
        "pi.docstatus = 1",
        "(pi.custom_biz_mode = '自办电汇' OR pi.custom_biz_mode = '电汇申请')",
    ]
    params: dict[str, Any] = {"companies": companies}

    if match_status == "pending":
        conditions.append("pi.outstanding_amount > 0")
    elif match_status == "completed":
        conditions.append("pi.outstanding_amount <= 0.0001")

    if filters.get("supplier"):
        conditions.append("pi.supplier LIKE %(supplier)s")
        params["supplier"] = f"%{filters['supplier']}%"

    if filters.get("bill_no"):
        conditions.append("pi.bill_no LIKE %(bill_no)s")
        params["bill_no"] = f"%{filters['bill_no']}%"

    if filters.get("owner"):
        conditions.append("pi.owner LIKE %(owner)s")
        params["owner"] = f"%{filters['owner']}%"

    where_clause = " AND ".join(conditions)

    has_custom_doc_details = _meta_has("Purchase Invoice", "custom_doc_details")
    doc_details_col = "COALESCE(pi.custom_doc_details, '')" if has_custom_doc_details else "''"
    has_invoice_type = _meta_has("Purchase Invoice", "custom_invoice_type")
    type_col = "COALESCE(pi.custom_invoice_type, '专用发票')" if has_invoice_type else "'专用发票'"

    sql = f"""
        SELECT
            pi.name AS pi_name,
            pi.company,
            pi.supplier,
            COALESCE(pi.bill_no, '') AS bill_no,
            {type_col} AS invoice_type,
            pi.bill_date,
            pi.posting_date,
            pi.grand_total,
            pi.outstanding_amount,
            pi.owner,
            {doc_details_col} AS custom_doc_details,
            GROUP_CONCAT(DISTINCT pii.purchase_order SEPARATOR '、') AS linked_po_names,
            GROUP_CONCAT(DISTINCT pii.purchase_receipt SEPARATOR '、') AS linked_pr_names,
            GROUP_CONCAT(DISTINCT CONCAT(pii.item_name, ' (', ROUND(pii.qty, 2), ' ', COALESCE(pii.uom, pii.stock_uom, ''), ')') SEPARATOR '、') AS synthesized_details,
            COUNT(pii.name) AS item_count,
            SUM(pii.qty) AS total_qty,
            (
                SELECT GROUP_CONCAT(DISTINCT rii.parent ORDER BY rii.parent DESC SEPARATOR '、')
                FROM `tabReimbursement Invoice Item` rii
                INNER JOIN `tabReimbursement Request` rr_inner ON rr_inner.name = rii.parent
                WHERE rii.source_pi = pi.name AND rr_inner.docstatus < 2
            ) AS linked_rr_names
        FROM `tabPurchase Invoice` pi
        LEFT JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        WHERE {where_clause}
        GROUP BY pi.name
        ORDER BY pi.posting_date DESC, pi.name DESC
        LIMIT 1000
    """

    invoices = frappe.db.sql(sql, params, as_dict=True)

    active_res = []
    if frappe.db.exists("DocType", "Reimbursement Source Reservation"):
        active_res = frappe.get_all(
            "Reimbursement Source Reservation",
            filters={"status": ["in", ["Draft", "Submitted"]]},
            fields=["source_purchase_invoice", "reserved_amount"],
        )
    reserved_by_pi = defaultdict(float)
    for res in active_res:
        reserved_by_pi[res.source_purchase_invoice] += flt(res.reserved_amount)

    rows = []
    for inv in invoices:
        reserved = reserved_by_pi.get(inv.pi_name, 0.0)
        net_outstanding = max(0.0, flt(inv.outstanding_amount) - reserved)
        if match_status == "pending" and net_outstanding <= 0.0001:
            continue

        rows.append({
            "pi_name": inv.pi_name,
            "company": inv.company,
            "supplier": inv.supplier,
            "bill_no": inv.bill_no,
            "invoice_type": inv.invoice_type,
            "bill_date": str(inv.bill_date) if inv.bill_date else "",
            "posting_date": str(inv.posting_date) if inv.posting_date else "",
            "grand_total": flt(inv.grand_total, 2),
            "outstanding_amount": flt(inv.outstanding_amount, 2),
            "net_available_amount": flt(net_outstanding, 2),
            "custom_doc_details": inv.custom_doc_details or inv.synthesized_details or "",
            "item_count": inv.item_count or 0,
            "total_qty": flt(inv.total_qty or 0, 2),
            "linked_po_names": inv.linked_po_names or "",
            "linked_pr_names": inv.linked_pr_names or "",
            "linked_rr_names": inv.linked_rr_names or "",
            "owner": inv.owner or "",
        })

    return {
        "companies": companies,
        "count": len(rows),
        "rows": rows,
    }


# =========================================================================
# 3. Core Engine: Create Self-Service Wire Transfer Bundle (PO + PR + PI + [RR])
# =========================================================================

@frappe.whitelist(methods=["POST"])
def create_self_service_wire_transfer_bundle(
    company: str,
    supplier: str,
    bill_no: str,
    bill_date: str | None = None,
    invoice_type: str = "专用发票",
    warehouse: str | None = None,
    auto_receive_stock: int | bool = 1,
    create_reimbursement_request: int | bool = 0,
    applicant: str | None = None,
    items: str | list | None = None,
) -> dict:
    """One-click generation of 自办电汇 bundle: PO -> PR (if stock item) -> PI -> [RR]."""
    assert_company_access(company)

    if not supplier or not supplier.strip():
        frappe.throw(_("请提供有效的供应商名称。"))

    if not bill_no or not bill_no.strip():
        frappe.throw(_("发票号码不能为空，请输入发票号码。"))

    if isinstance(items, str):
        items = frappe.parse_json(items) or []
    items = list(items or [])

    if not items:
        frappe.throw(_("请录入至少一行有效的发票物料明细。"))

    auto_receive_stock = bool(int(auto_receive_stock))
    create_reimbursement_request = bool(int(create_reimbursement_request))
    bill_date_str = bill_date or nowdate()

    # Resolve Default Warehouse if not provided
    if not warehouse:
        if frappe.db.exists("Warehouse", f"Goods In Transit - {company}"):
            warehouse = f"Goods In Transit - {company}"
        elif frappe.db.exists("Warehouse", f"Stores - {company}"):
            warehouse = f"Stores - {company}"
        else:
            wh_list = frappe.get_all("Warehouse", filters={"company": company, "is_group": 0}, limit=1)
            warehouse = wh_list[0].name if wh_list else ""

    # Validate items and enrich stock metadata
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
            as_dict=True
        )
        if not item_meta:
            frappe.throw(_("第 {0} 行物料 [{1}] 在系统中不存在。").format(idx, item_code))

        qty = flt(row.get("qty") or 0)
        if qty <= 0:
            frappe.throw(_("第 {0} 行物料 [{1}] 数量必须大于 0。").format(idx, item_code))

        rate = flt(row.get("rate") if row.get("rate") is not None else 0)
        if rate <= 0:
            frappe.throw(_("第 {0} 行物料 [{1}] 单价不能为 0！请输入有效单价。").format(idx, item_code))

        amount = flt(row.get("amount") or (qty * rate), 2)
        if amount <= 0:
            frappe.throw(_("第 {0} 行物料 [{1}] 金额不能为 0！").format(idx, item_code))

        tax_rate = flt(row.get("tax_rate") or 13.0, 2)
        tax_amount = flt(row.get("tax_amount") or (amount * (tax_rate / 100.0)), 2)
        total_amount = flt(row.get("total_amount") or (amount + tax_amount), 2)

        is_stock = bool(item_meta.is_stock_item)
        if is_stock:
            has_stock_items = True

        row_warehouse = (row.get("warehouse") or warehouse).strip()
        if is_stock and not row_warehouse:
            frappe.throw(_("物料 [{0}] 为库存品，必须指定有效的入库仓库。").format(item_code))

        validated_items.append({
            "item_code": item_code,
            "item_name": (row.get("item_name") or item_meta.item_name or item_code).strip(),
            "uom": (row.get("uom") or item_meta.stock_uom or "Nos").strip(),
            "stock_uom": item_meta.stock_uom or "Nos",
            "is_stock_item": is_stock,
            "item_group": item_meta.item_group,
            "qty": qty,
            "rate": rate,
            "amount": amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "warehouse": row_warehouse,
            "spec": (row.get("spec") or "").strip(),
            "remarks": (row.get("remarks") or row.get("description") or "").strip(),
        })

    # 1. 自动生成并提交采购订单 (Purchase Order)
    po = frappe.new_doc("Purchase Order")
    po.company = company
    po.supplier = supplier
    po.transaction_date = bill_date_str
    po.schedule_date = bill_date_str
    if _meta_has("Purchase Order", "custom_biz_mode"):
        po.custom_biz_mode = "自办电汇"

    for it in validated_items:
        po_item = {
            "item_code": it["item_code"],
            "item_name": it["item_name"],
            "description": it["remarks"] or it["spec"] or it["item_name"],
            "item_group": it["item_group"],
            "uom": it["uom"],
            "stock_uom": it["stock_uom"],
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": it["amount"],
            "schedule_date": bill_date_str,
            "warehouse": it["warehouse"],
        }
        if _meta_has("Purchase Order Item", "custom_spec_model"):
            po_item["custom_spec_model"] = it["spec"]
        if _meta_has("Purchase Order Item", "custom_line_remark"):
            po_item["custom_line_remark"] = it["remarks"]
        if _meta_has("Purchase Order Item", "custom_tax_rate"):
            po_item["custom_tax_rate"] = it["tax_rate"]
        if _meta_has("Purchase Order Item", "custom_tax_amount"):
            po_item["custom_tax_amount"] = it["tax_amount"]
        if _meta_has("Purchase Order Item", "custom_total_amount"):
            po_item["custom_total_amount"] = it["total_amount"]
        po.append("items", po_item)

    po.flags.ignore_permissions = True
    po.insert()
    po.submit()

    # Map PO items
    po_item_map = {item.item_code: item.name for item in po.items}

    # 2. 如果包含库存品且勾选了自动入库，自动生成并提交采购入库单 (Purchase Receipt)
    created_pr_name = None
    pr_item_map = {}
    if auto_receive_stock and has_stock_items:
        pr = frappe.new_doc("Purchase Receipt")
        pr.company = company
        pr.supplier = supplier
        pr.posting_date = bill_date_str
        pr.purchase_order = po.name
        if _meta_has("Purchase Receipt", "custom_biz_mode"):
            pr.custom_biz_mode = "自办电汇"

        for it in validated_items:
            if not it["is_stock_item"]:
                continue
            pr_row = {
                "item_code": it["item_code"],
                "item_name": it["item_name"],
                "description": it["remarks"] or it["spec"] or it["item_name"],
                "item_group": it["item_group"],
                "uom": it["uom"],
                "stock_uom": it["stock_uom"],
                "qty": it["qty"],
                "rate": it["rate"],
                "amount": it["amount"],
                "warehouse": it["warehouse"],
                "purchase_order": po.name,
                "purchase_order_item": po_item_map.get(it["item_code"]),
            }
            if _meta_has("Purchase Receipt Item", "custom_spec_model"):
                pr_row["custom_spec_model"] = it["spec"]
            if _meta_has("Purchase Receipt Item", "custom_line_remark"):
                pr_row["custom_line_remark"] = it["remarks"]
            if _meta_has("Purchase Receipt Item", "custom_tax_rate"):
                pr_row["custom_tax_rate"] = it["tax_rate"]
            if _meta_has("Purchase Receipt Item", "custom_tax_amount"):
                pr_row["custom_tax_amount"] = it["tax_amount"]
            if _meta_has("Purchase Receipt Item", "custom_total_amount"):
                pr_row["custom_total_amount"] = it["total_amount"]
            pr.append("items", pr_row)

        if pr.items:
            pr.flags.ignore_permissions = True
            pr.insert()
            pr.submit()
            created_pr_name = pr.name
            pr_item_map = {item.item_code: item.name for item in pr.items}

    # 3. 自动生成并提交采购发票 (Purchase Invoice)
    pi = frappe.new_doc("Purchase Invoice")
    pi.company = company
    pi.supplier = supplier
    pi.bill_no = bill_no
    pi.bill_date = bill_date_str
    pi.posting_date = bill_date_str
    if _meta_has("Purchase Invoice", "custom_biz_mode"):
        pi.custom_biz_mode = "自办电汇"
    if _meta_has("Purchase Invoice", "custom_invoice_type"):
        pi.custom_invoice_type = invoice_type or "专用发票"

    for it in validated_items:
        pi_row = {
            "item_code": it["item_code"],
            "item_name": it["item_name"],
            "description": it["remarks"] or it["spec"] or it["item_name"],
            "item_group": it["item_group"],
            "uom": it["uom"],
            "stock_uom": it["stock_uom"],
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": it["amount"],
            "warehouse": it["warehouse"],
            "purchase_order": po.name,
            "po_detail": po_item_map.get(it["item_code"]),
            "purchase_receipt": created_pr_name if it["is_stock_item"] else "",
            "pr_detail": pr_item_map.get(it["item_code"]) if it["is_stock_item"] else "",
        }
        if _meta_has("Purchase Invoice Item", "custom_spec_model"):
            pi_row["custom_spec_model"] = it["spec"]
        if _meta_has("Purchase Invoice Item", "custom_line_remark"):
            pi_row["custom_line_remark"] = it["remarks"]
        if _meta_has("Purchase Invoice Item", "custom_tax_rate"):
            pi_row["custom_tax_rate"] = it["tax_rate"]
        if _meta_has("Purchase Invoice Item", "custom_tax_amount"):
            pi_row["custom_tax_amount"] = it["tax_amount"]
        if _meta_has("Purchase Invoice Item", "custom_total_amount"):
            pi_row["custom_total_amount"] = it["total_amount"]
        pi.append("items", pi_row)

    pi.flags.ignore_permissions = True
    pi.insert()
    pi.submit()

    # 4. 可选：自动创建报销/电汇付款申请 (Reimbursement Request)
    created_rr_name = None
    if create_reimbursement_request and frappe.db.exists("DocType", "Reimbursement Request"):
        rr = frappe.new_doc("Reimbursement Request")
        rr.company = company
        rr.applicant = applicant or frappe.session.user
        rr.posting_date = bill_date_str
        rr.supplier = supplier
        if _meta_has("Reimbursement Request", "custom_biz_mode"):
            rr.custom_biz_mode = "自办电汇"
        if _meta_has("Reimbursement Request", "custom_payment_method"):
            rr.custom_payment_method = "电汇"

        rr_row = {
            "source_pi": pi.name,
            "amount": flt(pi.grand_total or pi.total),
            "claimed_amount": flt(pi.grand_total or pi.total),
            "supplier": supplier,
            "bill_no": bill_no,
        }
        rr.append("invoice_items", rr_row)
        rr.flags.ignore_permissions = True
        rr.insert()
        rr.submit()
        created_rr_name = rr.name

    return {
        "success": True,
        "po_name": po.name,
        "pr_name": created_pr_name,
        "pi_name": pi.name,
        "rr_name": created_rr_name,
        "grand_total": flt(pi.grand_total or pi.total),
        "message": _("自办电汇单据闭环生成成功！采购订单：{0}，入库单：{1}，发票：{2}").format(
            po.name, created_pr_name or "非库存无需入库", pi.name
        ),
    }
