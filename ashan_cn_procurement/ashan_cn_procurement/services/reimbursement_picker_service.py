# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, nowdate, getdate

from ashan_cn_procurement.services.authorization_service import assert_company_access
from ashan_cn_procurement.services.procurement_picker_service import (
    get_user_procurement_companies,
)


def _resolve_companies(company: str | None = None) -> list[str]:
    """Resolve accessible companies list with server-side permission checks."""
    user_comps = get_user_procurement_companies()["companies"]
    if not user_comps:
        frappe.throw(_("当前账号未获得任何公司的访问权限。"))

    if not company or company in ("All", "全部公司"):
        return user_comps

    assert_company_access(company)
    return [company]


def _meta_has(doctype: str, fieldname: str) -> bool:
    """Safely check if DocType has a field."""
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def _normalize_dict(values: Any) -> dict:
    if isinstance(values, str):
        values = frappe.parse_json(values)
    return values if isinstance(values, dict) else {}


# =========================================================================
# 1. KPI Aggregation for 报销申请中心
# =========================================================================

@frappe.whitelist()
def get_reimbursement_picker_overview_kpis(company: str | None = None) -> dict:
    """Return aggregated KPI counts for 报销申请中心."""
    companies = _resolve_companies(company)

    # 1. 待结款报销单数与总额
    rr_stats = frappe.db.sql("""
        SELECT
            COUNT(name) AS total_count,
            COALESCE(SUM(total_amount), 0) AS grand_total,
            COALESCE(SUM(outstanding_amount), 0) AS outstanding_total,
            SUM(CASE WHEN outstanding_amount > 0.0001 THEN 1 ELSE 0 END) AS pending_count
        FROM `tabReimbursement Request`
        WHERE docstatus = 1
          AND company IN %s
          AND (custom_biz_mode = '现金报销' OR custom_biz_mode = '报销申请')
    """, (companies,), as_dict=True)[0]

    pending_rr_count = rr_stats.pending_count or 0
    rr_total_count = rr_stats.total_count or 0
    rr_grand_total = flt(rr_stats.grand_total or 0)
    rr_outstanding = flt(rr_stats.outstanding_total or 0)

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
# 2. Document & Detail Queries for 报销申请
# =========================================================================

def _format_compact_preview(items: list[str], max_show: int = 2) -> str:
    """Format compact string with overflow count: 'item1、item2 +3'."""
    clean_items = [str(x).strip() for x in items if str(x).strip()]
    clean_items = list(dict.fromkeys(clean_items))
    if not clean_items:
        return "-"
    if len(clean_items) <= max_show:
        return "、".join(clean_items)
    return f"{'、'.join(clean_items[:max_show])} +{len(clean_items) - max_show}"


