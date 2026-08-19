# Copyright (c) 2026, Ashan CN Procurement
import os
import io
import re
import zipfile
import traceback
import frappe
from ashan_cn_procurement.parser.common import normalize_invoice_no, calculate_sha256
from ashan_cn_procurement.parser.xml_parser import parse_tax_invoice_xml
from ashan_cn_procurement.parser.pdf_parser import parse_tax_invoice_pdf
from ashan_cn_procurement.services.tax_invoice_matcher import get_matching_purchase_invoices, update_tax_invoice_match_state

def identify_company(buyer_name, buyer_tax_id):
	"""
	根据购买方名称与税号识别所属公司
	优先匹配 Tax Invoice Settings 中的 Company Mappings，其次匹配 tabCompany
	"""
	settings = frappe.get_single("Tax Invoice Settings")
	mappings = settings.get("company_mappings") or []

	# 1. 规则表精确税号匹配
	if buyer_tax_id:
		for m in mappings:
			if m.buyer_tax_id and m.buyer_tax_id.strip() == buyer_tax_id.strip():
				return m.company

	# 2. 规则表名称包含匹配
	if buyer_name:
		for m in mappings:
			if m.buyer_name and m.buyer_name.strip() in buyer_name.strip():
				return m.company

	# 3. 系统 Company 档案税号与名称匹配
	if buyer_tax_id:
		c = frappe.db.get_value("Company", {"tax_id": buyer_tax_id}, "name")
		if c:
			return c

	if buyer_name:
		c = frappe.db.get_value("Company", {"company_name": buyer_name}, "name")
		if c:
			return c
		# 模糊前缀匹配
		comps = frappe.get_all("Company", fields=["name", "company_name"])
		for comp in comps:
			c_name = comp.company_name or comp.name
			if c_name in buyer_name or buyer_name in c_name:
				return comp.name

	return None

def save_private_pdf_file(pdf_bytes, filename, docname):
	"""
	将发票 PDF 字节内容保存为 Frappe Private File 并绑定到 Tax Invoice
	绝对不保存 XML，仅长期保留 PDF
	"""
	if not pdf_bytes or not filename:
		return None

	# 确保文件名安全
	safe_filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
	if not safe_filename.lower().endswith(".pdf"):
		safe_filename += ".pdf"

	file_doc = frappe.new_doc("File")
	file_doc.file_name = safe_filename
	file_doc.is_private = 1
	file_doc.attached_to_doctype = "Tax Invoice"
	file_doc.attached_to_name = docname
	file_doc.attached_to_field = "invoice_pdf"
	file_doc.content = pdf_bytes
	file_doc.save(ignore_permissions=True)

	return file_doc.file_url

