# -*- coding: utf-8 -*-
import frappe
from frappe.utils import flt

def execute():
    """
    1. 为 Purchase Invoice 创建 custom_items_summary 字段
    2. 优化列表展示列 (in_list_view): 显示 ID, naming_series, supplier, posting_date, bill_no, custom_items_summary
    3. 批量回填历史单据的物料摘要
    4. 精简 Purchase Invoice Item 子表字段与行抽屉 (隐藏 90+ 冗余字段)
    """
    cf_name = "Purchase Invoice-custom_items_summary"
    if not frappe.db.exists("Custom Field", cf_name):
        cf = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Purchase Invoice",
            "fieldname": "custom_items_summary",
            "label": "开票物料明细",
            "fieldtype": "Small Text",
            "insert_after": "bill_no",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "in_global_search": 1,
            "read_only": 1,
            "columns": 3,
            "module": "Ashan CN Procurement"
        })
        cf.insert(ignore_permissions=True)
    else:
        cf = frappe.get_doc("Custom Field", cf_name)
        cf.label = "开票物料明细"
        cf.in_list_view = 1
        cf.in_standard_filter = 1
        cf.in_global_search = 1
        cf.read_only = 1
        cf.columns = 3
        cf.save(ignore_permissions=True)

    # 列表列优化：清空 title_field 让第一列始终展示单据编号 (ID)，并开启 naming_series, supplier, grand_total, bill_no
    frappe.db.set_value("DocType", "Purchase Invoice", "title_field", "")
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "naming_series"}, "in_list_view", 1)
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "supplier"}, "in_list_view", 1)
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "grand_total"}, "in_list_view", 1)
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "bill_no"}, "in_list_view", 1)
    frappe.db.set_value("DocField", {"parent": "Purchase Invoice", "fieldname": "due_date"}, "in_list_view", 0)

    # 将 description (说明) 转换为 Data (单行文本)
    frappe.make_property_setter({
        "doctype": "Purchase Invoice Item",
        "fieldname": "description",
        "property": "fieldtype",
        "value": "Data",
        "property_type": "Select"
    }, validate_fields_for_doctype=False)

    frappe.make_property_setter({
        "doctype": "Item",
        "fieldname": "description",
        "property": "fieldtype",
        "value": "Data",
        "property_type": "Select"
    }, validate_fields_for_doctype=False)

    # 精简 Purchase Invoice Item 子表字段
    KEEP_VISIBLE_FIELDS = [
        "item_code", "item_name", "custom_spec_model", "description", "uom",
        "qty", "rate", "custom_tax_rate", "custom_gross_rate", "amount",
        "custom_tax_amount", "custom_gross_amount", "custom_line_remark",
        "col_break1", "col_break7", "quantity_and_rate", "col_break2", "sec_break2", "col_break4"
    ]
    docfields = frappe.db.get_all("DocField", filters={"parent": "Purchase Invoice Item"}, fields=["name", "fieldname"])
    for df in docfields:
        fn = df.fieldname
        if fn and fn not in KEEP_VISIBLE_FIELDS:
            frappe.db.set_value("DocField", df.name, "hidden", 1)
        elif fn in KEEP_VISIBLE_FIELDS:
            frappe.db.set_value("DocField", df.name, "hidden", 0)

    label_updates = {
        "item_code": "物料编码",
        "item_name": "物料名称",
        "custom_spec_model": "规格型号",
        "description": "说明 (Description)",
        "uom": "单位",
        "quantity_and_rate": "数量、单价与财税金额",
        "qty": "数量",
        "rate": "不含税单价",
        "custom_tax_rate": "税率(%)",
        "custom_gross_rate": "含税单价",
        "amount": "总金额 (未税)",
        "custom_tax_amount": "税额",
        "custom_gross_amount": "价税合计",
        "custom_line_remark": "备注"
    }
    for fn, lbl in label_updates.items():
        if frappe.db.exists("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}):
            frappe.db.set_value("DocField", {"parent": "Purchase Invoice Item", "fieldname": fn}, "label", lbl)
        if frappe.db.exists("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}):
            frappe.db.set_value("Custom Field", {"dt": "Purchase Invoice Item", "fieldname": fn}, "label", lbl)

    # 历史单据回填
    invoices = frappe.get_all("Purchase Invoice", fields=["name"])
    for inv in invoices:
        doc = frappe.get_doc("Purchase Invoice", inv.name)
        if doc.items:
            item_strs = []
            for it in doc.items:
                name = (it.item_name or it.item_code or "").strip()
                if name:
                    qty = flt(it.qty)
                    item_strs.append(f"{name} (x{qty:g})")
            if item_strs:
                summary = "、".join(item_strs[:3]) + (f" 等共{len(item_strs)}项" if len(item_strs) > 3 else "")
                frappe.db.set_value("Purchase Invoice", inv.name, "custom_items_summary", summary, update_modified=False)

    frappe.db.commit()