@frappe.whitelist()
def get_reimbursement_picker_doc_summary_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query document level summary rows for 报销申请 with compact preview."""
    companies = _resolve_companies(company)
    filters = _normalize_dict(filters)

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
            COALESCE(rr.title, '') AS title,
            COALESCE(rr.custom_doc_details, '') AS doc_details,
            (
                SELECT COUNT(rii.name)
                FROM `tabReimbursement Invoice Item` rii
                WHERE rii.parent = rr.name
            ) AS item_count,
            (
                SELECT GROUP_CONCAT(DISTINCT rii.supplier ORDER BY rii.supplier DESC SEPARATOR '||')
                FROM `tabReimbursement Invoice Item` rii
                WHERE rii.parent = rr.name AND rii.supplier IS NOT NULL AND rii.supplier != ''
            ) AS raw_suppliers,
            (
                SELECT GROUP_CONCAT(DISTINCT rii.invoice_no ORDER BY rii.invoice_no DESC SEPARATOR '||')
                FROM `tabReimbursement Invoice Item` rii
                WHERE rii.parent = rr.name AND rii.invoice_no IS NOT NULL AND rii.invoice_no != ''
            ) AS raw_invoice_nos,
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

        suppliers_list = [s for s in (d.raw_suppliers or "").split("||") if s.strip()]
        invoices_list = [i for i in (d.raw_invoice_nos or "").split("||") if i.strip()]

        supp_count = len(suppliers_list)
        inv_count = len(invoices_list)

        masked_invoices = [f"…{x[-8:]}" if len(x) > 8 else x for x in invoices_list]

        rows.append({
            "idx": idx,
            "rr_name": d.rr_name,
            "company": d.company,
            "employee": d.employee,
            "employee_name": d.employee_name,
            "title": d.title or "-",
            "supplier_count": supp_count,
            "invoice_count": inv_count,
            "supplier_preview": _format_compact_preview(suppliers_list, 2),
            "invoice_preview": _format_compact_preview(masked_invoices, 2),
            "suppliers": "、".join(suppliers_list) if suppliers_list else "-",
            "invoice_nos": "、".join(invoices_list) if invoices_list else "-",
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


@frappe.whitelist()
def get_reimbursement_picker_rows(
    company: str | None = None,
    filters: dict | str | None = None,
) -> dict:
    """Query item detail rows for 报销申请."""
    companies = _resolve_companies(company)
    filters = _normalize_dict(filters)

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
    has_src_tax = _meta_has("Reimbursement Invoice Item", "source_tax_invoice")
    src_tax_col = "COALESCE(rii.source_tax_invoice, '')" if has_src_tax else "''"

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
            COALESCE(rii.source_pi, '') AS source_pi,
            {src_tax_col} AS source_tax_invoice
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
            "source_tax_invoice": it.source_tax_invoice or "-",
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


# =========================================================================
# 3. Reimbursement Creation Defaults API
# =========================================================================

@frappe.whitelist()
def get_reimbursement_creation_defaults(company: str | None = None) -> dict:
    """Return default company, employee, posting date for reimbursement dialog."""
    companies = _resolve_companies(company)

    selected_company = None
    if company and company not in ("All", "全部公司") and company in companies:
        selected_company = company
    elif len(companies) == 1:
        selected_company = companies[0]
    elif companies:
        selected_company = companies[0]

    employee = None
    employee_name = None

    if selected_company:
        emp = frappe.get_all(
            "Employee",
            filters={
                "user_id": frappe.session.user,
                "company": selected_company,
                "status": "Active",
            },
            fields=["name", "employee_name"],
            limit=1,
        )
        if emp:
            employee = emp[0].name
            employee_name = emp[0].employee_name

    return {
        "companies": companies,
        "company": selected_company,
        "employee": employee,
        "employee_name": employee_name,
        "posting_date": nowdate(),
        "auto_receive_stock": 1,
    }


# =========================================================================
# 4. Multi-Invoice Manual Entry Engine (Atomic POST)
# =========================================================================

VALID_INVOICE_TYPES = ("专用发票", "普通发票", "无发票")


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


def _ensure_uom(uom_name: str) -> str:
    """Ensure UOM exists in ERPNext UOM table."""
    uom_name = (uom_name or "个").strip()
    if not frappe.db.exists("UOM", uom_name):
        try:
            uom_doc = frappe.new_doc("UOM")
            uom_doc.uom_name = uom_name
            uom_doc.flags.ignore_permissions = True
            uom_doc.insert()
            return uom_doc.name
        except Exception:
            if frappe.db.exists("UOM", "Nos"):
                return "Nos"
            if frappe.db.exists("UOM", "Unit"):
                return "Unit"
    return uom_name


def _ensure_item(item_code_or_name: str, spec: str = "", uom: str = "个", is_stock: bool = False) -> tuple[str, str, str, bool]:
    """Ensure Item exists in ERPNext Item DocType, create non-stock service item if missing."""
    clean_name = (item_code_or_name or "零星费用项").strip()
    clean_uom = _ensure_uom(uom)

    # 1. 查找是否存在完全一致的 item_code
    if frappe.db.exists("Item", clean_name):
        doc = frappe.db.get_value("Item", clean_name, ["item_name", "stock_uom", "is_stock_item"], as_dict=True)
        return clean_name, doc.item_name, doc.stock_uom, bool(doc.is_stock_item)

    # 2. 查找是否存在 item_name
    match_by_name = frappe.db.get_value("Item", {"item_name": clean_name}, ["name", "item_name", "stock_uom", "is_stock_item"], as_dict=True)
    if match_by_name:
        return match_by_name.name, match_by_name.item_name, match_by_name.stock_uom, bool(match_by_name.is_stock_item)

    # 3. 若均不存在，自动建立一个非库存/费用型 Item
    item_doc = frappe.new_doc("Item")
    item_doc.item_code = clean_name
    item_doc.item_name = clean_name
    item_doc.item_group = "All Item Groups"
    item_doc.stock_uom = clean_uom
    item_doc.is_stock_item = 1 if is_stock else 0
    if spec and _meta_has("Item", "custom_spec_model"):
        item_doc.custom_spec_model = spec
    elif spec:
        item_doc.description = spec

    item_doc.flags.ignore_permissions = True
    item_doc.insert()
    return item_doc.name, item_doc.item_name, item_doc.stock_uom, bool(item_doc.is_stock_item)


def _resolve_warehouse_for_company(company: str, preferred: str | None = None) -> str:
    """Determine receiving warehouse for stock items."""
    if preferred and frappe.db.exists("Warehouse", preferred):
        return preferred
    if frappe.db.exists("Warehouse", f"Stores - {company}"):
        return f"Stores - {company}"
    if frappe.db.exists("Warehouse", f"Goods In Transit - {company}"):
        return f"Goods In Transit - {company}"
    whs = frappe.get_all("Warehouse", filters={"company": company, "is_group": 0}, pluck="name", limit=1)
    return whs[0] if whs else ""


@frappe.whitelist(methods=["POST"])
def create_manual_multi_invoice_reimbursement(
    company: str,
    employee: str,
    posting_date: str | None = None,
    title: str | None = None,
    auto_receive_stock: int | bool = 1,
    invoices: list[dict] | str | None = None,
) -> dict:
    """Create multi-invoice reimbursement bundle: PO -> PR(stock) -> PI -> RR."""
    assert_company_access(company)

    if isinstance(invoices, str):
        invoices = json.loads(invoices) or []
    if not invoices:
        frappe.throw(_("请添加至少一张报销发票。"))

    auto_receive_stock = bool(int(auto_receive_stock))
    posting_date_str = posting_date or nowdate()

    # Resolve Employee
    emp_doc_name = None
    if employee:
        emp_match = frappe.db.get_value("Employee", {"name": employee}, "name") or frappe.db.get_value("Employee", {"employee_name": employee}, "name")
        if emp_match:
            emp_doc_name = emp_match

    if not emp_doc_name:
        user_emp = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "company": company}, "name")
        emp_doc_name = user_emp or frappe.db.get_value("Employee", {"company": company}, "name") or ""

    employee_name = frappe.db.get_value("Employee", emp_doc_name, "employee_name") or (employee or "员工")

    default_warehouse = _resolve_warehouse_for_company(company)

    created_po_names = []
    created_pr_names = []
    created_pi_names = []
    all_rr_item_rows = []

    # 1. 逐张发票校验并生成采购链
    for inv_idx, inv in enumerate(invoices, 1):
        inv_type = (inv.get("invoice_type") or "专用发票").strip()
        if inv_type not in VALID_INVOICE_TYPES:
            inv_type = "专用发票"

        supplier_raw = (inv.get("supplier") or "").strip()
        if not supplier_raw:
            supplier_raw = "零星报销供应商" if inv_type == "无发票" else "报销商户"

        supplier_val = _ensure_supplier(supplier_raw)

        bill_no_raw = (inv.get("invoice_no") or "").strip()
        if not bill_no_raw:
            bill_no_raw = f"REIM-NOINV-{posting_date_str.replace('-', '')}-{inv_idx:02d}" if inv_type == "无发票" else f"REIM-INV-{posting_date_str.replace('-', '')}-{inv_idx:02d}"

        bill_date_str = (inv.get("invoice_date") or "").strip() or posting_date_str

        items = inv.get("items") or []
        if not items:
            frappe.throw(_("发票 [{0}] (商户: {1}) 至少需要录入一行有效的明细。").format(bill_no_raw, supplier_raw))

        validated_items = []
        has_stock_items = False

        for row_idx, row in enumerate(items, 1):
            item_code_raw = (row.get("item_code") or "").strip()
            item_name_raw = (row.get("item_name") or item_code_raw or "").strip()

            if not item_code_raw and not item_name_raw:
                frappe.throw(_("发票 [{0}] 第 {1} 行物料名称不能为空。").format(bill_no_raw, row_idx))

            raw_spec = (row.get("spec") or "").strip()
            raw_uom = (row.get("uom") or "个").strip()

            # 确保物料与单位安全建立/匹配
            final_code, final_name, final_uom, is_stock = _ensure_item(
                item_code_or_name=item_code_raw or item_name_raw,
                spec=raw_spec,
                uom=raw_uom,
                is_stock=False,
            )

            qty = flt(row.get("qty") or 1.0)
            rate = flt(row.get("rate") or 0.0)
            amount = flt(row.get("amount") or (qty * rate))

            if qty <= 0 or rate <= 0 or amount <= 0:
                frappe.throw(
                    _("发票 [{0}] 第 {1} 行 [{2}] 的数量({3})、单价(¥{4:.2f})或金额(¥{5:.2f})必须大于0！根据财务纪律，单价与金额严禁为0。").format(
                        bill_no_raw, row_idx, final_name, qty, rate, amount
                    )
                )

            # 税率：普通发票或无发票默认税率为 0
            if inv_type in ("普通发票", "无发票"):
                tax_rate = 0.0
            else:
                tax_rate = flt(row.get("tax_rate") or 13.0)

            tax_amount = flt(amount * (tax_rate / 100.0), 2)
            line_total = flt(amount + tax_amount, 2)

            if is_stock:
                has_stock_items = True

            validated_items.append({
                "idx": row_idx,
                "item_code": final_code,
                "item_name": final_name,
                "spec": raw_spec,
                "uom": final_uom,
                "qty": qty,
                "rate": rate,
                "amount": amount,
                "tax_rate": tax_rate,
                "tax_amount": tax_amount,
                "line_total": line_total,
                "remarks": (row.get("remarks") or "").strip(),
                "is_stock_item": is_stock,
                "warehouse": default_warehouse if is_stock else None,
            })

        # --- 生成发票对应的 PO ---
        po = frappe.new_doc("Purchase Order")
        po.company = company
        po.supplier = supplier_val
        po.transaction_date = posting_date_str
        po.schedule_date = posting_date_str
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
                "schedule_date": posting_date_str,
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
                po_row.custom_total_amount = it["line_total"]

        po.flags.ignore_permissions = True
        po.insert()
        po.submit()
        created_po_names.append(po.name)

        # --- 生成发票对应的 PR (若库存品) ---
        pr_name = None
        pr_item_map = {}
        if auto_receive_stock and has_stock_items:
            pr = frappe.new_doc("Purchase Receipt")
            pr.company = company
            pr.supplier = supplier_val
            pr.posting_date = posting_date_str
            pr.custom_biz_mode = "现金报销"

            for idx, it in enumerate(validated_items):
                if not it["is_stock_item"]:
                    continue
                po_row = po.items[idx]
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
                    "purchase_order_item": po_row.name,
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
                    pr_row.custom_total_amount = it["line_total"]

            if pr.items:
                pr.flags.ignore_permissions = True
                pr.insert()
                pr.submit()
                pr_name = pr.name
                created_pr_names.append(pr.name)
                for p_item in pr.items:
                    pr_item_map[p_item.item_code] = p_item.name

        # --- 生成发票对应的 PI ---
        pi = frappe.new_doc("Purchase Invoice")
        pi.company = company
        pi.supplier = supplier_val
        pi.bill_no = bill_no_raw
        pi.bill_date = bill_date_str
        pi.posting_date = posting_date_str
        pi.custom_biz_mode = "现金报销"
        if _meta_has("Purchase Invoice", "custom_invoice_type"):
            pi.custom_invoice_type = inv_type

        for idx, it in enumerate(validated_items):
            po_row = po.items[idx]
            pi_row = pi.append("items", {
                "item_code": it["item_code"],
                "item_name": it["item_name"],
                "uom": it["uom"],
                "stock_uom": it["uom"],
                "qty": it["qty"],
                "rate": it["rate"],
                "amount": it["amount"],
                "purchase_order": po.name,
                "po_detail": po_row.name,
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
                pi_row.custom_total_amount = it["line_total"]

        pi.flags.ignore_permissions = True
        pi.insert()
        pi.submit()
        created_pi_names.append(pi.name)

        # 收集该发票明细行供汇总进入 RR
        for idx, it in enumerate(validated_items):
            pi_item_row = pi.items[idx]
            all_rr_item_rows.append({
                "item_name": it["item_name"],
                "description": it["spec"],
                "qty": it["qty"],
                "rate": it["rate"],
                "amount": it["line_total"],  # 报销金额为价税合计
                "invoice_no": bill_no_raw,
                "supplier": supplier_val,
                "source_pi": pi.name,
                "source_pi_item": pi_item_row.name,
                "custom_line_remark": it["remarks"],
                "invoice_type": inv_type,
                "invoice_date": bill_date_str,
                "tax_rate": it["tax_rate"],
                "tax_amount": it["tax_amount"],
            })

    # 2. 创建 Reimbursement Request (Submitted)
    rr = frappe.new_doc("Reimbursement Request")
    rr.company = company
    rr.title = title or f"现金报销-{employee_name}-{posting_date_str} ({len(invoices)}张发票)"
    if emp_doc_name:
        rr.employee = emp_doc_name
    if employee_name:
        rr.employee_name = employee_name
    rr.posting_date = posting_date_str
    rr.custom_biz_mode = "现金报销"

    for r_it in all_rr_item_rows:
        row_dict = {
            "item_name": r_it["item_name"],
            "description": r_it["description"],
            "qty": r_it["qty"],
            "rate": r_it["rate"],
            "amount": r_it["amount"],
            "invoice_no": r_it["invoice_no"],
            "supplier": r_it["supplier"],
            "source_pi": r_it["source_pi"],
            "source_pi_item": r_it["source_pi_item"],
        }
        if _meta_has("Reimbursement Invoice Item", "custom_line_remark"):
            row_dict["custom_line_remark"] = r_it["custom_line_remark"]
        if _meta_has("Reimbursement Invoice Item", "invoice_type"):
            row_dict["invoice_type"] = r_it["invoice_type"]
        if _meta_has("Reimbursement Invoice Item", "invoice_date"):
            row_dict["invoice_date"] = r_it["invoice_date"]
        if _meta_has("Reimbursement Invoice Item", "tax_rate"):
            row_dict["tax_rate"] = r_it["tax_rate"]
        if _meta_has("Reimbursement Invoice Item", "tax_amount"):
            row_dict["tax_amount"] = r_it["tax_amount"]

        rr.append("invoice_items", row_dict)

    rr.flags.ignore_permissions = True
    rr.insert()
    rr.submit()

    # 3. 刷新 custom_doc_details
    try:
        from ashan_cn_procurement.overrides.document_details import update_doc_details
        update_doc_details(rr)
        if rr.get("custom_doc_details"):
            frappe.db.set_value("Reimbursement Request", rr.name, "custom_doc_details", rr.custom_doc_details, update_modified=False)
    except Exception:
        pass

    return {
        "success": True,
        "rr_name": rr.name,
        "invoice_count": len(invoices),
        "grand_total": flt(rr.total_amount, 2),
        "created_po_names": created_po_names,
        "created_pr_names": created_pr_names,
        "created_pi_names": created_pi_names,
    }


@frappe.whitelist()
def search_items_for_reimbursement(txt: str = "", limit: int = 20) -> list[dict]:
    """Search items for reimbursement by item_code, item_name or spec."""
    txt = (txt or "").strip()
    has_spec = _meta_has("Item", "custom_spec_model")
    spec_col = "custom_spec_model" if has_spec else "description"

    filters = [
        ["disabled", "=", 0],
    ]
    or_filters = [
        ["name", "like", f"%{txt}%"],
        ["item_name", "like", f"%{txt}%"],
    ]
    if has_spec:
        or_filters.append(["custom_spec_model", "like", f"%{txt}%"])
    else:
        or_filters.append(["description", "like", f"%{txt}%"])

    items = frappe.get_all(
        "Item",
        filters=filters,
        or_filters=or_filters if txt else None,
        fields=["name AS item_code", "item_name", f"{spec_col} AS spec", "stock_uom AS uom", "is_stock_item"],
        limit=int(limit or 20),
        order_by="name ASC",
    )
    return items
