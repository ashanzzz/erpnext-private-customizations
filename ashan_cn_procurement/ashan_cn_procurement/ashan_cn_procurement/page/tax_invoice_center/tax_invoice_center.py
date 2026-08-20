# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, flt
from ashan_cn_procurement.services.tax_invoice_matcher import update_tax_invoice_match_state
from ashan_cn_procurement.services.tax_invoice_cleanup import delete_single_tax_invoice_pdf, run_cleanup_now as run_cleanup_service
from ashan_cn_procurement.services.tax_invoice_import import process_import_batch

@frappe.whitelist()
def get_tax_invoices(filters=None, start=0, page_length=50):
	"""
	获取税局发票列表及顶部 4 项 KPI 统计指标
	"""
	if isinstance(filters, str):
		filters = frappe.parse_json(filters) or {}
	filters = filters or {}

	# 1. 统计 KPI 指标 (不受当前状态过滤器影响)
	kpi_conditions = []
	kpi_values = {}

	if filters.get("company"):
		kpi_conditions.append("company = %(company)s")
		kpi_values["company"] = filters["company"]
	if filters.get("from_date"):
		kpi_conditions.append("issue_date >= %(from_date)s")
		kpi_values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		kpi_conditions.append("issue_date <= %(to_date)s")
		kpi_values["to_date"] = filters["to_date"]

	kpi_where = ("WHERE " + " AND ".join(kpi_conditions)) if kpi_conditions else ""

	kpi_query = f"""
		SELECT
			SUM(CASE WHEN business_status = '待录入' THEN 1 ELSE 0 END) AS pending_count,
			SUM(CASE WHEN business_status = '已录入' THEN 1 ELSE 0 END) AS entered_count,
			SUM(CASE WHEN business_status = '已对冲' THEN 1 ELSE 0 END) AS offset_count,
			SUM(CASE WHEN business_status = '已废弃' THEN 1 ELSE 0 END) AS abandoned_count,
			SUM(CASE WHEN parse_status = '需复核' THEN 1 ELSE 0 END) AS review_count,
			COUNT(*) AS total_count
		FROM `tabTax Invoice`
		{kpi_where}
	"""
	kpi_res = frappe.db.sql(kpi_query, kpi_values, as_dict=True)[0]

	# 2. 查询列表数据
	list_conditions = []
	list_values = {"start": cint(start), "page_length": cint(page_length)}

	if filters.get("company"):
		list_conditions.append("company = %(company)s")
		list_values["company"] = filters["company"]
	if filters.get("business_status"):
		list_conditions.append("business_status = %(business_status)s")
		list_values["business_status"] = filters["business_status"]
	if filters.get("parse_status"):
		list_conditions.append("parse_status = %(parse_status)s")
		list_values["parse_status"] = filters["parse_status"]
	if filters.get("from_date"):
		list_conditions.append("issue_date >= %(from_date)s")
		list_values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		list_conditions.append("issue_date <= %(to_date)s")
		list_values["to_date"] = filters["to_date"]
	if filters.get("seller_name"):
		list_conditions.append("seller_name LIKE %(seller_name)s")
		list_values["seller_name"] = f"%{filters['seller_name']}%"
	if filters.get("search_text"):
		list_conditions.append("""
			(invoice_no LIKE %(st)s
			 OR seller_name LIKE %(st)s
			 OR buyer_name LIKE %(st)s
			 OR display_summary LIKE %(st)s
			 OR offset_invoice LIKE %(st)s
			 OR remark LIKE %(st)s)
		""")
		list_values["st"] = f"%{filters['search_text']}%"

	list_where = ("WHERE " + " AND ".join(list_conditions)) if list_conditions else ""

	invoices = frappe.db.sql(f"""
		SELECT
			name, invoice_no, issue_date, invoice_type, company,
			seller_name, seller_tax_id, buyer_name, buyer_tax_id, drawer,
			amount_without_tax, tax_amount, invoice_grand_total,
			vehicle_vessel_tax, late_fee, remark_total, payable_total,
			display_summary, business_status, matched_purchase_invoice,
			purchase_invoice_docstatus, match_status, matched_at,
			is_red_invoice, original_invoice_no, credit_note_no,
			offset_invoice, offset_at, offset_note,
			parse_status, parser_source, parse_confidence, parse_warning,
			invoice_pdf, pdf_removed, pdf_removed_at, pdf_remove_reason,
			abandoned_reason, abandoned_note, abandoned_by, abandoned_at,
			import_batch, original_filename, imported_at, remark
		FROM `tabTax Invoice`
		{list_where}
		ORDER BY issue_date DESC, creation DESC
		LIMIT %(start)s, %(page_length)s
	""", list_values, as_dict=True)

	return {
		"kpis": {
			"pending_count": cint(kpi_res.pending_count or 0),
			"entered_count": cint(kpi_res.entered_count or 0),
			"offset_count": cint(kpi_res.offset_count or 0),
			"abandoned_count": cint(kpi_res.abandoned_count or 0),
			"review_count": cint(kpi_res.review_count or 0),
			"total_count": cint(kpi_res.total_count or 0)
		},
		"invoices": invoices
	}

