# -*- coding: utf-8 -*-
# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint, now_datetime, getdate, nowdate

def is_invoice_month_locked(company, period):
    """
    检查指定公司在指定月份（YYYY-MM）是否已完成发票月度核定关账锁定
    """
    if not company or not period:
        return False
    
    period = str(period).strip()[:7]
    if not frappe.db.exists("DocType", "Monthly Invoice Closing"):
        return False

    return bool(frappe.db.exists("Monthly Invoice Closing", {
        "company": company,
        "period": period,
        "is_locked": 1
    }))

@frappe.whitelist()
def get_invoice_closing_data(company, period):
    """
    获取指定公司与月份的发票核定数据统计
    """
    if not company or not period:
        frappe.throw(_("请指定公司和核定账期"))

    period = str(period).strip()[:7]
    doc_name = f"INV-CLOSE-{company}-{period}"

    # 统计当月发票数据 (Purchase Invoice)
    # 以 bill_date 或 posting_date 属于当期为准
    sql = """
        SELECT 
            COUNT(name) as count,
            COALESCE(SUM(base_net_total), 0) as net_amount,
            COALESCE(SUM(total_taxes_and_charges), 0) as tax_amount,
            COALESCE(SUM(base_grand_total), 0) as grand_total
        FROM `tabPurchase Invoice`
        WHERE company = %s
          AND (
            (bill_date >= %s AND bill_date <= %s)
            OR (posting_date >= %s AND posting_date <= %s)
          )
          AND docstatus = 1
    """
    start_date = f"{period}-01"
    end_date = f"{period}-31"
    
    stats = frappe.db.sql(sql, (company, start_date, end_date, start_date, end_date), as_dict=True)
    inv_count = cint(stats[0].count) if stats else 0
    net_amt = flt(stats[0].net_amount) if stats else 0.0
    tax_amt = flt(stats[0].tax_amount) if stats else 0.0
    grand_tot = flt(stats[0].grand_total) if stats else 0.0

    closing_doc = None
    if frappe.db.exists("Monthly Invoice Closing", doc_name):
        closing_doc = frappe.get_doc("Monthly Invoice Closing", doc_name).as_dict()

    is_locked = bool(closing_doc and closing_doc.get("is_locked") == 1)

    return {
        "company": company,
        "period": period,
        "doc_name": doc_name,
        "is_locked": is_locked,
        "status": closing_doc.get("status") if closing_doc else ("已核定" if is_locked else "草稿"),
        "invoice_count": inv_count,
        "total_net_amount": net_amt,
        "total_tax_amount": tax_amt,
        "total_grand_total": grand_tot,
        "locked_by": closing_doc.get("locked_by") if closing_doc else None,
        "locked_at": str(closing_doc.get("locked_at")) if closing_doc and closing_doc.get("locked_at") else None,
        "unlock_reason": closing_doc.get("unlock_reason") if closing_doc else None,
        "notes": closing_doc.get("notes") if closing_doc else ""
    }

@frappe.whitelist(methods=["POST"])
def lock_monthly_invoice_closing(company, period, notes=None):
    """
    核定并锁定指定公司当月发票台账
    """
    if not company or not period:
        frappe.throw(_("请指定公司和核定账期"))

    roles = frappe.get_roles(frappe.session.user)
    if not (frappe.session.user == "Administrator" or any(r in roles for r in ["System Manager", "Accounts Manager", "财务经理"])):
        frappe.throw(_("只有财务主管或管理员有权执行发票月度核定关账！"), frappe.PermissionError)

    period = str(period).strip()[:7]
    doc_name = f"INV-CLOSE-{company}-{period}"

    data = get_invoice_closing_data(company, period)

    if frappe.db.exists("Monthly Invoice Closing", doc_name):
        doc = frappe.get_doc("Monthly Invoice Closing", doc_name)
    else:
        doc = frappe.new_doc("Monthly Invoice Closing")
        doc.company = company
        doc.period = period

    doc.is_locked = 1
    doc.status = "已核定"
    doc.invoice_count = data["invoice_count"]
    doc.total_net_amount = data["total_net_amount"]
    doc.total_tax_amount = data["total_tax_amount"]
    doc.total_grand_total = data["total_grand_total"]
    doc.locked_by = frappe.session.user
    doc.locked_at = now_datetime()
    if notes:
        doc.notes = notes

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": f"✅ {company} {period} 发票台账已正式核定并锁定！该月份发票进入只读封账保护。",
        "doc": doc.as_dict()
    }

@frappe.whitelist(methods=["POST"])
def unlock_monthly_invoice_closing(company, period, unlock_reason=None):
    """
    反审核解锁指定公司当月发票台账
    """
    if not company or not period:
        frappe.throw(_("请指定公司和核定账期"))

    roles = frappe.get_roles(frappe.session.user)
    if not (frappe.session.user == "Administrator" or any(r in roles for r in ["System Manager", "Accounts Manager", "财务经理"])):
        frappe.throw(_("只有财务主管或管理员有权执行发票月度关账解锁！"), frappe.PermissionError)

    if not unlock_reason or len(str(unlock_reason).strip()) < 2:
        frappe.throw(_("请详细填写反审核解锁原因，以便审计追踪！"))

    period = str(period).strip()[:7]
    doc_name = f"INV-CLOSE-{company}-{period}"

    if not frappe.db.exists("Monthly Invoice Closing", doc_name):
        frappe.throw(_("未找到该月发票关账记录"))

    doc = frappe.get_doc("Monthly Invoice Closing", doc_name)
    doc.is_locked = 0
    doc.status = "已解锁"
    doc.unlocked_by = frappe.session.user
    doc.unlocked_at = now_datetime()
    doc.unlock_reason = unlock_reason

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": f"🔓 {company} {period} 发票关账已解锁，允许补充录入或修改。",
        "doc": doc.as_dict()
    }
