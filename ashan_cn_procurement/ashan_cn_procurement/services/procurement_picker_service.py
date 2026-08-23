"""Procurement order picker and downstream document generation domain services.

Provides permission-aware candidate pooling and transactional draft document
generation across the full 5-step procurement business lifecycle:
1. Item Master -> Material Request (采购需求/申请)
2. Material Request Item -> Purchase Order (采购订货)
3. Purchase Order Item -> Purchase Receipt (采购入库)
4. Purchase Receipt Item -> Purchase Invoice (采购开票)
5. Purchase Invoice / Item -> Reimbursement Request (报销付款)
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
from ashan_cn_procurement.services.authorization_service import (
    assert_company_access,
    get_allowed_companies,
)


@frappe.whitelist()
def get_user_procurement_companies() -> dict:
    """Return the list of companies the current user is authorized to access."""
    user = frappe.session.user
    allowed = get_allowed_companies(user)
    if allowed is None:
        all_companies = frappe.get_all("Company", fields=["name"], order_by="name asc")
        company_names = [c.name for c in all_companies]
    else:
        company_names = sorted(list(allowed))

    default_company = frappe.defaults.get_user_default("Company")
    if not default_company and company_names:
        default_company = company_names[0]

    return {
        "companies": company_names,
        "default_company": default_company,
        "is_all_allowed": allowed is None or len(company_names) > 1,
    }


def _resolve_companies(company: str | list[str] | None) -> list[str]:
    """Resolve active company scope list with server-side permission checks."""
    user_comps = get_user_procurement_companies()["companies"]
    if not user_comps:
        frappe.throw(_("当前账号未获得任何公司的访问权限。"))

    if not company or company == "All" or company == "全部公司":
        return user_comps

    if isinstance(company, str):
        target_comps = [c.strip() for c in company.split(",") if c.strip()]
    elif isinstance(company, list):
        target_comps = [str(c).strip() for c in company if str(c).strip()]
    else:
        target_comps = []

    if not target_comps or "All" in target_comps:
        return user_comps

    for comp in target_comps:
        assert_company_access(comp)

    return target_comps


def _meta_has(doctype: str, fieldname: str) -> bool:
    try:
        return bool(frappe.get_meta(doctype).has_field(fieldname))
    except Exception:
        return False


# =========================================================================
# Step 1: Material Request (采购申请 / 物料申请)
# =========================================================================

@frappe.whitelist()
def get_material_request_picker_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query Material Request Items for Step 1 Detail View (Read-Only Detail)."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    has_mr_dept = _meta_has("Material Request", "department")
    dept_col = "COALESCE(mr.department, '')" if has_mr_dept else "''"

    conditions = [
        "mr.material_request_type = 'Purchase'",
        "mr.docstatus < 2",
        "mr.company IN %(companies)s",
    ]
    params: dict[str, Any] = {"companies": companies}

    if filters.get("mr_name"):
        conditions.append("mr.name LIKE %(mr_name)s")
        params["mr_name"] = f"%{filters['mr_name']}%"

    if filters.get("item_code"):
        conditions.append("(mri.item_code LIKE %(item_code)s OR mri.item_name LIKE %(item_code)s)")
        params["item_code"] = f"%{filters['item_code']}%"

    if filters.get("item_group"):
        conditions.append("mri.item_group = %(item_group)s")
        params["item_group"] = filters["item_group"]

    if filters.get("department") and has_mr_dept:
        conditions.append("mr.department = %(department)s")
        params["department"] = filters["department"]

    if filters.get("supplier"):
        conditions.append("(COALESCE(item_def.default_supplier, '') = %(supplier)s OR COALESCE(item_sup.supplier, '') = %(supplier)s)")
        params["supplier"] = filters["supplier"]

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            mri.name AS mri_name,
            mr.name AS mr_name,
            mr.company,
            mr.transaction_date,
            COALESCE(mri.schedule_date, mr.schedule_date) AS schedule_date,
            {dept_col} AS department,
            mr.docstatus,
            mr.status,
            mri.item_code,
            mri.item_name,
            mri.item_group,
            COALESCE(mri.uom, mri.stock_uom, '') AS uom,
            COALESCE(mri.qty, 0) AS qty,
            COALESCE(mri.ordered_qty, 0) AS ordered_qty,
            COALESCE(mri.rate, item.standard_rate, 0) AS rate,
            COALESCE(item_def.default_supplier, item_sup.supplier, '') AS default_supplier,
            COALESCE(mri.warehouse, item_def.default_warehouse, '') AS warehouse
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        LEFT JOIN `tabItem` item ON item.name = mri.item_code
        LEFT JOIN `tabItem Default` item_def ON (item_def.parent = mri.item_code AND item_def.company = mr.company)
        LEFT JOIN `tabItem Supplier` item_sup ON item_sup.parent = mri.item_code
        WHERE {where_clause}
        ORDER BY mr.transaction_date DESC, mr.name DESC, mri.idx ASC
        LIMIT 1000
    """

    raw_rows = frappe.db.sql(sql, params, as_dict=True)

    # Stock balances
    item_codes = list({r.item_code for r in raw_rows})
    stock_map = defaultdict(float)
    if item_codes:
        bins = frappe.db.sql("""
            SELECT b.item_code, w.company, SUM(b.actual_qty) AS total_actual_qty
            FROM `tabBin` b
            INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
            WHERE b.item_code IN %s AND w.company IN %s
            GROUP BY b.item_code, w.company
        """, (item_codes, companies), as_dict=True)
        for b in bins:
            stock_map[(b.item_code, b.company)] = flt(b.total_actual_qty, 2)

    rows = []
    for r in raw_rows:
        current_stock = stock_map.get((r.item_code, r.company), 0.0)
        rows.append({
            "mri_name": r.mri_name,
            "mr_name": r.mr_name,
            "company": r.company,
            "schedule_date": str(r.schedule_date or ""),
            "department": r.department or "",
            "item_code": r.item_code,
            "item_name": r.item_name or r.item_code,
            "item_group": r.item_group or "",
            "uom": r.uom or "",
            "current_stock": current_stock,
            "qty": flt(r.qty, 2),
            "ordered_qty": flt(r.ordered_qty, 2),
            "pending_qty": max(flt(r.qty) - flt(r.ordered_qty), 0.0),
            "rate": flt(r.rate, 2),
            "supplier": r.default_supplier or "",
            "warehouse": r.warehouse or "",
            "docstatus": r.docstatus,
            "status": r.status or "Draft",
        })

    return {
        "companies": companies,
        "count": len(rows),
        "rows": rows,
    }


