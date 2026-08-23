"""Procurement order picker and downstream document generation domain services.

Provides permission-aware candidate pooling and transactional draft document
generation across the four procurement flow stages:
1. Material Request Item -> Purchase Order
2. Purchase Order Item -> Purchase Receipt
3. Purchase Receipt Item -> Purchase Invoice
4. Purchase Invoice / Item -> Reimbursement Request
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from ashan_cn_procurement.reimbursement.service import (
    get_purchase_invoice_item_candidates,
    normalize_names,
)
from ashan_cn_procurement.services.authorization_service import assert_company_access


def _resolve_company(company: str | None) -> str:
    """Resolve and validate active company context with permission check."""
    company = (company or "").strip()
    if not company:
        default_company = frappe.defaults.get_user_default("Company")
        if default_company and frappe.db.exists("Company", default_company):
            company = default_company
        else:
            companies = frappe.get_list(
                "Company",
                fields=["name"],
                order_by="name asc",
                page_length=1,
            )
            company = companies[0].name if companies else ""

    if not company or not frappe.db.exists("Company", company):
        frappe.throw(_("请先选择有效公司。"))

    assert_company_access(company)
    return company


def _meta_has(doctype: str, fieldname: str) -> bool:
    try:
        return bool(frappe.get_meta(doctype).has_field(fieldname))
    except Exception:
        return False


# =========================================================================
# Stage 1: Material Request (Item) -> Purchase Order
# =========================================================================

@frappe.whitelist()
def get_pending_material_request_items(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unfulfilled Material Request Items for Purchase Order creation."""
    company = _resolve_company(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    conditions = ["mr.docstatus = 1", "mr.material_request_type = 'Purchase'", "mr.company = %(company)s"]
    params: dict[str, Any] = {"company": company}

    conditions.append("mr.status NOT IN ('Stopped', 'Cancelled', 'Transfer')")
    conditions.append("(mri.qty - COALESCE(mri.ordered_qty, 0)) > 0.0001")

    has_mr_dept = _meta_has("Material Request", "department")
    has_mri_dept = _meta_has("Material Request Item", "department")

    if filters.get("department"):
        if has_mr_dept:
            conditions.append("mr.department = %(department)s")
            params["department"] = filters["department"]
        elif has_mri_dept:
            conditions.append("mri.department = %(department)s")
            params["department"] = filters["department"]

    if filters.get("owner"):
        conditions.append("mr.owner LIKE %(owner)s")
        params["owner"] = f"%{filters['owner']}%"

    if filters.get("item_code"):
        conditions.append("(mri.item_code LIKE %(item_code)s OR mri.item_name LIKE %(item_code)s)")
        params["item_code"] = f"%{filters['item_code']}%"

    if filters.get("supplier"):
        conditions.append("(COALESCE(item_def.default_supplier, '') = %(supplier)s OR COALESCE(item_sup.supplier, '') = %(supplier)s)")
        params["supplier"] = filters["supplier"]

    if filters.get("from_date"):
        conditions.append("mr.transaction_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("mr.transaction_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    if filters.get("project"):
        has_mr_proj = _meta_has("Material Request", "project")
        has_mri_proj = _meta_has("Material Request Item", "project")
        if has_mr_proj and has_mri_proj:
            conditions.append("(mr.project = %(project)s OR mri.project = %(project)s)")
        elif has_mri_proj:
            conditions.append("mri.project = %(project)s")
        elif has_mr_proj:
            conditions.append("mr.project = %(project)s")
        params["project"] = filters["project"]

    where_clause = " AND ".join(conditions)

    dept_select = "mr.department" if has_mr_dept else ("mri.department" if has_mri_dept else "''")

    sql = f"""
        SELECT
            mri.name AS mri_name,
            mri.parent AS mr_name,
            mri.idx AS idx,
            mri.item_code,
            mri.item_name,
            mri.description,
            mri.item_group,
            mri.uom,
            mri.stock_uom,
            mri.qty,
            COALESCE(mri.ordered_qty, 0) AS ordered_qty,
            (mri.qty - COALESCE(mri.ordered_qty, 0)) AS pending_qty,
            COALESCE(mri.rate, 0) AS rate,
            COALESCE(mri.amount, 0) AS amount,
            mri.schedule_date,
            mri.warehouse,
            {dept_select} AS department,
            mr.transaction_date AS mr_date,
            mr.owner AS requested_by,
            COALESCE(item_def.default_supplier, item_sup.supplier, '') AS default_supplier
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        LEFT JOIN `tabItem Default` item_def ON (item_def.parent = mri.item_code AND item_def.company = %(company)s)
        LEFT JOIN `tabItem Supplier` item_sup ON item_sup.parent = mri.item_code
        WHERE {where_clause}
        GROUP BY mri.name
        ORDER BY mri.schedule_date ASC, mr.transaction_date DESC, mr.name DESC, mri.idx ASC
        LIMIT 2000
    """

    raw_rows = frappe.db.sql(sql, params, as_dict=True)
    rows = []
    total_pending_qty = 0.0
    total_estimated_amount = 0.0

    today = getdate(nowdate())
    for r in raw_rows:
        pending_qty = flt(r.pending_qty, 4)
        rate = flt(r.rate, 2)
        est_amt = round(pending_qty * rate, 2)
        sch_date = getdate(r.schedule_date) if r.schedule_date else None
        is_overdue = bool(sch_date and sch_date < today)
        is_urgent = bool(sch_date and not is_overdue and (sch_date - today).days <= 3)

        row_dict = {
            "mri_name": r.mri_name,
            "mr_name": r.mr_name,
            "idx": r.idx,
            "item_code": r.item_code,
            "item_name": r.item_name or r.item_code,
            "description": r.description or "",
            "item_group": r.item_group or "",
            "uom": r.uom or r.stock_uom or "",
            "stock_uom": r.stock_uom or "",
            "qty": flt(r.qty, 4),
            "ordered_qty": flt(r.ordered_qty, 4),
            "pending_qty": pending_qty,
            "this_qty": pending_qty,
            "rate": rate,
            "estimated_amount": est_amt,
            "schedule_date": str(r.schedule_date) if r.schedule_date else "",
            "warehouse": r.warehouse or "",
            "project": r.get("project") or "",
            "mr_date": str(r.mr_date) if r.mr_date else "",
            "department": r.department or "",
            "requested_by": r.requested_by or "",
            "supplier": r.default_supplier or "",
            "is_overdue": is_overdue,
            "is_urgent": is_urgent,
        }
        rows.append(row_dict)
        total_pending_qty += pending_qty
        total_estimated_amount += est_amt

    return {
        "company": company,
        "count": len(rows),
        "total_pending_qty": total_pending_qty,
        "total_estimated_amount": total_estimated_amount,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_purchase_orders_from_mr_items(
    company: str,
    selected_items: list[dict] | str,
    supplier_override: str | None = None,
    schedule_date: str | None = None,
) -> dict:
    """Generate Draft Purchase Order(s) from selected Material Request Items."""
    company = _resolve_company(company)
    if isinstance(selected_items, str):
        selected_items = frappe.parse_json(selected_items) or []

    if not selected_items:
        frappe.throw(_("请至少选择一行采购需求明细。"))

    mri_names = [item["mri_name"] for item in selected_items if item.get("mri_name")]
    if not mri_names:
        frappe.throw(_("无效的明细行选择。"))

    db_items = frappe.get_all(
        "Material Request Item",
        filters={"name": ["in", mri_names]},
        fields=[
            "name", "parent", "item_code", "item_name", "description",
            "item_group", "uom", "stock_uom", "qty", "ordered_qty",
            "rate", "schedule_date", "warehouse", "conversion_factor"
        ],
    )
    db_item_map = {row.name: row for row in db_items}
    input_item_map = {item["mri_name"]: item for item in selected_items}

    supplier_groups = defaultdict(list)

    for mri_name, db_row in db_item_map.items():
        req = input_item_map.get(mri_name, {})
        this_qty = flt(req.get("this_qty"), 4)
        if this_qty <= 0:
            this_qty = flt(db_row.qty) - flt(db_row.ordered_qty)

        if this_qty <= 0:
            continue

        max_available = flt(db_row.qty) - flt(db_row.ordered_qty)
        if this_qty > (max_available + 0.0001):
            frappe.throw(
                _("物料【{0}】本次订购数量 ({1}) 超过可用待订数量 ({2})。").format(
                    db_row.item_name or db_row.item_code, this_qty, max_available
                )
            )

        row_supplier = (supplier_override or req.get("supplier") or "").strip()
        if not row_supplier:
            row_supplier = (
                frappe.db.get_value("Item Default", {"parent": db_row.item_code, "company": company}, "default_supplier")
                or frappe.db.get_value("Item Supplier", {"parent": db_row.item_code}, "supplier")
                or ""
            )

        if not row_supplier:
            frappe.throw(
                _("物料【{0}】未指定供应商，请在行内选择或在顶部指定供应商。").format(
                    db_row.item_name or db_row.item_code
                )
            )

        supplier_groups[row_supplier].append({
            "db_row": db_row,
            "this_qty": this_qty,
            "rate": flt(req.get("rate")) if req.get("rate") is not None else flt(db_row.rate),
        })

    if not supplier_groups:
        frappe.throw(_("未能识别有效的待订购明细。"))

    created_orders = []

    for sup, items_to_order in supplier_groups.items():
        if not frappe.db.exists("Supplier", sup):
            frappe.throw(_("供应商【{0}】在系统中不存在。").format(sup))

        po = frappe.new_doc("Purchase Order")
        po.company = company
        po.supplier = sup
        po.transaction_date = nowdate()
        if schedule_date:
            po.schedule_date = schedule_date

        for item_data in items_to_order:
            db_row = item_data["db_row"]
            this_qty = item_data["this_qty"]
            rate = item_data["rate"]

            po_item = {
                "item_code": db_row.item_code,
                "item_name": db_row.item_name,
                "description": db_row.description,
                "item_group": db_row.item_group,
                "uom": db_row.uom or db_row.stock_uom,
                "stock_uom": db_row.stock_uom,
                "qty": this_qty,
                "rate": rate,
                "schedule_date": schedule_date or str(db_row.schedule_date or nowdate()),
                "warehouse": db_row.warehouse,
                "material_request": db_row.parent,
                "material_request_item": db_row.name,
            }
            po.append("items", po_item)

        po.flags.ignore_permissions = False
        po.insert()

        created_orders.append({
            "name": po.name,
            "supplier": po.supplier,
            "total_qty": sum(item_data["this_qty"] for item_data in items_to_order),
            "grand_total": flt(po.grand_total or po.total),
            "item_count": len(items_to_order),
        })

    return {
        "success": True,
        "created_count": len(created_orders),
        "orders": created_orders,
        "message": _("成功生成 {0} 张采购订单草稿。").format(len(created_orders)),
    }


# =========================================================================
# Stage 2: Purchase Order (Item) -> Purchase Receipt
# =========================================================================

@frappe.whitelist()
def get_pending_purchase_order_items(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unfulfilled Purchase Order Items for Purchase Receipt creation."""
    company = _resolve_company(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    conditions = ["po.docstatus = 1", "po.company = %(company)s"]
    params: dict[str, Any] = {"company": company}

    conditions.append("po.status NOT IN ('Closed', 'Cancelled', 'Delivered')")
    conditions.append("(poi.qty - COALESCE(poi.received_qty, 0)) > 0.0001")

    if filters.get("supplier"):
        conditions.append("po.supplier = %(supplier)s")
        params["supplier"] = filters["supplier"]

    if filters.get("po_name"):
        conditions.append("po.name LIKE %(po_name)s")
        params["po_name"] = f"%{filters['po_name']}%"

    if filters.get("item_code"):
        conditions.append("(poi.item_code LIKE %(item_code)s OR poi.item_name LIKE %(item_code)s)")
        params["item_code"] = f"%{filters['item_code']}%"

    if filters.get("warehouse"):
        conditions.append("poi.warehouse = %(warehouse)s")
        params["warehouse"] = filters["warehouse"]

    if filters.get("from_date"):
        conditions.append("po.transaction_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("po.transaction_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            poi.name AS poi_name,
            poi.parent AS po_name,
            poi.idx AS idx,
            poi.item_code,
            poi.item_name,
            poi.description,
            poi.uom,
            poi.stock_uom,
            poi.qty,
            COALESCE(poi.received_qty, 0) AS received_qty,
            (poi.qty - COALESCE(poi.received_qty, 0)) AS pending_qty,
            COALESCE(poi.rate, 0) AS rate,
            COALESCE(poi.amount, 0) AS amount,
            poi.schedule_date,
            poi.warehouse,
            po.supplier,
            po.transaction_date AS po_date,
            po.currency
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE {where_clause}
        ORDER BY po.supplier ASC, poi.schedule_date ASC, po.transaction_date DESC, po.name DESC, poi.idx ASC
        LIMIT 2000
    """

    raw_rows = frappe.db.sql(sql, params, as_dict=True)
    rows = []
    total_pending_qty = 0.0
    total_pending_amount = 0.0

    today = getdate(nowdate())
    for r in raw_rows:
        pending_qty = flt(r.pending_qty, 4)
        rate = flt(r.rate, 2)
        pending_amt = round(pending_qty * rate, 2)
        sch_date = getdate(r.schedule_date) if r.schedule_date else None
        is_overdue = bool(sch_date and sch_date < today)

        rows.append({
            "poi_name": r.poi_name,
            "po_name": r.po_name,
            "idx": r.idx,
            "supplier": r.supplier or "",
            "item_code": r.item_code,
            "item_name": r.item_name or r.item_code,
            "description": r.description or "",
            "uom": r.uom or r.stock_uom or "",
            "stock_uom": r.stock_uom or "",
            "qty": flt(r.qty, 4),
            "received_qty": flt(r.received_qty, 4),
            "pending_qty": pending_qty,
            "this_qty": pending_qty,
            "rate": rate,
            "pending_amount": pending_amt,
            "schedule_date": str(r.schedule_date) if r.schedule_date else "",
            "warehouse": r.warehouse or "",
            "project": r.get("project") or "",
            "po_date": str(r.po_date) if r.po_date else "",
            "currency": r.currency or "CNY",
            "is_overdue": is_overdue,
        })
        total_pending_qty += pending_qty
        total_pending_amount += pending_amt

    return {
        "company": company,
        "count": len(rows),
        "total_pending_qty": total_pending_qty,
        "total_pending_amount": total_pending_amount,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_purchase_receipts_from_po_items(
    company: str,
    selected_items: list[dict] | str,
    warehouse_override: str | None = None,
    posting_date: str | None = None,
) -> dict:
    """Generate Draft Purchase Receipt(s) from selected Purchase Order Items."""
    company = _resolve_company(company)
    if isinstance(selected_items, str):
        selected_items = frappe.parse_json(selected_items) or []

    if not selected_items:
        frappe.throw(_("请至少选择一行采购订单明细。"))

    poi_names = [item["poi_name"] for item in selected_items if item.get("poi_name")]
    if not poi_names:
        frappe.throw(_("无效的明细行选择。"))

    db_items = frappe.get_all(
        "Purchase Order Item",
        filters={"name": ["in", poi_names]},
        fields=[
            "name", "parent", "item_code", "item_name", "description",
            "item_group", "uom", "stock_uom", "qty", "received_qty",
            "rate", "warehouse", "conversion_factor"
        ],
    )
    db_item_map = {row.name: row for row in db_items}
    input_item_map = {item["poi_name"]: item for item in selected_items}

    po_parents = frappe.get_all(
        "Purchase Order",
        filters={"name": ["in", list({row.parent for row in db_items})]},
        fields=["name", "supplier", "currency", "buying_price_list"],
    )
    po_parent_map = {po.name: po for po in po_parents}

    supplier_groups = defaultdict(list)

    for poi_name, db_row in db_item_map.items():
        po_header = po_parent_map.get(db_row.parent)
        if not po_header:
            continue

        req = input_item_map.get(poi_name, {})
        this_qty = flt(req.get("this_qty"), 4)
        if this_qty <= 0:
            this_qty = flt(db_row.qty) - flt(db_row.received_qty)

        if this_qty <= 0:
            continue

        max_available = flt(db_row.qty) - flt(db_row.received_qty)
        if this_qty > (max_available + 0.0001):
            frappe.throw(
                _("物料【{0}】本次入库数量 ({1}) 超过未收数量 ({2})。").format(
                    db_row.item_name or db_row.item_code, this_qty, max_available
                )
            )

        target_warehouse = (warehouse_override or req.get("warehouse") or db_row.warehouse or "").strip()
        if not target_warehouse:
            frappe.throw(_("请为物料【{0}】指定入库仓库。").format(db_row.item_name or db_row.item_code))

        supplier_groups[po_header.supplier].append({
            "db_row": db_row,
            "po_header": po_header,
            "this_qty": this_qty,
            "warehouse": target_warehouse,
            "rate": flt(db_row.rate),
        })

    created_receipts = []

    for sup, items_to_receive in supplier_groups.items():
        pr = frappe.new_doc("Purchase Receipt")
        pr.company = company
        pr.supplier = sup
        pr.posting_date = posting_date or nowdate()

        for item_data in items_to_receive:
            db_row = item_data["db_row"]
            this_qty = item_data["this_qty"]
            wh = item_data["warehouse"]

            pr.append("items", {
                "item_code": db_row.item_code,
                "item_name": db_row.item_name,
                "description": db_row.description,
                "uom": db_row.uom or db_row.stock_uom,
                "stock_uom": db_row.stock_uom,
                "qty": this_qty,
                "received_qty": this_qty,
                "rate": db_row.rate,
                "warehouse": wh,
                "purchase_order": db_row.parent,
                "purchase_order_item": db_row.name,
            })

        pr.flags.ignore_permissions = False
        pr.insert()

        created_receipts.append({
            "name": pr.name,
            "supplier": pr.supplier,
            "total_qty": sum(item_data["this_qty"] for item_data in items_to_receive),
            "grand_total": flt(pr.grand_total or pr.total),
            "item_count": len(items_to_receive),
        })

    return {
        "success": True,
        "created_count": len(created_receipts),
        "receipts": created_receipts,
        "message": _("成功生成 {0} 张采购入库单草稿。").format(len(created_receipts)),
    }


# =========================================================================
# Stage 3: Purchase Receipt (Item) -> Purchase Invoice
# =========================================================================

@frappe.whitelist()
def get_pending_purchase_receipt_items(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unfulfilled Purchase Receipt Items for Purchase Invoice creation."""
    company = _resolve_company(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    conditions = ["pr.docstatus = 1", "pr.company = %(company)s"]
    params: dict[str, Any] = {"company": company}

    conditions.append("pr.status NOT IN ('Closed', 'Cancelled', 'Return Issued')")
    conditions.append("(pri.amount - COALESCE(pri.billed_amt, 0)) > 0.01")

    if filters.get("supplier"):
        conditions.append("pr.supplier = %(supplier)s")
        params["supplier"] = filters["supplier"]

    if filters.get("pr_name"):
        conditions.append("pr.name LIKE %(pr_name)s")
        params["pr_name"] = f"%{filters['pr_name']}%"

    if filters.get("item_code"):
        conditions.append("(pri.item_code LIKE %(item_code)s OR pri.item_name LIKE %(item_code)s)")
        params["item_code"] = f"%{filters['item_code']}%"

    if filters.get("from_date"):
        conditions.append("pr.posting_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("pr.posting_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            pri.name AS pri_name,
            pri.parent AS pr_name,
            pri.idx AS idx,
            pri.item_code,
            pri.item_name,
            pri.description,
            pri.uom,
            pri.stock_uom,
            pri.qty,
            COALESCE(pri.billed_amt, 0) AS billed_amt,
            COALESCE(pri.rate, 0) AS rate,
            COALESCE(pri.amount, 0) AS amount,
            (pri.amount - COALESCE(pri.billed_amt, 0)) AS pending_amt,
            pri.purchase_order,
            pri.purchase_order_item,
            pri.warehouse,
            pr.supplier,
            pr.posting_date AS pr_date,
            pr.currency
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE {where_clause}
        ORDER BY pr.supplier ASC, pr.posting_date DESC, pr.name DESC, pri.idx ASC
        LIMIT 2000
    """

    raw_rows = frappe.db.sql(sql, params, as_dict=True)
    rows = []
    total_pending_qty = 0.0
    total_pending_amount = 0.0

    for r in raw_rows:
        pending_amt = flt(r.pending_amt, 2)
        rate = flt(r.rate, 2)
        qty = flt(r.qty, 4)
        amt = flt(r.amount, 2)

        # Calculate pending quantity proportionally
        if amt > 0.0001:
            pending_qty = round(qty * (pending_amt / amt), 4)
            billed_qty = round(qty - pending_qty, 4)
        elif rate > 0.0001:
            pending_qty = round(pending_amt / rate, 4)
            billed_qty = round(qty - pending_qty, 4)
        else:
            pending_qty = qty
            billed_qty = 0.0

        rows.append({
            "pri_name": r.pri_name,
            "pr_name": r.pr_name,
            "idx": r.idx,
            "supplier": r.supplier or "",
            "item_code": r.item_code,
            "item_name": r.item_name or r.item_code,
            "description": r.description or "",
            "uom": r.uom or r.stock_uom or "",
            "stock_uom": r.stock_uom or "",
            "qty": qty,
            "billed_qty": billed_qty,
            "pending_qty": pending_qty,
            "this_qty": pending_qty,
            "rate": rate,
            "pending_amount": pending_amt,
            "purchase_order": r.purchase_order or "",
            "purchase_order_item": r.purchase_order_item or "",
            "warehouse": r.warehouse or "",
            "project": r.get("project") or "",
            "pr_date": str(r.pr_date) if r.pr_date else "",
            "currency": r.currency or "CNY",
        })
        total_pending_qty += pending_qty
        total_pending_amount += pending_amt

    return {
        "company": company,
        "count": len(rows),
        "total_pending_qty": total_pending_qty,
        "total_pending_amount": total_pending_amount,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_purchase_invoices_from_pr_items(
    company: str,
    selected_items: list[dict] | str,
    bill_no: str | None = None,
    bill_date: str | None = None,
    posting_date: str | None = None,
) -> dict:
    """Generate Draft Purchase Invoice(s) from selected Purchase Receipt Items."""
    company = _resolve_company(company)
    if isinstance(selected_items, str):
        selected_items = frappe.parse_json(selected_items) or []

    if not selected_items:
        frappe.throw(_("请至少选择一行采购入库明细。"))

    pri_names = [item["pri_name"] for item in selected_items if item.get("pri_name")]
    if not pri_names:
        frappe.throw(_("无效的明细行选择。"))

    db_items = frappe.get_all(
        "Purchase Receipt Item",
        filters={"name": ["in", pri_names]},
        fields=[
            "name", "parent", "item_code", "item_name", "description",
            "item_group", "uom", "stock_uom", "qty", "billed_amt",
            "rate", "amount", "warehouse", "purchase_order",
            "purchase_order_item", "conversion_factor"
        ],
    )
    db_item_map = {row.name: row for row in db_items}
    input_item_map = {item["pri_name"]: item for item in selected_items}

    pr_parents = frappe.get_all(
        "Purchase Receipt",
        filters={"name": ["in", list({row.parent for row in db_items})]},
        fields=["name", "supplier", "currency", "buying_price_list"],
    )
    pr_parent_map = {pr.name: pr for pr in pr_parents}

    supplier_groups = defaultdict(list)

    for pri_name, db_row in db_item_map.items():
        pr_header = pr_parent_map.get(db_row.parent)
        if not pr_header:
            continue

        req = input_item_map.get(pri_name, {})
        this_qty = flt(req.get("this_qty"), 4)
        if this_qty <= 0:
            this_qty = flt(db_row.qty)

        if this_qty <= 0:
            continue

        supplier_groups[pr_header.supplier].append({
            "db_row": db_row,
            "pr_header": pr_header,
            "this_qty": this_qty,
            "rate": flt(db_row.rate),
        })

    created_invoices = []

    for sup, items_to_invoice in supplier_groups.items():
        pi = frappe.new_doc("Purchase Invoice")
        pi.company = company
        pi.supplier = sup
        pi.posting_date = posting_date or nowdate()
        if bill_no:
            pi.bill_no = bill_no
        if bill_date:
            pi.bill_date = bill_date

        for item_data in items_to_invoice:
            db_row = item_data["db_row"]
            this_qty = item_data["this_qty"]

            pi.append("items", {
                "item_code": db_row.item_code,
                "item_name": db_row.item_name,
                "description": db_row.description,
                "uom": db_row.uom or db_row.stock_uom,
                "stock_uom": db_row.stock_uom,
                "qty": this_qty,
                "rate": db_row.rate,
                "warehouse": db_row.warehouse,
                "purchase_receipt": db_row.parent,
                "pr_detail": db_row.name,
                "purchase_order": db_row.purchase_order,
                "po_detail": db_row.purchase_order_item,
            })

        pi.flags.ignore_permissions = False
        pi.insert()

        created_invoices.append({
            "name": pi.name,
            "supplier": pi.supplier,
            "total_qty": sum(item_data["this_qty"] for item_data in items_to_invoice),
            "grand_total": flt(pi.grand_total or pi.total),
            "item_count": len(items_to_invoice),
        })

    return {
        "success": True,
        "created_count": len(created_invoices),
        "invoices": created_invoices,
        "message": _("成功生成 {0} 张采购发票草稿。").format(len(created_invoices)),
    }


# =========================================================================
# Stage 4: Purchase Invoice -> Reimbursement Request
# =========================================================================

@frappe.whitelist()
def get_pending_reimbursement_invoices(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unpaid Purchase Invoices for Reimbursement Request creation."""
    company = _resolve_company(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    inv_filters = {
        "company": company,
        "docstatus": 1,
        "outstanding_amount": [">", 0],
    }

    if filters.get("supplier"):
        inv_filters["supplier"] = filters["supplier"]

    if filters.get("bill_no"):
        inv_filters["bill_no"] = ["like", f"%{filters['bill_no']}%"]

    if filters.get("owner"):
        inv_filters["owner"] = ["like", f"%{filters['owner']}%"]

    fields = [
        "name", "supplier", "bill_no", "bill_date", "posting_date",
        "grand_total", "outstanding_amount", "owner", "currency"
    ]
    if _meta_has("Purchase Invoice", "custom_invoice_type"):
        fields.append("custom_invoice_type")

    invoices = frappe.get_list(
        "Purchase Invoice",
        filters=inv_filters,
        fields=fields,
        order_by="posting_date desc, name desc",
        page_length=1000,
    )

    active_res = []
    if frappe.db.exists("DocType", "Reimbursement Source Reservation"):
        active_res = frappe.get_all(
            "Reimbursement Source Reservation",
            filters={"status": ["in", ["Draft", "Submitted"]]},
            fields=["source_purchase_invoice", "source_purchase_invoice_item", "reserved_amount"],
        )
    reserved_by_pi = defaultdict(float)
    for res in active_res:
        reserved_by_pi[res.source_purchase_invoice] += flt(res.reserved_amount)

    rows = []
    total_outstanding = 0.0

    for inv in invoices:
        reserved = reserved_by_pi.get(inv.name, 0.0)
        net_outstanding = max(0.0, flt(inv.outstanding_amount) - reserved)
        if net_outstanding <= 0.0001:
            continue

        rows.append({
            "pi_name": inv.name,
            "supplier": inv.supplier,
            "bill_no": inv.bill_no or "",
            "bill_date": str(inv.bill_date) if inv.bill_date else "",
            "posting_date": str(inv.posting_date) if inv.posting_date else "",
            "grand_total": flt(inv.grand_total, 2),
            "outstanding_amount": flt(inv.outstanding_amount, 2),
            "net_available_amount": flt(net_outstanding, 2),
            "this_amount": flt(net_outstanding, 2),
            "owner": inv.owner or "",
            "invoice_type": inv.get("custom_invoice_type") or "普通发票",
            "currency": inv.currency or "CNY",
        })
        total_outstanding += net_outstanding

    return {
        "company": company,
        "count": len(rows),
        "total_outstanding": total_outstanding,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_reimbursement_from_invoices(
    company: str,
    selected_invoices: list[str] | str,
    applicant: str | None = None,
    purpose: str | None = None,
) -> dict:
    """Generate Draft Reimbursement Request from selected unpaid Purchase Invoices."""
    company = _resolve_company(company)
    invoice_names = normalize_names(selected_invoices)
    if not invoice_names:
        frappe.throw(_("请选择至少一张采购发票。"))

    rr = frappe.new_doc("Reimbursement Request")
    rr.company = company
    rr.posting_date = nowdate()
    rr.title = (purpose or "").strip() or f"采购发票报销_{nowdate()}"
    if applicant:
        if _meta_has("Reimbursement Request", "applicant"):
            rr.applicant = applicant
        elif _meta_has("Reimbursement Request", "employee"):
            rr.employee = applicant
    else:
        current_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        if _meta_has("Reimbursement Request", "applicant"):
            rr.applicant = current_emp or frappe.session.user
        elif _meta_has("Reimbursement Request", "employee"):
            rr.employee = current_emp
    if purpose and _meta_has("Reimbursement Request", "purpose"):
        rr.purpose = purpose

    candidates = get_purchase_invoice_item_candidates(
        company,
        purchase_invoice_names=invoice_names,
    )

    for candidate in candidates:
        rr.append("invoice_items", candidate["row"])

    rr.flags.ignore_permissions = False
    rr.insert()

    return {
        "success": True,
        "reimbursement_name": rr.name,
        "total_amount": flt(rr.get("total_amount") or sum(flt(c["row"]["amount"]) for c in candidates)),
        "message": _("成功生成报销申请单草稿：{0}").format(rr.name),
    }


# =========================================================================
# Overall Summary KPI Endpoint
# =========================================================================

@frappe.whitelist()
def get_procurement_picker_overview_kpis(company: str | None = None) -> dict:
    """Return aggregated KPI counts for all 4 procurement stages."""
    company = _resolve_company(company)

    mr_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT mri.name)
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        WHERE mr.docstatus = 1
          AND mr.material_request_type = 'Purchase'
          AND mr.company = %s
          AND mr.status NOT IN ('Stopped', 'Cancelled')
          AND (mri.qty - COALESCE(mri.ordered_qty, 0)) > 0.0001
    """, (company,))[0][0] or 0

    po_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT poi.name)
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE po.docstatus = 1
          AND po.company = %s
          AND po.status NOT IN ('Closed', 'Cancelled', 'Delivered')
          AND (poi.qty - COALESCE(poi.received_qty, 0)) > 0.0001
    """, (company,))[0][0] or 0

    pr_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT pri.name)
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE pr.docstatus = 1
          AND pr.company = %s
          AND pr.status NOT IN ('Closed', 'Cancelled', 'Return Issued')
          AND (pri.amount - COALESCE(pri.billed_amt, 0)) > 0.01
    """, (company,))[0][0] or 0

    pi_stats = frappe.db.sql("""
        SELECT COUNT(name), COALESCE(SUM(outstanding_amount), 0)
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1
          AND company = %s
          AND outstanding_amount > 0
    """, (company,))[0]

    pi_count = pi_stats[0] or 0
    pi_amount = flt(pi_stats[1] or 0)

    return {
        "company": company,
        "kpis": {
            "mr_to_po": {"count": mr_count, "label": "待订货需求明细"},
            "po_to_pr": {"count": po_count, "label": "待收货订单明细"},
            "pr_to_pi": {"count": pr_count, "label": "待开票入库明细"},
            "pi_to_rr": {"count": pi_count, "amount": pi_amount, "label": "待报销/付款发票"},
        }
    }
