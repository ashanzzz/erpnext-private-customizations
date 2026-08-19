# Copyright (c) 2026, Ashan CN Procurement
import frappe
from frappe.utils import now_datetime
from ashan_cn_procurement.parser.common import normalize_invoice_no

def get_matching_purchase_invoices(invoice_nos):
	"""
	批量根据发票号码查询有效的 Purchase Invoice (docstatus < 2)
	返回映射: { normalized_bill_no: [pi_dict, ...] }
	"""
	if not invoice_nos:
		return {}

	clean_nos = [normalize_invoice_no(n) for n in invoice_nos if n]
	if not clean_nos:
		return {}

	# 批量查询 Purchase Invoice
	pis = frappe.db.sql("""
		SELECT name, bill_no, docstatus, supplier, company, grand_total, posting_date
		FROM `tabPurchase Invoice`
		WHERE docstatus < 2
		  AND bill_no IN %(bill_nos)s
	""", {"bill_nos": tuple(clean_nos)}, as_dict=True)

	by_bill_no = {}
	for pi in pis:
		b_no = normalize_invoice_no(pi.get("bill_no"))
		if b_no:
			by_bill_no.setdefault(b_no, []).append(pi)

	return by_bill_no

def update_tax_invoice_match_state(tax_inv_name_or_doc, matched_pis=None):
	"""
	根据匹配的 Purchase Invoice 列表更新 Tax Invoice 的业务状态与匹配状态
	遵循【人工已废弃保护原则】
	"""
	if isinstance(tax_inv_name_or_doc, str):
		if not frappe.db.exists("Tax Invoice", tax_inv_name_or_doc):
			return None
		doc = frappe.get_doc("Tax Invoice", tax_inv_name_or_doc)
	else:
		doc = tax_inv_name_or_doc

	inv_no = normalize_invoice_no(doc.invoice_no)
	if matched_pis is None:
		pis = frappe.db.sql("""
			SELECT name, bill_no, docstatus, supplier, company, grand_total, posting_date
			FROM `tabPurchase Invoice`
			WHERE docstatus < 2 AND bill_no = %s
		""", (inv_no,), as_dict=True)
	else:
		pis = matched_pis

	is_abandoned = (doc.business_status == "已废弃")

	if not pis:
		# 无匹配 Purchase Invoice
		doc.matched_purchase_invoice = None
		doc.purchase_invoice_docstatus = None
		doc.match_status = "未匹配"
		if not is_abandoned:
			doc.business_status = "待录入"
	elif len(pis) == 1:
		# 单一匹配
		pi = pis[0]
		doc.matched_purchase_invoice = pi.get("name")
		doc.purchase_invoice_docstatus = "已提交" if pi.get("docstatus") == 1 else "草稿"
		doc.matched_at = now_datetime()

		if is_abandoned:
			# 废弃冲突：人工已废弃记录发生匹配，状态保持已废弃，匹配状态标为废弃冲突
			doc.match_status = "废弃冲突"
		else:
			doc.business_status = "已录入"
			doc.match_status = "单一匹配"
	else:
		# 多重匹配
		pi = pis[0]
		doc.matched_purchase_invoice = pi.get("name")
		doc.purchase_invoice_docstatus = "已提交" if pi.get("docstatus") == 1 else "草稿"
		doc.matched_at = now_datetime()

		if is_abandoned:
			doc.match_status = "废弃冲突"
		else:
			doc.business_status = "已录入"
			doc.match_status = "多重匹配"

	if hasattr(doc, "save") and not doc.flags.in_insert:
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)

	return doc

def on_purchase_invoice_change(doc, method=None):
	"""
	Purchase Invoice Hook: after_insert, on_update, on_update_after_submit, on_cancel
	实时触发税局发票状态刷新
	"""
	bill_no = normalize_invoice_no(doc.get("bill_no"))
	old_bill_no = None

	if hasattr(doc, "get_doc_before_save"):
		old_doc = doc.get_doc_before_save()
		if old_doc:
			old_bill_no = normalize_invoice_no(old_doc.get("bill_no"))

	affected_nos = set(filter(None, [bill_no, old_bill_no]))
	for b_no in affected_nos:
		tax_invs = frappe.get_all("Tax Invoice", filters={"invoice_no": b_no}, fields=["name"])
		for ti in tax_invs:
			update_tax_invoice_match_state(ti.name)

def on_purchase_invoice_delete(doc, method=None):
	"""Purchase Invoice on_trash Hook"""
	bill_no = normalize_invoice_no(doc.get("bill_no"))
	if bill_no:
		tax_invs = frappe.get_all("Tax Invoice", filters={"invoice_no": bill_no}, fields=["name"])
		for ti in tax_invs:
			update_tax_invoice_match_state(ti.name)

def reconcile_tax_invoice_matches():
	"""
	每日调度兜底：全量核对税局发票与 Purchase Invoice 的匹配状态
	"""
	tax_invs = frappe.get_all("Tax Invoice", fields=["name", "invoice_no", "business_status", "matched_purchase_invoice", "match_status"])
	if not tax_invs:
		return

	inv_nos = [t.invoice_no for t in tax_invs if t.invoice_no]
	matched_map = get_matching_purchase_invoices(inv_nos)

	for ti in tax_invs:
		inv_no = normalize_invoice_no(ti.invoice_no)
		pis = matched_map.get(inv_no, [])
		update_tax_invoice_match_state(ti.name, matched_pis=pis)
