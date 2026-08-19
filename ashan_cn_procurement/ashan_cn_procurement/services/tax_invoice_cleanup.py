# Copyright (c) 2026, Ashan CN Procurement
import frappe
from frappe.utils import now_datetime, getdate, add_days, today

def delete_single_tax_invoice_pdf(invoice_no, user=None, reason="手动清理"):
	"""
	清理单张税局发票的 PDF 原始附件
	注意：仅删除物理文件与 File 记录，永久保留发票主记录及明细数据
	"""
	if not frappe.db.exists("Tax Invoice", invoice_no):
		return {"ok": False, "error": f"发票 {invoice_no} 不存在"}

	doc = frappe.get_doc("Tax Invoice", invoice_no)
	pdf_url = doc.invoice_pdf

	if not pdf_url and doc.pdf_removed:
		return {"ok": True, "message": "该发票 PDF 已处于清理状态"}

	# 删除关联的 Frappe File 记录
	if pdf_url:
		file_docs = frappe.get_all("File", filters={"file_url": pdf_url}, fields=["name"])
		for f in file_docs:
			try:
				f_doc = frappe.get_doc("File", f.name)
				f_doc.delete(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"删除发票 {invoice_no} PDF File 记录失败: {str(e)}", "Tax Invoice PDF Cleanup")

	# 更新主表字段
	doc.invoice_pdf = None
	doc.pdf_removed = 1
	doc.pdf_removed_at = now_datetime()
	doc.pdf_removed_by = user or frappe.session.user
	doc.pdf_remove_reason = reason
	doc.save(ignore_permissions=True)

	return {"ok": True, "invoice_no": invoice_no}

def cleanup_expired_tax_invoice_pdfs():
	"""
	每日定时任务：自动清理超过保留期限的税局发票 PDF 附件
	默认保留 730 天（约 2 年）
	"""
	settings = frappe.get_single("Tax Invoice Settings")
	if not settings.auto_cleanup_enabled:
		return {"ok": True, "message": "自动清理未开启"}

	retention_days = int(settings.pdf_retention_days or 730)
	ref_field = settings.cleanup_reference or "发票日期"
	current_date = getdate(today())

	# 查询带有 PDF 附件且尚未清理的发票
	tax_invs = frappe.get_all(
		"Tax Invoice",
		filters={
			"pdf_removed": 0,
			"invoice_pdf": ["is", "set"]
		},
		fields=["name", "invoice_no", "issue_date", "creation"]
	)

	cleaned_count = 0
	for ti in tax_invs:
		if ref_field == "发票日期" and ti.issue_date:
			base_date = getdate(ti.issue_date)
		else:
			base_date = getdate(ti.creation)

		expiry_date = add_days(base_date, retention_days)
		if current_date >= expiry_date:
			res = delete_single_tax_invoice_pdf(ti.invoice_no, user="Administrator", reason="自动保留期限到期")
			if res.get("ok"):
				cleaned_count += 1

	return {"ok": True, "cleaned_count": cleaned_count}

def run_cleanup_now(user=None):
	"""管理员手动立即执行一次到期清理"""
	return cleanup_expired_tax_invoice_pdfs()
