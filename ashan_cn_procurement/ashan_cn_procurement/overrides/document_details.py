# -*- coding: utf-8 -*-
# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, cint

def update_doc_details(doc, method=None):
    """
    通用【单据明细】(custom_doc_details) 自动推导生成引擎
    支持:
      - Material Request (采购申请)
      - Purchase Order (采购订单)
      - Purchase Receipt (物资入库)
      - Purchase Invoice (采购发票)
      - Reimbursement Request (员工报销申请)
    """
    try:
        dt = doc.doctype
        details_str = ""

        # 1. 采购物料类单据 (MR, PO, PR, PI)
        if dt in ["Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice"]:
            items = doc.get("items") or []
            item_strs = []
            for item in items:
                # 提取物料名称/编号
                name = (item.get("item_name") or item.get("item_code") or item.get("description") or "").strip()
                # 过滤多余换行符与超长描述
                if "\n" in name:
                    name = name.split("\n")[0].strip()
                if len(name) > 30:
                    name = name[:28] + ".."

                qty = flt(item.get("qty"))
                uom = (item.get("uom") or item.get("stock_uom") or "").strip()

                # 格式化数量与单位
                if qty > 0:
                    qty_str = f"{int(qty)}" if qty == int(qty) else f"{qty:.2f}".rstrip("0").rstrip(".")
                    if uom:
                        item_strs.append(f"{name} ({qty_str}{uom})")
                    else:
                        item_strs.append(f"{name} ({qty_str})")
                else:
                    amount = flt(item.get("amount") or item.get("custom_tax_inclusive_amount") or item.get("base_amount"))
                    if amount > 0:
                        item_strs.append(f"{name} (¥{amount:,.2f})")
                    else:
                        item_strs.append(name if name else "物料")

            if not item_strs:
                details_str = ""
            elif len(item_strs) > 3:
                details_str = "、".join(item_strs[:3]) + f" 等共{len(item_strs)}项"
            else:
                details_str = "、".join(item_strs)

        # 2. 报销申请单据 (Reimbursement Request)
        elif dt == "Reimbursement Request":
            invoices = doc.get("invoice_items") or doc.get("invoices") or []
            inv_strs = []
            for inv in invoices:
                inv_type = (inv.get("custom_line_remark") or inv.get("invoice_type") or "发票").strip()
                amt = flt(inv.get("tax_inclusive_amount") or inv.get("tax_exclusive_amount") or inv.get("amount"))
                if amt > 0:
                    inv_strs.append(f"{inv_type} (¥{amt:,.2f})")
                else:
                    inv_strs.append(inv_type)


            if not inv_strs:
                # 若无发票子表，读取报销事由
                reason = (doc.get("reimbursement_reason") or doc.get("description") or "").strip()
                tot = flt(doc.get("total_amount") or doc.get("tax_inclusive_amount"))
                if reason:
                    details_str = f"{reason} (¥{tot:,.2f})" if tot > 0 else reason
                else:
                    details_str = f"报销 (¥{tot:,.2f})" if tot > 0 else ""
            elif len(inv_strs) > 3:
                details_str = "、".join(inv_strs[:3]) + f" 等共{len(inv_strs)}张"
            else:
                details_str = "、".join(inv_strs)

        # 写入字段
        doc.custom_doc_details = details_str

        # 兼顾旧版 Purchase Invoice 字段兼容性
        if dt == "Purchase Invoice" and hasattr(doc, "custom_items_summary"):
            doc.custom_items_summary = details_str

    except Exception as e:
        frappe.logger("document_details").warning(f"Failed to generate doc details for {doc.doctype} {doc.name}: {e}")