@frappe.whitelist()
def get_tax_invoice_detail(invoice_no):
	"""获取单张税局发票完整明细与子表"""
	if not frappe.db.exists("Tax Invoice", invoice_no):
		frappe.throw(_("税局发票不存在: {0}").format(invoice_no))

	doc = frappe.get_doc("Tax Invoice", invoice_no)
	return doc.as_dict()

@frappe.whitelist()
def upload_tax_invoice_file():
	"""
	接收发票文件 (PDF 或 ZIP) 上传接口
	创建 Tax Invoice Import Batch 并触发后台 Background Job
	"""
	if "file" not in frappe.request.files:
		frappe.throw(_("未找到上传文件"))

	uploaded_file = frappe.request.files["file"]
	filename = uploaded_file.filename
	content = uploaded_file.read()

	is_zip = filename.lower().endswith(".zip")
	source_type = "ZIP" if is_zip else "PDF"

	# 保存为临时私有 File
	file_doc = frappe.new_doc("File")
	file_doc.file_name = filename
	file_doc.is_private = 1
	file_doc.content = content
	file_doc.save(ignore_permissions=True)

	# 创建批次记录
	batch = frappe.new_doc("Tax Invoice Import Batch")
	batch.source_type = source_type
	batch.source_filename = filename
	batch.uploaded_by = frappe.session.user
	batch.uploaded_at = now_datetime()
	batch.batch_status = "等待处理"
	batch.progress_percent = 0
	batch.current_message = "文件已接收，开始智能解析..."
	batch.temporary_upload_file = file_doc.file_url
	batch.insert(ignore_permissions=True)
	frappe.db.commit()

	# 优先同步极速解析，失败时回退至异步队列
	from ashan_cn_procurement.services.tax_invoice_import import process_import_batch
	res = {}
	try:
		res = process_import_batch(batch.name)
	except Exception as e:
		frappe.log_error(title=f"Tax Invoice Direct Import Error: {filename}")
		try:
			frappe.enqueue(
				"ashan_cn_procurement.services.tax_invoice_import.process_import_batch",
				queue="long",
				batch_name=batch.name,
				timeout=3600
			)
		except Exception:
			pass

	batch.reload()
	is_ok = (batch.batch_status != "失败") and (batch.created_count > 0 or batch.duplicate_count > 0 or batch.review_count > 0)
	return {
		"ok": is_ok,
		"batch_name": batch.name,
		"filename": filename,
		"source_type": source_type,
		"status": batch.batch_status,
		"created_count": batch.created_count or 0,
		"duplicate_count": batch.duplicate_count or 0,
		"review_count": batch.review_count or 0,
		"failed_count": batch.failed_count or 0,
		"current_message": batch.current_message,
		"error_log": batch.error_log or (res.get("error_log") if isinstance(res, dict) else "") or (res.get("error") if isinstance(res, dict) else "")
	}

@frappe.whitelist()
def get_import_batch_status(batch_name):
	"""轮询查询导入批次进度"""
	if not frappe.db.exists("Tax Invoice Import Batch", batch_name):
		frappe.throw(_("批次不存在: {0}").format(batch_name))

	batch = frappe.get_doc("Tax Invoice Import Batch", batch_name)
	return {
		"batch_name": batch.name,
		"status": batch.batch_status,
		"progress_percent": batch.progress_percent,
		"current_message": batch.current_message,
		"file_count": batch.file_count,
		"candidate_count": batch.invoice_candidate_count,
		"parsed_count": batch.parsed_count,
		"created_count": batch.created_count,
		"updated_count": batch.updated_count,
		"duplicate_count": batch.duplicate_count,
		"review_count": batch.review_count,
		"failed_count": batch.failed_count,
		"started_at": batch.started_at,
		"finished_at": batch.finished_at,
		"error_log": batch.error_log
	}

