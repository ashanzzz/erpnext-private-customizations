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


def _normalize_name_list(values: Any) -> list[str]:
    """Return safe, de-duplicated document names from RPC input."""
    if isinstance(values, str):
        values = frappe.parse_json(values)
    if not isinstance(values, (list, tuple, set)):
        return []
    return list(dict.fromkeys(str(v).strip() for v in values if str(v).strip()))


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

    # 4. 可用税局发票数
    tax_inv_ready_count = frappe.db.sql("""
        SELECT COUNT(name)
        FROM `tabTax Invoice`
        WHERE company IN %s
          AND business_status != '已废弃'
          AND business_status != '已对冲'
          AND COALESCE(parse_status, '已解析') = '已解析'
    """, (companies,))[0][0] or 0

    return {
        "pending_rr_count": pending_rr_count,
        "rr_total_count": rr_total_count,
        "rr_grand_total": rr_grand_total,
        "rr_outstanding": rr_outstanding,
        "pi_count": pi_count,
        "pr_count": pr_count,
        "tax_inv_ready_count": tax_inv_ready_count,
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

        # Display masked invoice numbers (show last 8 chars for elegance)
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
# 3. Reimbursement V2 Engine (Multi-Tax-Invoice Driven)
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


def _classify_tax_invoice_for_reimbursement(row: dict, company: str) -> tuple[str, list[dict]]:
    """Determine eligibility and issues for one Tax Invoice."""
    issues = []
    eligibility = "ready"

    # 1. 基础阻断检查
    if row.get("business_status") == "已废弃":
        issues.append({"level": "blocked", "message": "发票已被废弃，禁止报销"})
        eligibility = "blocked"

    if row.get("business_status") == "已对冲":
        issues.append({"level": "blocked", "message": "发票已红冲对冲，无需报销"})
        eligibility = "blocked"

    if row.get("company") and row.get("company") != company:
        issues.append({"level": "blocked", "message": f"发票所属公司({row.get('company')})与报销公司不一致"})
        eligibility = "blocked"

    parse_warning = row.get("parse_warning") or ""
    if "购买方" in parse_warning or "纳税人识别号不匹配" in parse_warning:
        issues.append({"level": "blocked", "message": f"发票购买方信息异常: {parse_warning}"})
        eligibility = "blocked"

    if flt(row.get("payable_total")) <= 0:
        issues.append({"level": "blocked", "message": "发票应付金额必须大于 0"})
        eligibility = "blocked"

    # 2. 检查是否已被有效 Reservation 占用
    res_key = f"TAXINV::{row.get('name')}"
    active_res = frappe.get_all(
        "Reimbursement Source Reservation",
        filters={"active_source_key": res_key, "status": ["in", ("Draft", "Submitted")]},
        fields=["name", "reimbursement_request", "status"],
        limit=1,
    )
    if active_res:
        issues.append({
            "level": "blocked",
            "message": f"发票已被报销单 {active_res[0].reimbursement_request} 占用",
        })
        eligibility = "blocked"

    # 3. 检查采购发票 (PI) 状态
    matched_pi = row.get("matched_purchase_invoice")
    if matched_pi:
        pi_doc = frappe.db.get_value("Purchase Invoice", matched_pi, ["name", "docstatus", "outstanding_amount", "company", "supplier"], as_dict=True)
        if not pi_doc:
            issues.append({"level": "warning", "message": "关联的采购发票已不存在，将重新规划单据"})
        elif pi_doc.docstatus != 1:
            issues.append({"level": "blocked", "message": f"关联的采购发票 {matched_pi} 未提交(Draft/Cancelled)"})
            eligibility = "blocked"
        elif flt(pi_doc.outstanding_amount) <= 0.0001:
            issues.append({"level": "warning", "message": f"关联的采购发票 {matched_pi} 已经全额结清"})
    else:
        # 没有 PI 时，预查供应商
        seller_tax_id = (row.get("seller_tax_id") or "").strip()
        seller_name = (row.get("seller_name") or "").strip()
        supp_name = None
        if seller_tax_id:
            supp_name = frappe.db.get_value("Supplier", {"tax_id": seller_tax_id}, "name")
        if not supp_name and seller_name:
            supp_name = frappe.db.get_value("Supplier", {"supplier_name": seller_name}, "name") or (seller_name if frappe.db.exists("Supplier", seller_name) else None)

        if not supp_name and eligibility != "blocked":
            issues.append({"level": "warning", "message": f"销售方 [{seller_name or seller_tax_id}] 尚未在 ERP 供应商档案中建档"})
            eligibility = "need_supplier"

    return eligibility, issues


@frappe.whitelist()
def get_reimbursable_tax_invoices(
    company: str,
    filters: dict | str | None = None,
    start: int = 0,
    page_length: int = 50,
) -> dict:
    """Query reimbursable Tax Invoices for multi-selection."""
    assert_company_access(company)
    filters = _normalize_dict(filters)

    start = max(int(start or 0), 0)
    page_length = min(max(int(page_length or 50), 1), 100)

    conditions = [
        "company = %(company)s",
        "business_status != '已废弃'",
    ]
    params: dict[str, Any] = {"company": company, "start": start, "page_length": page_length}

    if filters.get("search"):
        conditions.append("""(
            invoice_no LIKE %(search)s
            OR seller_name LIKE %(search)s
            OR display_summary LIKE %(search)s
        )""")
        params["search"] = f"%{filters['search']}%"

    if filters.get("from_date"):
        conditions.append("issue_date >= %(from_date)s")
        params["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("issue_date <= %(to_date)s")
        params["to_date"] = filters["to_date"]

    if filters.get("invoice_type"):
        conditions.append("invoice_type = %(invoice_type)s")
        params["invoice_type"] = filters["invoice_type"]

    if filters.get("pi_mode") == "has_pi":
        conditions.append("matched_purchase_invoice IS NOT NULL AND matched_purchase_invoice != ''")
    elif filters.get("pi_mode") == "need_pi":
        conditions.append("(matched_purchase_invoice IS NULL OR matched_purchase_invoice = '')")

    where_sql = " AND ".join(conditions)

    # 统计总数与分类计数
    count_sql = f"""
        SELECT
            COUNT(*) AS total_count,
            SUM(CASE WHEN matched_purchase_invoice IS NOT NULL AND matched_purchase_invoice != '' THEN 1 ELSE 0 END) AS has_pi_count,
            SUM(CASE WHEN (matched_purchase_invoice IS NULL OR matched_purchase_invoice = '') THEN 1 ELSE 0 END) AS need_pi_count
        FROM `tabTax Invoice`
        WHERE {where_sql}
    """
    counts = frappe.db.sql(count_sql, params, as_dict=True)[0]
    total = counts.total_count or 0

    # 获取列表记录
    rows_sql = f"""
        SELECT
            name,
            invoice_no,
            issue_date,
            invoice_type,
            business_status,
            match_status,
            COALESCE(parse_status, '已解析') AS parse_status,
            COALESCE(parse_warning, '') AS parse_warning,
            COALESCE(seller_name, '') AS seller_name,
            COALESCE(seller_tax_id, '') AS seller_tax_id,
            COALESCE(display_summary, '') AS display_summary,
            COALESCE(payable_total, 0) AS payable_total,
            COALESCE(matched_purchase_invoice, '') AS matched_purchase_invoice
        FROM `tabTax Invoice`
        WHERE {where_sql}
        ORDER BY issue_date DESC, name DESC
        LIMIT %(start)s, %(page_length)s
    """
    raw_rows = frappe.db.sql(rows_sql, params, as_dict=True)

    result_rows = []
    ready_count = 0
    review_count = 0
    blocked_count = 0

    for r in raw_rows:
        eligibility, issues = _classify_tax_invoice_for_reimbursement(r, company)
        if eligibility == "ready":
            ready_count += 1
        elif eligibility in ("need_supplier", "need_item"):
            review_count += 1
        else:
            blocked_count += 1

        masked_no = f"…{r.invoice_no[-8:]}" if len(r.invoice_no or "") > 8 else (r.invoice_no or "-")

        result_rows.append({
            "name": r.name,
            "invoice_no": r.invoice_no,
            "masked_invoice_no": masked_no,
            "issue_date": str(r.issue_date or ""),
            "invoice_type": r.invoice_type or "专用发票",
            "seller_name": r.seller_name or "未指定",
            "seller_tax_id": r.seller_tax_id or "",
            "display_summary": r.display_summary or "发票明细",
            "payable_total": flt(r.payable_total, 2),
            "business_status": r.business_status or "待录入",
            "parse_status": r.parse_status,
            "match_status": r.match_status or "未匹配",
            "matched_purchase_invoice": r.matched_purchase_invoice or "",
            "erp_state": "has_pi" if r.matched_purchase_invoice else "need_pi",
            "eligibility": eligibility,
            "issues": issues,
            "issue_count": len(issues),
        })

    return {
        "rows": result_rows,
        "total": total,
        "ready_count": ready_count,
        "review_count": review_count,
        "blocked_count": blocked_count,
    }


# =========================================================================
# 4. Preview Engine (Read-only Dry-run)
# =========================================================================

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


def _build_single_invoice_preview(
    tax_inv_name: str,
    company: str,
    resolutions: dict,
    auto_receive_stock: bool,
) -> dict:
    """Build dry-run preview and action plan for one Tax Invoice."""
    tax_inv = frappe.get_doc("Tax Invoice", tax_inv_name)
    issues = []
    status = "ready"

    # 1. 基础校验
    if tax_inv.company != company:
        issues.append({"level": "blocked", "message": f"发票所属公司({tax_inv.company})与报销公司不一致"})
        status = "blocked"

    if tax_inv.business_status in ("已废弃", "已对冲"):
        issues.append({"level": "blocked", "message": f"发票状态为 {tax_inv.business_status}，禁止报销"})
        status = "blocked"

    # 2. 检查已有 PI 复用
    pi_mode = "create"
    pi_name = None
    pi_supplier = None
    pi_items = []
    payable_amount = flt(tax_inv.payable_total, 2)

    if tax_inv.matched_purchase_invoice:
        pi_data = frappe.db.get_value(
            "Purchase Invoice",
            tax_inv.matched_purchase_invoice,
            ["name", "company", "bill_no", "supplier", "docstatus", "outstanding_amount", "grand_total"],
            as_dict=True,
        )
        if pi_data and pi_data.docstatus == 1 and pi_data.company == company:
            pi_mode = "reuse"
            pi_name = pi_data.name
            pi_supplier = pi_data.supplier
            # 可报销金额为当前待付金额
            available_amt = min(payable_amount, flt(pi_data.outstanding_amount, 2))
            if available_amt <= 0.0001:
                issues.append({"level": "warning", "message": f"关联发票 {pi_name} 已无可报销待付额"})

    # 3. 若需新建 PI，解析 Supplier 和 Items
    if pi_mode == "create":
        # 解析 Supplier
        seller_tax_id = (tax_inv.seller_tax_id or "").strip()
        seller_name = (tax_inv.seller_name or "").strip()
        explicit_supp = (resolutions.get("suppliers") or {}).get(tax_inv_name)

        if explicit_supp and frappe.db.exists("Supplier", explicit_supp):
            pi_supplier = explicit_supp
        elif seller_tax_id and frappe.db.exists("Supplier", {"tax_id": seller_tax_id}):
            pi_supplier = frappe.db.get_value("Supplier", {"tax_id": seller_tax_id}, "name")
        elif seller_name and frappe.db.exists("Supplier", {"supplier_name": seller_name}):
            pi_supplier = frappe.db.get_value("Supplier", {"supplier_name": seller_name}, "name")
        elif seller_name and frappe.db.exists("Supplier", seller_name):
            pi_supplier = seller_name
        else:
            pi_supplier = None
            issues.append({"level": "blocked", "message": f"未找到供应商 [{seller_name}]，请在档案建档或在解决栏指定"})
            if status != "blocked":
                status = "need_supplier"

        # 解析 Item 明细
        items_resolutions = (resolutions.get("items") or {}).get(tax_inv_name) or {}
        wh_resolution = (resolutions.get("warehouses") or {}).get(tax_inv_name)
        target_wh = _resolve_warehouse_for_company(company, wh_resolution)

        raw_items = frappe.get_all(
            "Tax Invoice Item",
            filters={"parent": tax_inv.name},
            fields=["name", "item_name", "spec_model", "unit", "quantity", "unit_price", "amount", "tax_rate_text", "tax_amount", "line_total"],
            order_by="idx ASC",
        )

        has_stock = False
        parsed_items = []
        for it in raw_items:
            raw_name = (it.item_name or "").strip()
            item_code = items_resolutions.get(it.name) or items_resolutions.get(raw_name)

            if not item_code:
                if frappe.db.exists("Item", raw_name):
                    item_code = raw_name
                elif frappe.db.exists("Item", {"item_name": raw_name}):
                    item_code = frappe.db.get_value("Item", {"item_name": raw_name}, "name")

            item_meta = None
            if item_code:
                item_meta = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom", "is_stock_item"], as_dict=True)

            if not item_meta:
                issues.append({"level": "blocked", "message": f"物料 [{raw_name}] 无法匹配到 ERP 物料编码"})
                if status == "ready":
                    status = "need_item"

            is_stock = bool(item_meta.is_stock_item) if item_meta else False
            if is_stock:
                has_stock = True

            qty = flt(it.quantity) or 1.0
            amt = flt(it.amount) or flt(it.line_total)
            rate = flt(it.unit_price) or (flt(amt / qty, 2) if qty else amt)
            tax_rate = flt(str(it.tax_rate_text or "13").replace("%", ""))
            tax_amt = flt(it.tax_amount) or flt(amt * (tax_rate / 100.0), 2)
            total = flt(it.line_total) or flt(amt + tax_amt, 2)

            parsed_items.append({
                "tax_item_name": it.name,
                "raw_item_name": raw_name,
                "spec": it.spec_model or "",
                "uom": it.unit or (item_meta.stock_uom if item_meta else "Nos"),
                "qty": qty,
                "rate": rate,
                "amount": amt,
                "tax_rate": tax_rate,
                "tax_amount": tax_amt,
                "line_total": total,
                "item_code": item_code,
                "is_stock_item": is_stock,
                "warehouse": target_wh if is_stock else "",
            })

        pi_items = parsed_items
        if has_stock and auto_receive_stock and not target_wh:
            issues.append({"level": "blocked", "message": "发票包含库存品，但未找到可用仓库"})
            if status == "ready":
                status = "blocked"

    return {
        "tax_invoice": tax_inv.name,
        "invoice_no": tax_inv.invoice_no,
        "masked_invoice_no": f"…{tax_inv.invoice_no[-8:]}" if len(tax_inv.invoice_no or "") > 8 else tax_inv.invoice_no,
        "issue_date": str(tax_inv.issue_date or ""),
        "invoice_type": tax_inv.invoice_type or "专用发票",
        "seller_name": tax_inv.seller_name or "",
        "seller_tax_id": tax_inv.seller_tax_id or "",
        "payable_total": payable_amount,
        "status": status,
        "purchase_invoice_mode": pi_mode,
        "purchase_invoice": pi_name,
        "supplier": pi_supplier,
        "items": pi_items,
        "issues": issues,
    }


def _build_reimbursement_preview(
    company: str,
    employee: str,
    tax_invoice_names: list[str],
    resolutions: dict,
    auto_receive_stock: bool,
) -> dict:
    """Build full dry-run preview for all selected Tax Invoices."""
    invoices_preview = []
    suppliers_set = set()
    grand_total = 0.0
    existing_pi_count = 0
    new_pi_count = 0
    stock_inv_count = 0
    blocking_count = 0
    warning_count = 0

    for name in tax_invoice_names:
        plan = _build_single_invoice_preview(name, company, resolutions, auto_receive_stock)
        invoices_preview.append(plan)

        if plan["supplier"]:
            suppliers_set.add(plan["supplier"])
        grand_total += plan["payable_total"]

        if plan["purchase_invoice_mode"] == "reuse":
            existing_pi_count += 1
        else:
            new_pi_count += 1

        if any(it.get("is_stock_item") for it in plan.get("items", [])):
            stock_inv_count += 1

        for iss in plan.get("issues", []):
            if iss.get("level") == "blocked":
                blocking_count += 1
            else:
                warning_count += 1

    return {
        "ready": (blocking_count == 0),
        "blocking_count": blocking_count,
        "warning_count": warning_count,
        "summary": {
            "invoice_count": len(invoices_preview),
            "supplier_count": len(suppliers_set),
            "grand_total": flt(grand_total, 2),
            "existing_pi_count": existing_pi_count,
            "new_pi_count": new_pi_count,
            "stock_invoice_count": stock_inv_count,
        },
        "invoices": invoices_preview,
    }


@frappe.whitelist()
def preview_tax_invoice_reimbursement(
    company: str,
    employee: str,
    tax_invoice_names: Any,
    resolutions: Any = None,
    auto_receive_stock: int | bool = 1,
) -> dict:
    """Public read-only dry-run preview API."""
    assert_company_access(company)
    names = _normalize_name_list(tax_invoice_names)
    if not names:
        frappe.throw(_("请选择至少一张税局发票。"))

    res_dict = _normalize_dict(resolutions)
    return _build_reimbursement_preview(
        company=company,
        employee=employee,
        tax_invoice_names=names,
        resolutions=res_dict,
        auto_receive_stock=bool(int(auto_receive_stock)),
    )


# =========================================================================
# 5. Create Transaction Engine (Atomic POST)
# =========================================================================

def _reserve_tax_invoices(rr_name: str, invoice_plans: list[dict]) -> None:
    """Create persistent Tax Invoice reservations to prevent concurrency/duplication."""
    for plan in invoice_plans:
        tax_inv_name = plan["tax_invoice"]
        res = frappe.get_doc({
            "doctype": "Reimbursement Source Reservation",
            "reimbursement_request": rr_name,
            "source_kind": "Tax Invoice",
            "source_tax_invoice": tax_inv_name,
            "active_source_key": f"TAXINV::{tax_inv_name}",
            "reserved_amount": plan["payable_total"],
            "status": "Draft",
        })
        try:
            res.insert(ignore_permissions=True)
        except frappe.DuplicateEntryError:
            frappe.throw(_("发票 [{0}] 已被其它报销单占用，请刷新后重试。").format(tax_inv_name))


def _create_purchase_package_from_tax_invoice(
    invoice_plan: dict,
    company: str,
    posting_date: str,
    auto_receive_stock: bool,
) -> dict:
    """Create PO + PR(if stock) + PI for one Tax Invoice."""
    supplier_val = invoice_plan["supplier"]
    bill_no_val = invoice_plan["invoice_no"]
    bill_date_str = invoice_plan["issue_date"] or posting_date
    invoice_type = invoice_plan["invoice_type"] or "专用发票"
    items = invoice_plan["items"]

    # 1. Purchase Order
    po = frappe.new_doc("Purchase Order")
    po.company = company
    po.supplier = supplier_val
    po.transaction_date = posting_date
    po.schedule_date = posting_date
    po.custom_biz_mode = "现金报销"

    for it in items:
        po_row = po.append("items", {
            "item_code": it["item_code"],
            "item_name": it["raw_item_name"],
            "uom": it["uom"],
            "stock_uom": it["uom"],
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": it["amount"],
            "schedule_date": posting_date,
            "warehouse": it["warehouse"] if it["is_stock_item"] else None,
            "description": it["raw_item_name"],
        })
        if _meta_has("Purchase Order Item", "custom_spec_model"):
            po_row.custom_spec_model = it["spec"]
        if _meta_has("Purchase Order Item", "custom_tax_rate"):
            po_row.custom_tax_rate = it["tax_rate"]
        if _meta_has("Purchase Order Item", "custom_tax_amount"):
            po_row.custom_tax_amount = it["tax_amount"]
        if _meta_has("Purchase Order Item", "custom_total_amount"):
            po_row.custom_total_amount = it["line_total"]

    po.flags.ignore_permissions = True
    po.insert()
    po.submit()

    # 2. Purchase Receipt (if stock item and auto_receive_stock)
    pr_name = None
    pr_item_map = {}
    has_stock = any(it["is_stock_item"] for it in items)

    if auto_receive_stock and has_stock:
        pr = frappe.new_doc("Purchase Receipt")
        pr.company = company
        pr.supplier = supplier_val
        pr.posting_date = posting_date
        pr.custom_biz_mode = "现金报销"

        for idx, it in enumerate(items):
            if not it["is_stock_item"]:
                continue
            po_row = po.items[idx]
            pr_row = pr.append("items", {
                "item_code": it["item_code"],
                "item_name": it["raw_item_name"],
                "uom": it["uom"],
                "stock_uom": it["uom"],
                "qty": it["qty"],
                "rate": it["rate"],
                "amount": it["amount"],
                "warehouse": it["warehouse"],
                "purchase_order": po.name,
                "purchase_order_item": po_row.name,
                "description": it["raw_item_name"],
            })
            if _meta_has("Purchase Receipt Item", "custom_spec_model"):
                pr_row.custom_spec_model = it["spec"]
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
            for p_item in pr.items:
                pr_item_map[p_item.item_code] = p_item.name

    # 3. Purchase Invoice
    pi = frappe.new_doc("Purchase Invoice")
    pi.company = company
    pi.supplier = supplier_val
    pi.bill_no = bill_no_val
    pi.bill_date = bill_date_str
    pi.posting_date = posting_date
    pi.custom_biz_mode = "现金报销"
    if _meta_has("Purchase Invoice", "custom_invoice_type"):
        pi.custom_invoice_type = invoice_type

    for idx, it in enumerate(items):
        po_row = po.items[idx]
        pi_row = pi.append("items", {
            "item_code": it["item_code"],
            "item_name": it["raw_item_name"],
            "uom": it["uom"],
            "stock_uom": it["uom"],
            "qty": it["qty"],
            "rate": it["rate"],
            "amount": it["amount"],
            "purchase_order": po.name,
            "po_detail": po_row.name,
            "purchase_receipt": pr_name if (it["is_stock_item"] and pr_name) else None,
            "pr_detail": pr_item_map.get(it["item_code"]) if (it["is_stock_item"] and pr_name) else None,
            "description": it["raw_item_name"],
        })
        if _meta_has("Purchase Invoice Item", "custom_spec_model"):
            pi_row.custom_spec_model = it["spec"]
        if _meta_has("Purchase Invoice Item", "custom_tax_rate"):
            pi_row.custom_tax_rate = it["tax_rate"]
        if _meta_has("Purchase Invoice Item", "custom_tax_amount"):
            pi_row.custom_tax_amount = it["tax_amount"]
        if _meta_has("Purchase Invoice Item", "custom_total_amount"):
            pi_row.custom_total_amount = it["line_total"]

    pi.flags.ignore_permissions = True
    pi.insert()
    pi.submit()

    # Link back to Tax Invoice
    frappe.db.set_value("Tax Invoice", invoice_plan["tax_invoice"], {
        "matched_purchase_invoice": pi.name,
        "match_status": "已匹配",
        "business_status": "已录入",
    }, update_modified=False)

    return {
        "po_name": po.name,
        "pr_name": pr_name,
        "pi_name": pi.name,
    }


def _attach_source_tax_invoice_to_rr(rr, tax_invoice_names: list[str]) -> None:
    """Map and attach source_tax_invoice link to RR child rows."""
    tax_rows = frappe.get_all(
        "Tax Invoice",
        filters={"name": ["in", tax_invoice_names]},
        fields=["name", "invoice_no", "matched_purchase_invoice"],
    )

    by_pi = {}
    by_bill_no = {}
    for r in tax_rows:
        if r.matched_purchase_invoice:
            by_pi[r.matched_purchase_invoice] = r.name
        if r.invoice_no:
            by_bill_no[r.invoice_no] = r.name

    pi_names = list({row.source_pi for row in rr.invoice_items if row.source_pi})
    pi_bill_map = {}
    if pi_names:
        for p in frappe.get_all("Purchase Invoice", filters={"name": ["in", pi_names]}, fields=["name", "bill_no"]):
            pi_bill_map[p.name] = p.bill_no

    for row in rr.invoice_items:
        t_name = by_pi.get(row.source_pi)
        if not t_name and row.source_pi:
            b_no = pi_bill_map.get(row.source_pi)
            t_name = by_bill_no.get(b_no)
        if t_name:
            row.source_tax_invoice = t_name


@frappe.whitelist(methods=["POST"])
def create_tax_invoice_reimbursement(
    company: str,
    employee: str,
    posting_date: str,
    tax_invoice_names: Any,
    title: str | None = None,
    resolutions: Any = None,
    auto_receive_stock: int | bool = 1,
) -> dict:
    """Create multi-tax-invoice reimbursement bundle atomically."""
    assert_company_access(company)
    names = _normalize_name_list(tax_invoice_names)
    if not names:
        frappe.throw(_("请选择至少一张发票。"))

    res_dict = _normalize_dict(resolutions)
    auto_receive_stock = bool(int(auto_receive_stock))
    posting_date = posting_date or nowdate()

    # 1. 严格二次预检（服务器事实）
    preview = _build_reimbursement_preview(
        company=company,
        employee=employee,
        tax_invoice_names=names,
        resolutions=res_dict,
        auto_receive_stock=auto_receive_stock,
    )

    if preview["blocking_count"] > 0:
        frappe.throw(_("当前仍有 {0} 项阻断问题未解决，不能创建报销。").format(preview["blocking_count"]))

    # Resolve Employee name
    emp_name = frappe.db.get_value("Employee", employee, "employee_name") or employee

    # 2. 创建 Reimbursement Request Draft
    rr = frappe.new_doc("Reimbursement Request")
    rr.company = company
    rr.employee = employee
    rr.employee_name = emp_name
    rr.posting_date = posting_date
    rr.custom_biz_mode = "现金报销"
    rr.title = title or f"现金报销-{emp_name}-{posting_date} ({len(names)}张发票)"
    rr.flags.ignore_permissions = True
    rr.insert()

    # 3. 创建发票占用 (Reservation)
    _reserve_tax_invoices(rr.name, preview["invoices"])

    # 4. 逐张发票生成采购链或复用已有的 PI
    reused_pi_names = []
    created_po_names = []
    created_pr_names = []
    created_pi_names = []
    all_pi_item_names = []

    for inv_plan in preview["invoices"]:
        if inv_plan["purchase_invoice_mode"] == "reuse":
            pi_name = inv_plan["purchase_invoice"]
            reused_pi_names.append(pi_name)
        else:
            package = _create_purchase_package_from_tax_invoice(
                invoice_plan=inv_plan,
                company=company,
                posting_date=posting_date,
                auto_receive_stock=auto_receive_stock,
            )
            pi_name = package["pi_name"]
            created_pi_names.append(pi_name)
            if package.get("po_name"):
                created_po_names.append(package["po_name"])
            if package.get("pr_name"):
                created_pr_names.append(package["pr_name"])

        # 收集 PI 明细 ID 用于导入 RR
        pi_items = frappe.get_all("Purchase Invoice Item", filters={"parent": pi_name}, pluck="name")
        all_pi_item_names.extend(pi_items)

    # 5. 调用核心 service 将所有 PI items 导入 RR
    from ashan_cn_procurement.reimbursement.service import import_purchase_invoice_items
    import_purchase_invoice_items(
        reimbursement_request_name=rr.name,
        purchase_invoice_item_names=all_pi_item_names,
    )

    # 6. 回填 source_tax_invoice
    rr.reload()
    _attach_source_tax_invoice_to_rr(rr, names)
    rr.flags.ignore_permissions = True
    rr.save()

    # 7. 提交 RR (推进状态与占用声明周期)
    rr.submit()

    # 8. 刷新关联单据详情
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
        "invoice_count": len(names),
        "grand_total": flt(rr.total_amount, 2),
        "reused_pi_names": reused_pi_names,
        "created_po_names": created_po_names,
        "created_pr_names": created_pr_names,
        "created_pi_names": created_pi_names,
    }


# =========================================================================
# 6. Backward Compatibility Stub (Deprecated)
# =========================================================================

def _ensure_supplier(supplier_name: str) -> str:
    """Ensure supplier exists in ERPNext Supplier DocType (Deprecated helper)."""
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
    """[DEPRECATED] Single-invoice entry bundle kept for legacy compatibility."""
    assert_company_access(company)
    return {
        "success": True,
        "message": "Deprecated",
    }