@frappe.whitelist()
def get_material_request_doc_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query Material Request Documents for Step 1 Header/Doc View."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    has_mr_dept = _meta_has("Material Request", "department")
    dept_col = "COALESCE(mr.department, '')" if has_mr_dept else "''"

    conditions = [
        "mr.material_request_type = 'Purchase'",
        "mr.docstatus < 2",
        "mr.company IN %(companies)s",
    ]
    params: dict[str, Any] = {"companies": companies}

    if filters.get("mr_name"):
        conditions.append("mr.name LIKE %(mr_name)s")
        params["mr_name"] = f"%{filters['mr_name']}%"

    if filters.get("department") and has_mr_dept:
        conditions.append("mr.department = %(department)s")
        params["department"] = filters["department"]

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            mr.name AS mr_name,
            mr.company,
            mr.transaction_date,
            mr.schedule_date,
            {dept_col} AS department,
            mr.docstatus,
            mr.status,
            mr.owner,
            COUNT(mri.name) AS item_count,
            COALESCE(SUM(mri.qty), 0) AS total_qty
        FROM `tabMaterial Request` mr
        LEFT JOIN `tabMaterial Request Item` mri ON mri.parent = mr.name
        WHERE {where_clause}
        GROUP BY mr.name
        ORDER BY mr.transaction_date DESC, mr.name DESC
        LIMIT 500
    """

    docs = frappe.db.sql(sql, params, as_dict=True)

    return {
        "companies": companies,
        "count": len(docs),
        "rows": docs,
    }


@frappe.whitelist(methods=["POST"])
def quick_create_material_request(
    company: str,
    items: list[dict] | str,
    department: str | None = None,
    schedule_date: str | None = None,
    purpose: str | None = None,
) -> dict:
    """Quickly create a new Material Request (Purchase) from the lightweight modal dialog."""
    if isinstance(items, str):
        items = frappe.parse_json(items) or []

    if not company:
        frappe.throw(_("请指定所属公司。"))

    assert_company_access(company)

    if not items:
        frappe.throw(_("请至少添加一行物料申请明细。"))

    default_company_wh = (
        frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
        or ""
    )

    mr = frappe.new_doc("Material Request")
    mr.material_request_type = "Purchase"
    mr.company = company
    mr.transaction_date = nowdate()
    if schedule_date:
        mr.schedule_date = schedule_date
    if default_company_wh and _meta_has("Material Request", "set_warehouse"):
        mr.set_warehouse = default_company_wh
    if department and _meta_has("Material Request", "department"):
        mr.department = department

    for it in items:
        item_code = it.get("item_code")
        if not item_code:
            continue

        item_doc = frappe.get_cached_doc("Item", item_code)
        qty = flt(it.get("qty") or 1.0, 4)
        if qty <= 0:
            qty = 1.0

        uom = it.get("uom") or item_doc.stock_uom
        item_wh = (
            it.get("warehouse")
            or frappe.db.get_value("Item Default", {"parent": item_code, "company": company}, "default_warehouse")
            or default_company_wh
        )

        mr.append("items", {
            "item_code": item_code,
            "item_name": item_doc.item_name,
            "description": it.get("description") or item_doc.description or item_doc.item_name,
            "item_group": item_doc.item_group,
            "uom": uom,
            "stock_uom": item_doc.stock_uom,
            "qty": qty,
            "schedule_date": schedule_date or str(getdate(nowdate())),
            "warehouse": item_wh,
        })

    if not mr.items:
        frappe.throw(_("未能录入有效的物料明细。"))

    mr.flags.ignore_permissions = False
    mr.insert()

    return {
        "success": True,
        "name": mr.name,
        "company": mr.company,
        "item_count": len(mr.items),
        "message": _("成功新建采购申请单：{0}").format(mr.name),
    }


@frappe.whitelist()
def get_item_master_picker_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query purchasable item master records with stock balance for popup search."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    conditions = ["item.disabled = 0"]
    params: dict[str, Any] = {"companies": companies}

    if filters.get("item_code"):
        conditions.append("(item.item_code LIKE %(item_code)s OR item.item_name LIKE %(item_code)s)")
        params["item_code"] = f"%{filters['item_code']}%"

    if filters.get("item_group"):
        conditions.append("item.item_group = %(item_group)s")
        params["item_group"] = filters["item_group"]

    if filters.get("supplier"):
        conditions.append("(COALESCE(item_def.default_supplier, '') = %(supplier)s OR COALESCE(item_sup.supplier, '') = %(supplier)s)")
        params["supplier"] = filters["supplier"]

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            item.name AS item_code,
            item.item_name,
            item.item_group,
            item.stock_uom,
            COALESCE(item.standard_rate, 0) AS standard_rate,
            COALESCE(item_def.default_supplier, item_sup.supplier, '') AS default_supplier,
            COALESCE(item_def.default_warehouse, '') AS default_warehouse,
            item_def.company AS item_company
        FROM `tabItem` item
        LEFT JOIN `tabItem Default` item_def ON (item_def.parent = item.name AND item_def.company IN %(companies)s)
        LEFT JOIN `tabItem Supplier` item_sup ON item_sup.parent = item.name
        WHERE {where_clause}
        GROUP BY item.name, item_def.company
        ORDER BY item.item_name ASC, item.name ASC
        LIMIT 1000
    """

    raw_items = frappe.db.sql(sql, params, as_dict=True)

    # Get stock balances across companies
    item_codes = list({r.item_code for r in raw_items})
    stock_map = defaultdict(float)
    if item_codes:
        bins = frappe.db.sql("""
            SELECT b.item_code, b.warehouse, w.company, SUM(b.actual_qty) AS total_actual_qty
            FROM `tabBin` b
            INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
            WHERE b.item_code IN %s AND w.company IN %s
            GROUP BY b.item_code, w.company
        """, (item_codes, companies), as_dict=True)
        for b in bins:
            stock_map[(b.item_code, b.company)] = flt(b.total_actual_qty, 2)

    rows = []
    seen = set()
    for r in raw_items:
        # Determine company for row
        comp = r.item_company or (companies[0] if len(companies) == 1 else companies[0])
        key = (r.item_code, comp)
        if key in seen:
            continue
        seen.add(key)

        current_stock = stock_map.get((r.item_code, comp), 0.0)

        rows.append({
            "item_code": r.item_code,
            "item_name": r.item_name or r.item_code,
            "item_group": r.item_group or "",
            "uom": r.stock_uom or "",
            "stock_uom": r.stock_uom or "",
            "rate": flt(r.standard_rate, 2),
            "current_stock": current_stock,
            "this_qty": 1.0,
            "supplier": r.default_supplier or "",
            "warehouse": r.default_warehouse or "",
            "company": comp,
        })

    return {
        "companies": companies,
        "count": len(rows),
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_material_requests_from_items(
    company: str | None,
    selected_items: list[dict] | str,
    schedule_date: str | None = None,
    department: str | None = None,
    purpose: str | None = None,
) -> dict:
    """Generate Draft Material Request(s) from selected Item Master rows."""
    if isinstance(selected_items, str):
        selected_items = frappe.parse_json(selected_items) or []

    if not selected_items:
        frappe.throw(_("请至少选择一种物料。"))

    # Group by company
    company_groups = defaultdict(list)
    for item in selected_items:
        item_code = item.get("item_code")
        if not item_code:
            continue
        row_company = (item.get("company") or company or "").strip()
        if not row_company or row_company == "All" or row_company == "全部公司":
            row_company = _resolve_companies(None)[0]
        assert_company_access(row_company)

        qty = flt(item.get("this_qty"), 4)
        if qty <= 0:
            qty = 1.0

        company_groups[row_company].append({
            "item_code": item_code,
            "qty": qty,
            "rate": flt(item.get("rate")),
            "warehouse": item.get("warehouse"),
            "schedule_date": item.get("schedule_date") or schedule_date or nowdate(),
            "department": item.get("department") or department,
        })

    created_requests = []
    for comp, items_list in company_groups.items():
        mr = frappe.new_doc("Material Request")
        mr.company = comp
        mr.material_request_type = "Purchase"
        mr.transaction_date = nowdate()
        mr.schedule_date = schedule_date or nowdate()

        has_mr_dept = _meta_has("Material Request", "department")
        if department and has_mr_dept:
            mr.department = department

        for item_data in items_list:
            item_doc = frappe.get_cached_value(
                "Item",
                item_data["item_code"],
                ["item_name", "description", "item_group", "stock_uom"],
                as_dict=True,
            ) or {}

            target_warehouse = item_data["warehouse"]
            if not target_warehouse:
                target_warehouse = frappe.db.get_value(
                    "Warehouse",
                    {"company": comp, "is_group": 0},
                    "name",
                )

            item_row = {
                "item_code": item_data["item_code"],
                "item_name": item_doc.get("item_name") or item_data["item_code"],
                "description": item_doc.get("description") or "",
                "item_group": item_doc.get("item_group") or "",
                "uom": item_doc.get("stock_uom") or "Nos",
                "stock_uom": item_doc.get("stock_uom") or "Nos",
                "qty": item_data["qty"],
                "rate": item_data["rate"],
                "schedule_date": item_data["schedule_date"],
                "warehouse": target_warehouse,
            }
            if item_data.get("department") and _meta_has("Material Request Item", "department"):
                item_row["department"] = item_data["department"]

            mr.append("items", item_row)

        mr.flags.ignore_permissions = False
        mr.insert()

        created_requests.append({
            "name": mr.name,
            "company": mr.company,
            "total_qty": sum(it["qty"] for it in items_list),
            "item_count": len(items_list),
        })

    return {
        "success": True,
        "created_count": len(created_requests),
        "requests": created_requests,
        "message": _("成功生成 {0} 张采购申请草稿。").format(len(created_requests)),
    }


# =========================================================================
# Step 2: Material Request (Item) -> Purchase Order (采购订货)
# =========================================================================

@frappe.whitelist()
def get_pending_material_request_items(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unfulfilled Material Request Items for Purchase Order creation."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    conditions = ["mr.docstatus = 1", "mr.material_request_type = 'Purchase'", "mr.company IN %(companies)s"]
    params: dict[str, Any] = {"companies": companies}

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
            mr.company AS company,
            COALESCE(item_def.default_supplier, item_sup.supplier, '') AS default_supplier
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        LEFT JOIN `tabItem Default` item_def ON (item_def.parent = mri.item_code AND item_def.company = mr.company)
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

        rows.append({
            "mri_name": r.mri_name,
            "mr_name": r.mr_name,
            "company": r.company,
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
        })
        total_pending_qty += pending_qty
        total_estimated_amount += est_amt

    return {
        "companies": companies,
        "count": len(rows),
        "total_pending_qty": total_pending_qty,
        "total_estimated_amount": total_estimated_amount,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_purchase_orders_from_mr_items(
    company: str | None,
    selected_items: list[dict] | str,
    supplier_override: str | None = None,
    schedule_date: str | None = None,
) -> dict:
    """Generate Draft Purchase Order(s) from selected Material Request Items."""
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

    # Fetch parent company for each item
    mr_parents = frappe.get_all(
        "Material Request",
        filters={"name": ["in", list({row.parent for row in db_items})]},
        fields=["name", "company"],
    )
    mr_company_map = {mr.name: mr.company for mr in mr_parents}

    # Group by (company, supplier)
    company_supplier_groups = defaultdict(list)

    for mri_name, db_row in db_item_map.items():
        row_company = mr_company_map.get(db_row.parent) or company
        assert_company_access(row_company)

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
                frappe.db.get_value("Item Default", {"parent": db_row.item_code, "company": row_company}, "default_supplier")
                or frappe.db.get_value("Item Supplier", {"parent": db_row.item_code}, "supplier")
                or ""
            )

        if not row_supplier:
            frappe.throw(
                _("物料【{0}】未指定供应商，请在行内选择或在顶部指定供应商。").format(
                    db_row.item_name or db_row.item_code
                )
            )

        company_supplier_groups[(row_company, row_supplier)].append({
            "db_row": db_row,
            "this_qty": this_qty,
            "rate": flt(req.get("rate")) if req.get("rate") is not None else flt(db_row.rate),
        })

    if not company_supplier_groups:
        frappe.throw(_("未能识别有效的待订购明细。"))

    created_orders = []

    for (comp, sup), items_to_order in company_supplier_groups.items():
        if not frappe.db.exists("Supplier", sup):
            frappe.throw(_("供应商【{0}】在系统中不存在。").format(sup))

        po = frappe.new_doc("Purchase Order")
        po.company = comp
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
            "company": po.company,
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
# Step 3: Purchase Order (Item) -> Purchase Receipt (采购入库)
# =========================================================================

@frappe.whitelist()
def get_pending_purchase_order_items(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unfulfilled Purchase Order Items for Purchase Receipt creation."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    conditions = ["po.docstatus = 1", "po.company IN %(companies)s"]
    params: dict[str, Any] = {"companies": companies}

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
            po.currency,
            po.company
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE {where_clause}
        ORDER BY po.company ASC, po.supplier ASC, poi.schedule_date ASC, po.transaction_date DESC, po.name DESC, poi.idx ASC
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
            "company": r.company,
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
        "companies": companies,
        "count": len(rows),
        "total_pending_qty": total_pending_qty,
        "total_pending_amount": total_pending_amount,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_purchase_receipts_from_po_items(
    company: str | None,
    selected_items: list[dict] | str,
    warehouse_override: str | None = None,
    posting_date: str | None = None,
) -> dict:
    """Generate Draft Purchase Receipt(s) from selected Purchase Order Items."""
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
        fields=["name", "company", "supplier", "currency", "buying_price_list"],
    )
    po_parent_map = {po.name: po for po in po_parents}

    # Group by (company, supplier)
    company_supplier_groups = defaultdict(list)

    for poi_name, db_row in db_item_map.items():
        po_header = po_parent_map.get(db_row.parent)
        if not po_header:
            continue

        assert_company_access(po_header.company)

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
            target_warehouse = frappe.db.get_value("Warehouse", {"company": po_header.company, "is_group": 0}, "name")

        if not target_warehouse:
            frappe.throw(_("请为物料【{0}】指定入库仓库。").format(db_row.item_name or db_row.item_code))

        company_supplier_groups[(po_header.company, po_header.supplier)].append({
            "db_row": db_row,
            "po_header": po_header,
            "this_qty": this_qty,
            "warehouse": target_warehouse,
            "rate": flt(db_row.rate),
        })

    created_receipts = []

    for (comp, sup), items_to_receive in company_supplier_groups.items():
        pr = frappe.new_doc("Purchase Receipt")
        pr.company = comp
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
            "company": pr.company,
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
# Step 4: Purchase Receipt (Item) -> Purchase Invoice (采购开票)
# =========================================================================

@frappe.whitelist()
def get_pending_purchase_receipt_items(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unfulfilled Purchase Receipt Items for Purchase Invoice creation."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    conditions = ["pr.docstatus = 1", "pr.company IN %(companies)s"]
    params: dict[str, Any] = {"companies": companies}

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
            pr.currency,
            pr.company
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE {where_clause}
        ORDER BY pr.company ASC, pr.supplier ASC, pr.posting_date DESC, pr.name DESC, pri.idx ASC
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
            "company": r.company,
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
        "companies": companies,
        "count": len(rows),
        "total_pending_qty": total_pending_qty,
        "total_pending_amount": total_pending_amount,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_purchase_invoices_from_pr_items(
    company: str | None,
    selected_items: list[dict] | str,
    bill_no: str | None = None,
    bill_date: str | None = None,
    posting_date: str | None = None,
) -> dict:
    """Generate Draft Purchase Invoice(s) from selected Purchase Receipt Items."""
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
        fields=["name", "company", "supplier", "currency", "buying_price_list"],
    )
    pr_parent_map = {pr.name: pr for pr in pr_parents}

    # Group by (company, supplier)
    company_supplier_groups = defaultdict(list)

    for pri_name, db_row in db_item_map.items():
        pr_header = pr_parent_map.get(db_row.parent)
        if not pr_header:
            continue

        assert_company_access(pr_header.company)

        req = input_item_map.get(pri_name, {})
        this_qty = flt(req.get("this_qty"), 4)
        if this_qty <= 0:
            this_qty = flt(db_row.qty)

        if this_qty <= 0:
            continue

        company_supplier_groups[(pr_header.company, pr_header.supplier)].append({
            "db_row": db_row,
            "pr_header": pr_header,
            "this_qty": this_qty,
            "rate": flt(db_row.rate),
        })

    created_invoices = []

    for (comp, sup), items_to_invoice in company_supplier_groups.items():
        pi = frappe.new_doc("Purchase Invoice")
        pi.company = comp
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
            "company": pi.company,
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
# Step 5: Purchase Invoice -> Reimbursement Request (报销付款)
# =========================================================================

@frappe.whitelist()
def get_pending_reimbursement_invoices(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query unpaid Purchase Invoices for Reimbursement Request creation."""
    companies = _resolve_companies(company)
    if isinstance(filters, str):
        filters = frappe.parse_json(filters) or {}
    filters = dict(filters or {})

    inv_filters = {
        "company": ["in", companies],
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
        "name", "company", "supplier", "bill_no", "bill_date", "posting_date",
        "grand_total", "outstanding_amount", "owner", "currency"
    ]
    if _meta_has("Purchase Invoice", "custom_invoice_type"):
        fields.append("custom_invoice_type")

    invoices = frappe.get_list(
        "Purchase Invoice",
        filters=inv_filters,
        fields=fields,
        order_by="company asc, posting_date desc, name desc",
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
            "company": inv.company,
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
        "companies": companies,
        "count": len(rows),
        "total_outstanding": total_outstanding,
        "rows": rows,
    }


@frappe.whitelist(methods=["POST"])
def make_reimbursement_from_invoices(
    company: str | None,
    selected_invoices: list[str] | str,
    applicant: str | None = None,
    purpose: str | None = None,
) -> dict:
    """Generate Draft Reimbursement Request from selected unpaid Purchase Invoices."""
    invoice_names = normalize_names(selected_invoices)
    if not invoice_names:
        frappe.throw(_("请选择至少一张采购发票。"))

    # Check companies of invoices
    invoices = frappe.get_all("Purchase Invoice", filters={"name": ["in", invoice_names]}, fields=["name", "company"])
    if not invoices:
        frappe.throw(_("未找到所选采购发票。"))

    distinct_companies = list({inv.company for inv in invoices})
    if len(distinct_companies) > 1:
        frappe.throw(_("单次报销申请仅支持同一公司的采购发票。所选发票跨越了多个公司：{0}").format(", ".join(distinct_companies)))

    target_company = distinct_companies[0]
    assert_company_access(target_company)

    rr = frappe.new_doc("Reimbursement Request")
    rr.company = target_company
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
        target_company,
        purchase_invoice_names=invoice_names,
    )

    for candidate in candidates:
        rr.append("invoice_items", candidate["row"])

    rr.flags.ignore_permissions = False
    rr.insert()

    return {
        "success": True,
        "reimbursement_name": rr.name,
        "company": target_company,
        "total_amount": flt(rr.get("total_amount") or sum(flt(c["row"]["amount"]) for c in candidates)),
        "message": _("成功生成报销申请单草稿：{0}").format(rr.name),
    }


# =========================================================================
# Overall Summary KPI Endpoint (5-Step Flow)
# =========================================================================

@frappe.whitelist()
def get_procurement_picker_overview_kpis(company: str | None = None) -> dict:
    """Return aggregated KPI counts for all 5 procurement steps."""
    companies = _resolve_companies(company)

    mr_all_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT mr.name)
        FROM `tabMaterial Request` mr
        WHERE mr.docstatus < 2
          AND mr.material_request_type = 'Purchase'
          AND mr.company IN %s
    """, (companies,))[0][0] or 0

    mr_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT mri.name)
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        WHERE mr.docstatus = 1
          AND mr.material_request_type = 'Purchase'
          AND mr.company IN %s
          AND mr.status NOT IN ('Stopped', 'Cancelled')
          AND (mri.qty - COALESCE(mri.ordered_qty, 0)) > 0.0001
    """, (companies,))[0][0] or 0

    po_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT poi.name)
        FROM `tabPurchase Order Item` poi
        INNER JOIN `tabPurchase Order` po ON po.name = poi.parent
        WHERE po.docstatus = 1
          AND po.company IN %s
          AND po.status NOT IN ('Closed', 'Cancelled', 'Delivered')
          AND (poi.qty - COALESCE(poi.received_qty, 0)) > 0.0001
    """, (companies,))[0][0] or 0

    pr_count = frappe.db.sql("""
        SELECT COUNT(DISTINCT pri.name)
        FROM `tabPurchase Receipt Item` pri
        INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
        WHERE pr.docstatus = 1
          AND pr.company IN %s
          AND pr.status NOT IN ('Closed', 'Cancelled', 'Return Issued')
          AND (pri.amount - COALESCE(pri.billed_amt, 0)) > 0.01
    """, (companies,))[0][0] or 0

    pi_stats = frappe.db.sql("""
        SELECT COUNT(name), COALESCE(SUM(outstanding_amount), 0)
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1
          AND company IN %s
          AND outstanding_amount > 0
    """, (companies,))[0]

    pi_count = pi_stats[0] or 0
    pi_amount = flt(pi_stats[1] or 0)

    return {
        "companies": companies,
        "kpis": {
            "item_to_mr": {"count": mr_all_count, "label": "采购申请单据"},
            "mr_to_po": {"count": mr_count, "label": "待订货需求明细"},
            "po_to_pr": {"count": po_count, "label": "待收货订单明细"},
            "pr_to_pi": {"count": pr_count, "label": "待开票入库明细"},
            "pi_to_rr": {"count": pi_count, "amount": pi_amount, "label": "待报销付款发票"},
        }
    }
