# Copyright (c) 2026, Ashan CN Procurement
import io
import re
import pypdf
from ashan_cn_procurement.parser.common import (
	normalize_invoice_no,
	calculate_sha256,
	clean_decimal,
	clean_date_str,
	parse_remark_vehicle_vessel_tax
)

def parse_tax_invoice_pdf(pdf_bytes, filename=""):
	"""
	解析税局发票 PDF 字节数据，提取结构化数据并返回字典
	用于降级解析（在缺少 XML 时使用）
	支持数电发票标准版式及通用发票版式
	"""
	sha256_hash = calculate_sha256(pdf_bytes)
	pdf_size = len(pdf_bytes)

	# 1. 尝试从文件名提取发票号提示
	filename_hint_inv = ""
	if filename:
		m_fn = re.search(r'dzfp_(\d+)_', filename)
		if m_fn:
			filename_hint_inv = m_fn.group(1)

	# 2. 读取 PDF 文本
	text_pages = []
	try:
		reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
		for p in reader.pages:
			t = p.extract_text() or ""
			text_pages.append(t)
	except Exception as e:
		return {
			"ok": False,
			"error": f"PDF 文件无法读取: {str(e)}",
			"sha256": sha256_hash,
			"pdf_size": pdf_size
		}

	full_text = "\n".join(text_pages)
	if not full_text.strip():
		return {
			"ok": True,
			"invoice_no": filename_hint_inv or "UNKNOWN",
			"parse_status": "需复核",
			"parser_source": "PDF",
			"parse_confidence": "低",
			"parse_warning": "PDF 无可提取的文本层 (可能是纯图片/扫描件)",
			"sha256": sha256_hash,
			"pdf_size": pdf_size,
			"items": []
		}

	warnings = []

	# 3. 发票类型
	invoice_type = "电子发票"
	if "增值税专用发票" in full_text:
		invoice_type = "电子发票（增值税专用发票）"
	elif "普通发票" in full_text:
		invoice_type = "电子发票（普通发票）"

	# 4. 数电发票专属连续数据块解析
	# 数电发票文本特征：发票号(20位)、日期(YYYY年MM月DD日)、购买方名、购方税号、销方名、销方税号、金额、价税合计、开票人
	inv_no = ""
	issue_date = None
	buyer_name, buyer_tax_id = "", ""
	seller_name, seller_tax_id = "", ""
	amt_without_tax = 0.0
	tax_amt = 0.0
	grand_tot = 0.0
	drawer = ""

	lines = [line.strip() for line in full_text.splitlines() if line.strip()]

	# 扫描 20 位发票号码行
	inv_idx = -1
	for idx, line in enumerate(lines):
		if re.match(r'^\d{20}$', line):
			inv_no = line
			inv_idx = idx
			break

	if inv_idx != -1 and inv_idx + 1 < len(lines):
		# 数电发票典型行序列
		# line 1: 日期
		m_d = re.match(r'^(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{2}-\d{2})', lines[inv_idx + 1])
		if m_d:
			issue_date = clean_date_str(m_d.group(1))

		# 寻找后续的税号与名称
		for off in range(2, min(15, len(lines) - inv_idx)):
			curr = lines[inv_idx + off]
			# 统一信用代码
			if re.match(r'^[0-9A-Za-z]{15,20}$', curr):
				if not buyer_tax_id:
					buyer_tax_id = curr
					if inv_idx + off - 1 >= 0 and not buyer_name:
						buyer_name = lines[inv_idx + off - 1]
				elif not seller_tax_id and curr != buyer_tax_id:
					seller_tax_id = curr
					if inv_idx + off - 1 >= 0 and not seller_name:
						seller_name = lines[inv_idx + off - 1]
			# 金额合计行 (如 ¥ 25633.63 ¥ 3332.37 或 ¥ 817.00)
			elif '¥' in curr or '￥' in curr:
				amts = re.findall(r'[0-9.,-]+', curr)
				if len(amts) == 2:
					amt_without_tax = clean_decimal(amts[0])
					tax_amt = clean_decimal(amts[1])
				elif len(amts) == 1:
					if grand_tot == 0.0:
						grand_tot = clean_decimal(amts[0])

	# 兜底正则提取
	if not inv_no:
		m_inv = re.search(r'发\s*票\s*号\s*码\s*[:：]?\s*([0-9]{10,25})', full_text)
		if m_inv:
			inv_no = m_inv.group(1)
		elif filename_hint_inv:
			inv_no = filename_hint_inv
		else:
			m_num = re.search(r'(?<!\d)(\d{20})(?!\d)', full_text)
			if m_num:
				inv_no = m_num.group(1)

	inv_no = normalize_invoice_no(inv_no)

	if not issue_date:
		m_date = re.search(r'开\s*票\s*日\s*期\s*[:：]?\s*([0-9]{4}\s*年\s*[0-9]{1,2}\s*月\s*[0-9]{1,2}\s*日|[0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2})', full_text)
		if m_date:
			issue_date = clean_date_str(m_date.group(1))

	# 兜底购买方/销售方
	if not buyer_tax_id or not seller_tax_id:
		tax_ids = re.findall(r'(?:统一社会信用代码|纳税人识别号)\s*[:：/]?\s*([0-9A-Za-z]{15,20})', full_text)
		if len(tax_ids) >= 2:
			buyer_tax_id = buyer_tax_id or tax_ids[0].strip()
			seller_tax_id = seller_tax_id or tax_ids[1].strip()
		elif len(tax_ids) == 1:
			buyer_tax_id = buyer_tax_id or tax_ids[0].strip()

	# 价税合计 (小写)
	if grand_tot == 0.0:
		m_gt = re.search(r'(?:价税合计|小写)\s*[（(]?[^）)]*[）)]?\s*[¥￥]?\s*([0-9.,-]+)', full_text)
		if m_gt:
			grand_tot = clean_decimal(m_gt.group(1))

	# 若只有不含税和税额，则价税合计 = 不含税 + 税额
	if grand_tot == 0.0 and (amt_without_tax != 0.0 or tax_amt != 0.0):
		grand_tot = round(amt_without_tax + tax_amt, 2)
	elif amt_without_tax == 0.0 and tax_amt == 0.0 and grand_tot != 0.0:
		# 不征税发票
		amt_without_tax = grand_tot
		tax_amt = 0.0

	# 5. 开票人与备注
	m_dr = re.search(r'开\s*票\s*人\s*[:：]\s*([^\s\n\r]+)', full_text)
	if m_dr:
		drawer = m_dr.group(1)

	remark = ""
	m_rem = re.search(r'备\s*注\s*[:：]?\s*([\s\S]*?)(?:开\s*票\s*人|$)', full_text)
	if m_rem:
		remark = m_rem.group(1).strip()

	remark_data = parse_remark_vehicle_vessel_tax(remark or full_text)
	vehicle_vessel_tax = remark_data["vehicle_vessel_tax"]
	late_fee = remark_data["late_fee"]
	remark_total = remark_data["remark_total"]

	if remark_total > 0:
		payable_total = remark_total
	else:
		payable_total = round(grand_tot + vehicle_vessel_tax + late_fee, 2)

	# 6. 红字发票
	is_red = (grand_tot < 0 or amt_without_tax < 0 or "红字" in full_text)

	# 7. 明细项提取
	items = []
	is_toll = "通行日期" in full_text or "车牌号" in full_text and ("客车" in full_text or "货车" in full_text)

	if vehicle_vessel_tax > 0 or "保费" in full_text or "保险" in full_text:
		items.append({
			"line_type": "普通",
			"item_name": "*金融服务*保费" if "保费" in full_text else "保险服务费",
			"spec_model": None,
			"unit": "次",
			"quantity": 1.0,
			"unit_price": amt_without_tax or grand_tot,
			"amount": amt_without_tax,
			"tax_rate_text": "6%" if abs(tax_amt - round(amt_without_tax * 0.06, 2)) < 0.1 else "",
			"tax_amount": tax_amt,
			"vehicle_vessel_tax": 0.0,
			"late_fee": 0.0,
			"line_total": grand_tot,
			"plate_number": remark_data.get("plate_number"),
			"vehicle_type": None,
			"passage_start": None,
			"passage_end": None,
			"source_note": None
		})
		if vehicle_vessel_tax > 0 or late_fee > 0:
			items.append({
				"line_type": "车船税",
				"item_name": "代收车船税",
				"spec_model": remark_data.get("tax_period"),
				"unit": "辆",
				"quantity": 1.0,
				"unit_price": vehicle_vessel_tax + late_fee,
				"amount": 0.0,
				"tax_rate_text": "不征税",
				"tax_amount": 0.0,
				"vehicle_vessel_tax": vehicle_vessel_tax,
				"late_fee": late_fee,
				"line_total": round(vehicle_vessel_tax + late_fee, 2),
				"plate_number": remark_data.get("plate_number"),
				"vehicle_type": None,
				"passage_start": None,
				"passage_end": None,
				"source_note": f"所属期: {remark_data.get('tax_period') or '—'}"
			})
	elif is_toll:
		plate_toll = remark_data.get("plate_number")
		if not plate_toll:
			m_p = re.search(r'([津京冀沪粤鲁豫苏浙皖黑吉辽蒙晋陕甘宁青新鄂湘赣闽川黔滇渝藏桂琼][A-Z0-9]{5,7})', full_text)
			if m_p:
				plate_toll = m_p.group(1)

		items.append({
			"line_type": "通行费",
			"item_name": "*通行费*通行费",
			"spec_model": None,
			"unit": "次",
			"quantity": None,
			"unit_price": None,
			"amount": amt_without_tax,
			"tax_rate_text": "不征税" if tax_amt == 0 else "",
			"tax_amount": tax_amt,
			"vehicle_vessel_tax": 0.0,
			"late_fee": 0.0,
			"line_total": grand_tot,
			"plate_number": plate_toll,
			"vehicle_type": "客车" if "客车" in full_text else ("货车" if "货车" in full_text else None),
			"passage_start": None,
			"passage_end": None,
			"source_note": None
		})
	else:
		# 提取所有 *...* 项目
		raw_items = re.findall(r'(\*[^*]+\*[^\s\n\r]+)', full_text)
		if raw_items:
			for r_it in raw_items:
				items.append({
					"line_type": "普通",
					"item_name": r_it,
					"spec_model": None,
					"unit": None,
					"quantity": None,
					"unit_price": None,
					"amount": amt_without_tax / len(raw_items) if amt_without_tax else 0.0,
					"tax_rate_text": "",
					"tax_amount": tax_amt / len(raw_items) if tax_amt else 0.0,
					"vehicle_vessel_tax": 0.0,
					"late_fee": 0.0,
					"line_total": grand_tot / len(raw_items) if grand_tot else 0.0,
					"plate_number": None,
					"vehicle_type": None,
					"passage_start": None,
					"passage_end": None,
					"source_note": None
				})
		else:
			items.append({
				"line_type": "普通",
				"item_name": "发票项目明细",
				"spec_model": None,
				"unit": None,
				"quantity": None,
				"unit_price": None,
				"amount": amt_without_tax,
				"tax_rate_text": "",
				"tax_amount": tax_amt,
				"vehicle_vessel_tax": 0.0,
				"late_fee": 0.0,
				"line_total": grand_tot,
				"plate_number": None,
				"vehicle_type": None,
				"passage_start": None,
				"passage_end": None,
				"source_note": None
			})

	# 8. 置信度评估
	confidence = "高"
	parse_status = "已解析"

	if not inv_no or not issue_date or grand_tot == 0.0:
		confidence = "低"
		parse_status = "需复核"
		warnings.append("关键字段 (发票号/日期/价税合计) 提取不完整")
	elif abs((amt_without_tax + tax_amt) - grand_tot) > 0.05:
		confidence = "中"
		warnings.append("金额自校验存在微小差异")

	return {
		"ok": True,
		"invoice_no": inv_no or filename_hint_inv or "UNKNOWN",
		"issue_date": issue_date,
		"invoice_type": invoice_type,
		"seller_name": seller_name,
		"seller_tax_id": seller_tax_id,
		"buyer_name": buyer_name,
		"buyer_tax_id": buyer_tax_id,
		"amount_without_tax": amt_without_tax,
		"tax_amount": tax_amt,
		"invoice_grand_total": grand_tot,
		"vehicle_vessel_tax": vehicle_vessel_tax,
		"late_fee": late_fee,
		"remark_total": remark_total,
		"payable_total": payable_total,
		"drawer": drawer,
		"remark": remark,
		"is_red_invoice": 1 if is_red else 0,
		"original_invoice_no": None,
		"credit_note_no": None,
		"items": items,
		"parse_status": parse_status,
		"parser_source": "PDF",
		"parser_version": "1.0.0",
		"parse_confidence": confidence,
		"parse_warning": "; ".join(warnings) if warnings else "",
		"source_xml_sha256": None,
		"pdf_sha256": sha256_hash,
		"pdf_size": pdf_size
	}