def process_import_batch(batch_name):
	"""
	Background Job 异步处理税局发票导入批次
	"""
	if not frappe.db.exists("Tax Invoice Import Batch", batch_name):
		return

	batch = frappe.get_doc("Tax Invoice Import Batch", batch_name)
	batch.batch_status = "处理中"
	batch.started_at = now_datetime()
	batch.progress_percent = 5
	batch.current_message = "正在读取上传文件..."
	batch.save(ignore_permissions=True)
	frappe.db.commit()

	temp_file_url = batch.temporary_upload_file
	error_logs = []
	created_nos = []
	updated_nos = []

	try:
		# 1. 读取临时上传文件
		if not temp_file_url:
			raise ValueError("未找到临时上传文件")

		file_doc_name = frappe.db.get_value("File", {"file_url": temp_file_url}, "name")
		if not file_doc_name:
			raise ValueError(f"File 记录不存在: {temp_file_url}")

		file_doc = frappe.get_doc("File", file_doc_name)
		file_content = file_doc.get_content()

		is_zip = (batch.source_type == "ZIP" or batch.source_filename.lower().endswith(".zip"))

		# 2. 组织待解析的发票数据包
		# { invoice_no_or_key: { "xml": bytes, "pdf": (bytes, filename), "fn_hint": str } }
		invoices_map = {}

		if is_zip:
			batch.current_message = "正在解压并分析 ZIP 结构..."
			batch.save(ignore_permissions=True)
			frappe.db.commit()

			with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
				namelist = zf.namelist()
				batch.file_count = len(namelist)

				for entry_name in namelist:
					# 忽略目录与隐藏文件
					if entry_name.endswith('/') or '__MACOSX' in entry_name or entry_name.startswith('.'):
						continue
					basename = os.path.basename(entry_name)
					# 忽略汇总文件与非单票发票
					if basename in ["合并发票.pdf", "全量发票查询导出结果.xlsx"] or basename.endswith(".xlsx") or basename.endswith(".xls"):
						continue

					m_fn = re.search(r'dzfp_(\d+)_', basename)
					inv_hint = m_fn.group(1) if m_fn else os.path.splitext(basename)[0]

					if inv_hint not in invoices_map:
						invoices_map[inv_hint] = {"xml": None, "pdf": None, "fn_hint": inv_hint}

					entry_bytes = zf.read(entry_name)
					if basename.lower().endswith(".xml"):
						invoices_map[inv_hint]["xml"] = entry_bytes
					elif basename.lower().endswith(".pdf"):
						invoices_map[inv_hint]["pdf"] = (entry_bytes, basename)
		else:
			# 单个或直接上传的 PDF
			batch.file_count = 1
			inv_hint = os.path.splitext(batch.source_filename)[0]
			m_fn = re.search(r'dzfp_(\d+)_', batch.source_filename)
			if m_fn:
				inv_hint = m_fn.group(1)
			invoices_map[inv_hint] = {"xml": None, "pdf": (file_content, batch.source_filename), "fn_hint": inv_hint}

		batch.invoice_candidate_count = len(invoices_map)
		batch.progress_percent = 15
		batch.current_message = f"识别出 {len(invoices_map)} 份待处理发票，开始逐票解析..."
		batch.save(ignore_permissions=True)
		frappe.db.commit()

		# 3. 逐张发票解析入库
		total_candidates = len(invoices_map)
		processed_idx = 0

		for key, bundle in invoices_map.items():
			processed_idx += 1
			xml_bytes = bundle.get("xml")
			pdf_tuple = bundle.get("pdf")
			pdf_bytes = pdf_tuple[0] if pdf_tuple else None
			pdf_filename = pdf_tuple[1] if pdf_tuple else ""

			# 更新进度
			progress = int(15 + (processed_idx / max(1, total_candidates)) * 75)
			batch.progress_percent = progress
			batch.current_message = f"正在解析发票 ({processed_idx}/{total_candidates}): {key}..."
			if processed_idx % 5 == 0 or processed_idx == total_candidates:
				batch.save(ignore_permissions=True)
				frappe.db.commit()

			try:
				parsed_data = None
				# 优先 XML 解析数据
				if xml_bytes:
					parsed_data = parse_tax_invoice_xml(xml_bytes, filename=pdf_filename)
					if not parsed_data.get("ok"):
						# XML 失败则尝试降级为 PDF
						if pdf_bytes:
							parsed_data = parse_tax_invoice_pdf(pdf_bytes, filename=pdf_filename)
						else:
							batch.failed_count += 1
							error_logs.append(f"发票 {key} XML 解析失败: {parsed_data.get('error')}")
							continue
				elif pdf_bytes:
					# 仅有 PDF
					parsed_data = parse_tax_invoice_pdf(pdf_bytes, filename=pdf_filename)
					if not parsed_data.get("ok"):
						batch.failed_count += 1
						error_logs.append(f"发票 {key} PDF 解析失败: {parsed_data.get('error')}")
						continue
				else:
					# 既无有效 XML 也无 PDF
					continue

				inv_no = normalize_invoice_no(parsed_data.get("invoice_no") or key)
				if not inv_no or inv_no == "UNKNOWN":
					batch.failed_count += 1
					error_logs.append(f"文件 {pdf_filename} 无法提取有效发票号码")
					continue

				batch.parsed_count += 1

				# 识别所属公司
				comp = identify_company(parsed_data.get("buyer_name"), parsed_data.get("buyer_tax_id"))
				if not comp:
					if parsed_data.get("parse_status") == "已解析":
						parsed_data["parse_status"] = "需复核"
					parsed_data["parse_warning"] = (parsed_data.get("parse_warning") or "") + "; 购买方公司未能自动匹配"

				# 4. 去重与更新检查
				if frappe.db.exists("Tax Invoice", inv_no):
					existing_doc = frappe.get_doc("Tax Invoice", inv_no)
					# 检查关键金额与日期是否一致
					is_same_amount = (
						abs(flt(existing_doc.invoice_grand_total) - flt(parsed_data.get("invoice_grand_total"))) < 0.05 and
						abs(flt(existing_doc.amount_without_tax) - flt(parsed_data.get("amount_without_tax"))) < 0.05
					)

					if is_same_amount:
						# 金额一致：若原记录无 PDF 则补挂 PDF
						if (not existing_doc.invoice_pdf or existing_doc.pdf_removed) and pdf_bytes:
							new_url = save_private_pdf_file(pdf_bytes, pdf_filename, existing_doc.name)
							existing_doc.invoice_pdf = new_url
							existing_doc.pdf_sha256 = calculate_sha256(pdf_bytes)
							existing_doc.pdf_size = len(pdf_bytes)
							existing_doc.pdf_removed = 0
							existing_doc.save(ignore_permissions=True)
							batch.updated_count += 1
							updated_nos.append(inv_no)
						else:
							batch.duplicate_count += 1
					else:
						# 金额冲突：标记需复核
						existing_doc.parse_status = "需复核"
						existing_doc.parse_warning = (existing_doc.parse_warning or "") + "; 重复导入且关键金额数据与已有记录冲突"
						existing_doc.save(ignore_permissions=True)
						batch.review_count += 1
					continue

				# 5. 创建新 Tax Invoice 记录
				doc = frappe.new_doc("Tax Invoice")
				doc.invoice_no = inv_no
				doc.issue_date = parsed_data.get("issue_date")
				doc.invoice_type = parsed_data.get("invoice_type")
				doc.company = comp
				doc.seller_name = parsed_data.get("seller_name")
				doc.seller_tax_id = parsed_data.get("seller_tax_id")
				doc.buyer_name = parsed_data.get("buyer_name")
				doc.buyer_tax_id = parsed_data.get("buyer_tax_id")
				doc.drawer = parsed_data.get("drawer")
				doc.amount_without_tax = parsed_data.get("amount_without_tax")
				doc.tax_amount = parsed_data.get("tax_amount")
				doc.invoice_grand_total = parsed_data.get("invoice_grand_total")
				doc.vehicle_vessel_tax = parsed_data.get("vehicle_vessel_tax") or 0.0
				doc.late_fee = parsed_data.get("late_fee") or 0.0
				doc.remark_total = parsed_data.get("remark_total") or 0.0
				doc.payable_total = parsed_data.get("payable_total")
				doc.remark = parsed_data.get("remark")
				doc.is_red_invoice = parsed_data.get("is_red_invoice") or 0
				doc.original_invoice_no = parsed_data.get("original_invoice_no")
				doc.credit_note_no = parsed_data.get("credit_note_no")
				doc.parse_status = parsed_data.get("parse_status") or "已解析"
				doc.parser_source = parsed_data.get("parser_source")
				doc.parser_version = parsed_data.get("parser_version")
				doc.parse_confidence = parsed_data.get("parse_confidence")
				doc.parse_warning = parsed_data.get("parse_warning")
				doc.source_xml_sha256 = parsed_data.get("source_xml_sha256")
				doc.import_batch = batch.name
				doc.original_filename = pdf_filename or batch.source_filename
				doc.imported_at = now_datetime()
				doc.imported_by = batch.uploaded_by
				doc.business_status = "待录入"
				doc.match_status = "未匹配"

				# 明细项
				for it in (parsed_data.get("items") or []):
					doc.append("items", it)

				# 插入主记录
				doc.insert(ignore_permissions=True)

				# 挂载 Private PDF 附件 (长期保留，XML 丢弃)
				if pdf_bytes:
					pdf_url = save_private_pdf_file(pdf_bytes, pdf_filename, doc.name)
					doc.invoice_pdf = pdf_url
					doc.pdf_sha256 = calculate_sha256(pdf_bytes)
					doc.pdf_size = len(pdf_bytes)
					doc.save(ignore_permissions=True)
				else:
					doc.parse_status = "需复核"
					doc.parse_warning = (doc.parse_warning or "") + "; 缺少原始 PDF 附件"
					doc.save(ignore_permissions=True)

				batch.created_count += 1
				created_nos.append(inv_no)
				if doc.parse_status == "需复核":
					batch.review_count += 1

			except Exception as e_row:
				batch.failed_count += 1
				err_msg = f"发票 {key} 处理异常: {str(e_row)}\n{traceback.format_exc()}"
				error_logs.append(err_msg)
				frappe.log_error(err_msg, "Tax Invoice Single Process")

		# 6. 集中批量匹配 Purchase Invoice
		batch.current_message = "正在进行采购发票批量自动匹配..."
		batch.progress_percent = 95
		batch.save(ignore_permissions=True)
		frappe.db.commit()

		all_touched_nos = set(created_nos + updated_nos)
		if all_touched_nos:
			matched_map = get_matching_purchase_invoices(list(all_touched_nos))
			for inv_n in all_touched_nos:
				pis = matched_map.get(inv_n, [])
				update_tax_invoice_match_state(inv_n, matched_pis=pis)

		# 7. 删除临时上传文件 (ZIP / 临时包)
		batch.current_message = "正在清理临时上传文件..."
		try:
			if file_doc_name and frappe.db.exists("File", file_doc_name):
				f_doc = frappe.get_doc("File", file_doc_name)
				f_doc.delete(ignore_permissions=True)
			batch.temporary_upload_file = None
		except Exception as e_del:
			frappe.log_error(f"清理临时上传文件失败: {str(e_del)}", "Tax Invoice Cleanup Temp File")

		# 8. 批次收尾
		batch.batch_status = "已完成" if batch.failed_count == 0 else "部分失败"
		batch.finished_at = now_datetime()
		batch.progress_percent = 100
		batch.current_message = f"导入完成！新增: {batch.created_count}, 略过重复: {batch.duplicate_count}, 需复核: {batch.review_count}, 失败: {batch.failed_count}"
		if error_logs:
			batch.error_log = "\n---\n".join(error_logs)
		batch.save(ignore_permissions=True)
		frappe.db.commit()

	except Exception as e_batch:
		frappe.db.rollback()
		batch.batch_status = "失败"
		batch.finished_at = now_datetime()
		batch.current_message = f"批次处理失败: {str(e_batch)}"
		batch.error_log = traceback.format_exc()
		batch.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.log_error(batch.error_log, "Tax Invoice Batch Import")