@frappe.whitelist()
def abandon_tax_invoice(invoice_no, reason, note=None):
	"""人工标记发票为【已废弃】"""
	if not frappe.db.exists("Tax Invoice", invoice_no):
		frappe.throw(_("发票不存在: {0}").format(invoice_no))

	doc = frappe.get_doc("Tax Invoice", invoice_no)
	doc.business_status = "已废弃"
	doc.abandoned_reason = reason
	doc.abandoned_note = note
	doc.abandoned_by = frappe.session.user
	doc.abandoned_at = now_datetime()

	# 若存在匹配的 Purchase Invoice，标记为废弃冲突
	if doc.matched_purchase_invoice:
		doc.match_status = "废弃冲突"

	doc.save(ignore_permissions=True)
	return {"ok": True, "invoice_no": invoice_no}

@frappe.whitelist()
def restore_tax_invoice(invoice_no):
	"""将已废弃发票恢复为【待录入】并自动重新匹配"""
	if not frappe.db.exists("Tax Invoice", invoice_no):
		frappe.throw(_("发票不存在: {0}").format(invoice_no))

	doc = frappe.get_doc("Tax Invoice", invoice_no)
	doc.business_status = "待录入"
	doc.abandoned_reason = None
	doc.abandoned_note = None
	doc.abandoned_by = None
	doc.abandoned_at = None
	doc.save(ignore_permissions=True)

	# 立即重新匹配一次
	update_tax_invoice_match_state(doc)
	return {"ok": True, "invoice_no": invoice_no}

@frappe.whitelist()
def rematch_tax_invoice(invoice_no):
	"""手动重新执行 Purchase Invoice 匹配"""
	if not frappe.db.exists("Tax Invoice", invoice_no):
		frappe.throw(_("发票不存在: {0}").format(invoice_no))

	doc = update_tax_invoice_match_state(invoice_no)
	return {"ok": True, "match_status": doc.match_status, "business_status": doc.business_status}

@frappe.whitelist()
def delete_tax_invoice_pdf(invoice_no):
	"""手动清理发票 PDF 原始附件"""
	return delete_single_tax_invoice_pdf(invoice_no, user=frappe.session.user, reason="用户手动清理")

@frappe.whitelist()
def get_recent_batches():
	"""获取最近导入批次记录"""
	return frappe.get_all(
		"Tax Invoice Import Batch",
		fields=[
			"name", "source_type", "source_filename", "uploaded_by", "uploaded_at",
			"batch_status", "progress_percent", "created_count", "duplicate_count",
			"review_count", "failed_count", "current_message"
		],
		order_by="creation DESC",
		limit=20
	)

@frappe.whitelist()
def get_settings():
	"""获取发票设置"""
	settings = frappe.get_single("Tax Invoice Settings")
	return settings.as_dict()

@frappe.whitelist()
def save_settings(settings_data):
	"""保存发票设置"""
	if isinstance(settings_data, str):
		settings_data = frappe.parse_json(settings_data) or {}

	settings = frappe.get_single("Tax Invoice Settings")
	settings.auto_cleanup_enabled = 1 if settings_data.get("auto_cleanup_enabled") else 0
	settings.pdf_retention_days = cint(settings_data.get("pdf_retention_days") or 730)
	settings.cleanup_reference = settings_data.get("cleanup_reference") or "发票日期"
	settings.pdf_parser_enabled = 1 if settings_data.get("pdf_parser_enabled") else 0
	settings.max_files_per_batch = cint(settings_data.get("max_files_per_batch") or 200)

	settings.set("company_mappings", [])
	for m in settings_data.get("company_mappings", []):
		settings.append("company_mappings", {
			"company": m.get("company"),
			"buyer_name": m.get("buyer_name"),
			"buyer_tax_id": m.get("buyer_tax_id")
		})

	settings.save(ignore_permissions=True)
	return {"ok": True}

@frappe.whitelist()
def run_cleanup_now():
	"""立即执行到期附件清理"""
	return run_cleanup_service(user=frappe.session.user)

@frappe.whitelist()
def trigger_red_invoice_reconciliation():
	"""手动触发全量红字发票红冲对冲"""
	from ashan_cn_procurement.services.tax_invoice_matcher import auto_reconcile_all_red_invoices
	return auto_reconcile_all_red_invoices()

@frappe.whitelist()
def unlink_tax_invoice_offset(invoice_no):
	"""手动解除红冲对冲"""
	from ashan_cn_procurement.services.tax_invoice_matcher import unlink_offset_invoices
	return unlink_offset_invoices(invoice_no)
