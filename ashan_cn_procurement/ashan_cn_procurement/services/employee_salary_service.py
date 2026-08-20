# Copyright (c) 2026, Ashan CN Procurement
import json
import frappe
from frappe.utils import flt, cint, getdate, today
import math
from datetime import datetime, date

def calculate_age_and_retirement_details(id_card="", birth_date_str=None, gender=None, job_title="操作工", original_retirement_age=None, ref_period_month=None):
	"""
	国家法定标准渐进式延迟法定退休年龄计算器 (2024年9月13日全国人大常委会决定 & Excel法定核心公式)
	1. 当前年龄：严格截止到当前发薪账期本月1日 (例如 2026-07 对应 2026-07-01 的实岁)
	2. 原退休年龄 (男60, 女干部55, 女工人50) 及其具体退休日期与剩余退休月数
	3. 渐进式延迟退休年龄及其具体退休日期与剩余退休月数
	"""
	id_card = str(id_card or "").strip().upper()
	is_valid_id = False
	birth_d = None
	derived_gender = gender

	# 1. 18位中国身份证智能提取出生日期与性别
	if len(id_card) == 18 and (id_card[:17].isdigit()) and (id_card[17].isdigit() or id_card[17] == 'X'):
		try:
			b_str = id_card[6:14]
			birth_d = datetime.strptime(b_str, "%Y%m%d").date()
			is_valid_id = True
			derived_gender = "男" if int(id_card[16]) % 2 != 0 else "女"
		except Exception:
			is_valid_id = False

	# 若未识别身份证但提供了出生日期
	if not birth_d and birth_date_str:
		try:
			birth_d = datetime.strptime(str(birth_date_str).strip()[:10], "%Y-%m-%d").date()
		except Exception:
			birth_d = None

	# 2. 解析基准账期 (默认 2026-07)
	ref_pm = str(ref_period_month or "2026-07").strip()
	if "-" in ref_pm:
		parts = ref_pm.split("-")
		ref_y = int(parts[0])
		ref_m = int(parts[1])
	else:
		ref_y = 2026
		ref_m = 7

	# 计算截止本月1日的当前实岁年龄
	current_age = 0
	current_age_months = 0
	if birth_d:
		total_m_age = (ref_y - birth_d.year) * 12 + (ref_m - birth_d.month)
		if total_m_age < 0:
			total_m_age = 0
		current_age = total_m_age // 12
		current_age_months = total_m_age % 12

	# 3. 确定原法定退休年龄 (男 60 岁，女干部 55 岁，女工人 50 岁)
	orig_val = flt(original_retirement_age) if original_retirement_age is not None else 0.0
	if orig_val <= 0:
		orig_val = None

	if derived_gender == "女":
		management_keywords = ["管理", "经理", "主管", "技术", "财务", "会计", "人事", "总监", "主任", "工程"]
		is_cadre = any(k in str(job_title) for k in management_keywords)
		default_female_retire = 55.0 if is_cadre else 50.0
		if orig_val and orig_val not in [60.0]:
			original_retire = orig_val
		else:
			original_retire = default_female_retire
	else:
		if orig_val:
			original_retire = orig_val
		else:
			original_retire = 60.0

	# 4. 原退休日期与距离原退休月数
	orig_retire_period = ""
	months_left_orig = 0
	delay_months = 0
	delayed_age_str = f"{int(original_retire)} 岁"
	delayed_retire_age_float = original_retire
	delayed_retire_period = ""
	months_left_delayed = 0

	if birth_d:
		by = birth_d.year
		bm = birth_d.month

		orig_retire_y = by + int(original_retire)
		orig_retire_m = bm
		orig_total_m = orig_retire_y * 12 + orig_retire_m
		ref_total_m = ref_y * 12 + ref_m

		orig_retire_period = f"{orig_retire_y}-{orig_retire_m:02d}"
		months_left_orig = orig_total_m - ref_total_m

		# 5. 渐进式延迟退休 (全国人大 2024 标准)
		if original_retire >= 60:
			base_year = 1965
			step = 4
			max_delay = 36
		elif original_retire >= 55:
			base_year = 1970
			step = 4
			max_delay = 36
		else:
			# 50 岁
			base_year = 1975
			step = 2
			max_delay = 60

		m_diff = (by - base_year) * 12 + bm
		if m_diff <= 0:
			delay_months = 0
		else:
			delay_months = min(max_delay, math.ceil(m_diff / step))

		# 延迟后退休年龄 (岁 + 月)
		d_years = int(original_retire) + (delay_months // 12)
		d_months = delay_months % 12
		if d_months == 0:
			delayed_age_str = f"{d_years} 岁"
		else:
			delayed_age_str = f"{d_years} 岁 {d_months} 个月"

		delayed_retire_age_float = round(original_retire + (delay_months / 12.0), 2)

		del_total_m = orig_total_m + delay_months
		del_retire_y = del_total_m // 12
		del_retire_m = del_total_m % 12
		if del_retire_m == 0:
			del_retire_y -= 1
			del_retire_m = 12

		delayed_retire_period = f"{del_retire_y}-{del_retire_m:02d}"
		months_left_delayed = del_total_m - ref_total_m

	return {
		"is_valid_id": is_valid_id,
		"birth_date": birth_d.strftime("%Y-%m-%d") if birth_d else "",
		"gender": derived_gender or "男",
		"current_age": current_age,
		"current_age_months": current_age_months,
		"current_age_detail": f"{current_age} 岁 {current_age_months} 个月",
		"original_retirement_age": int(original_retire) if original_retire.is_integer() else original_retire,
		"orig_retire_period": orig_retire_period,
		"months_left_orig": months_left_orig,
		"delay_months": delay_months,
		"delayed_retirement_age_str": delayed_age_str,
		"delayed_retirement_age": delayed_retire_age_float,
		"delayed_retire_period": delayed_retire_period,
		"months_left_delayed": months_left_delayed
	}

@frappe.whitelist()
def calculate_employee_age_and_retirement(id_card=None, birth_date=None, gender=None, job_title=None, original_retirement_age=None, period_month=None):
	"""白名单 RPC：以指定账期本月1日为基准返回年龄与原退休/延迟退休倒计时指标"""
	return calculate_age_and_retirement_details(
		id_card=id_card,
		birth_date_str=birth_date,
		gender=gender,
		job_title=job_title,
		original_retirement_age=original_retirement_age,
		ref_period_month=period_month or "2026-07"
	)



@frappe.whitelist()
def get_employee_profiles(company="天津祺富机械加工有限公司", search_text=None, employee_type=None, period_month=None):
	"""
	获取指定公司的人员薪酬档案列表与统计指标
	"""
	filters = {"company": company}
	if employee_type and employee_type != "全部":
		filters["employee_type"] = employee_type

	records = frappe.get_all(
		"Ashan Employee Salary Profile",
		filters=filters,
		fields=[
			"name", "employee_no", "employee_name", "company", "id_card", "mobile",
			"gender", "birth_date", "current_age", "retirement_age", "retirement_date",
			"employee_type", "employment_status", "salary_mode",
			"department", "job_title", "base_salary", "post_allowance", "performance_base",
			"meal_allowance", "traffic_allowance", "communication_allowance", "other_allowance",
			"fixed_salary", "commercial_insurance", "is_insured",
			"social_security_base", "housing_fund_base",
			"deduction_child_education", "deduction_continuing_education",
			"deduction_serious_illness", "deduction_housing_loan",
			"deduction_housing_rent", "deduction_elderly_care", "deduction_infant_care",
			"bank_name", "bank_account", "notes", "modified"
		],
		order_by="employee_no asc"
	)

	# 内存级快速搜索过滤
	if search_text:
		st = search_text.strip().lower()
		records = [
			r for r in records
			if st in (r.get("employee_no") or "").lower()
			or st in (r.get("employee_name") or "").lower()
			or st in (r.get("mobile") or "").lower()
			or st in (r.get("id_card") or "").lower()
			or st in (r.get("department") or "").lower()
			or st in (r.get("job_title") or "").lower()
		]

	# 计算每位员工的专项附加扣除合计、津贴合计与年龄/退休参数 (以本月1日为基准)
	target_pm = period_month or "2026-07"
	for r in records:
		calc_ret = calculate_age_and_retirement_details(
			id_card=r.get("id_card"),
			birth_date_str=r.get("birth_date"),
			gender=r.get("gender"),
			job_title=r.get("job_title"),
			original_retirement_age=r.get("original_retirement_age") or r.get("retirement_age"),
			ref_period_month=target_pm
		)
		r["current_age"] = calc_ret["current_age"]
		r["current_age_months"] = calc_ret["current_age_months"]
		r["current_age_detail"] = calc_ret["current_age_detail"]
		r["original_retirement_age"] = calc_ret["original_retirement_age"]
		r["orig_retire_period"] = calc_ret["orig_retire_period"]
		r["months_left_orig"] = calc_ret["months_left_orig"]
		r["delayed_retirement_age"] = calc_ret["delayed_retirement_age"]
		r["delayed_retirement_age_str"] = calc_ret["delayed_retirement_age_str"]
		r["delay_months"] = calc_ret["delay_months"]
		r["delayed_retire_period"] = calc_ret["delayed_retire_period"]
		r["months_left_delayed"] = calc_ret["months_left_delayed"]
		r["is_valid_id"] = calc_ret["is_valid_id"]
		if not r.get("gender"):
			r["gender"] = calc_ret["gender"]

		total_deduction = (
			flt(r.get("deduction_child_education")) +
			flt(r.get("deduction_continuing_education")) +
			flt(r.get("deduction_serious_illness")) +
			flt(r.get("deduction_housing_loan")) +
			flt(r.get("deduction_housing_rent")) +
			flt(r.get("deduction_elderly_care")) +
			flt(r.get("deduction_infant_care"))
		)
		total_allowance = (
			flt(r.get("post_allowance")) +
			flt(r.get("meal_allowance")) +
			flt(r.get("traffic_allowance")) +
			flt(r.get("communication_allowance")) +
			flt(r.get("other_allowance"))
		)
		r["total_deduction"] = total_deduction
		r["total_allowance"] = total_allowance

	# KPI 统计卡片指标
	total_count = len(records)
	regular_count = len([r for r in records if r.get("employee_type") == "正式工"])
	rehire_count = len([r for r in records if r.get("employee_type") == "返聘工"])
	other_type_count = total_count - regular_count - rehire_count

	# 基础薪资总盘（祺富算固定工资，吉众算基本工资+津贴）
	if "祺富" in company:
		total_base_payroll = sum(flt(r.get("fixed_salary")) for r in records)
	else:
		total_base_payroll = sum(flt(r.get("base_salary")) + flt(r.get("total_allowance")) for r in records)

	return {
		"company": company,
		"records": records,
		"kpi": {
			"total_count": total_count,
			"regular_count": regular_count,
			"rehire_count": rehire_count,
			"other_type_count": other_type_count,
			"total_base_payroll": total_base_payroll
		}
	}


@frappe.whitelist()
def get_qifu_employees(company="天津祺富机械加工有限公司", period_month=None):
	"""获取祺富在职员工档案母表列表 (支持动态按月份基准计算年龄与退休)"""
	res = get_employee_profiles(company=company, period_month=period_month)
	return res.get("records", [])


@frappe.whitelist()
def create_employee_salary_profile(**kwargs):
	"""新建员工薪酬档案"""
	doc = frappe.new_doc("Ashan Employee Salary Profile")
	for k, v in kwargs.items():
		if hasattr(doc, k):
			setattr(doc, k, v)
	if not doc.company:
		doc.company = "天津祺富机械加工有限公司"
	if not doc.employment_status:
		doc.employment_status = "在职"
	doc.insert()
	return {
		"success": True,
		"message": f"✅ 成功创建员工【{doc.employee_name}】薪酬母表档案！",
		"doc": doc
	}


@frappe.whitelist()
def update_employee_salary_profile(name, **kwargs):
	"""更新员工薪酬档案"""
	doc = frappe.get_doc("Ashan Employee Salary Profile", name)
	for k, v in kwargs.items():
		if hasattr(doc, k) and k not in ["name", "doctype", "owner", "creation"]:
			setattr(doc, k, v)
	doc.save()
	return {
		"success": True,
		"message": f"✅ 员工【{doc.employee_name}】档案已更新！",
		"doc": doc
	}


@frappe.whitelist()
def update_single_employee(employee_name, data):
	"""
	更新单名员工的薪酬与人事参数
	"""
	if isinstance(data, str):
		data = json.loads(data)

	if not frappe.db.exists("Ashan Employee Salary Profile", employee_name):
		frappe.throw(f"未找到员工档案: {employee_name}")

	doc = frappe.get_doc("Ashan Employee Salary Profile", employee_name)

	allowed_fields = [
		"id_card", "gender", "birth_date", "current_age", "retirement_age", "retirement_date",
		"original_retirement_age", "delayed_retirement_age",
		"employee_type", "employment_status", "salary_mode",
		"department", "job_title", "base_salary", "post_allowance", "performance_base",
		"meal_allowance", "traffic_allowance", "communication_allowance", "other_allowance",
		"fixed_salary", "commercial_insurance", "is_insured",
		"social_security_base", "housing_fund_base",
		"deduction_child_education", "deduction_continuing_education",
		"deduction_serious_illness", "deduction_housing_loan",
		"deduction_housing_rent", "deduction_elderly_care", "deduction_infant_care",
		"bank_name", "bank_account", "notes"
	]

	for field in allowed_fields:
		if field in data:
			val = data[field]
			if field in ["fixed_salary", "base_salary", "post_allowance", "performance_base",
			             "meal_allowance", "traffic_allowance", "communication_allowance",
			             "other_allowance", "commercial_insurance", "social_security_base",
			             "housing_fund_base", "deduction_child_education", "deduction_continuing_education",
			             "deduction_serious_illness", "deduction_housing_loan", "deduction_housing_rent",
			             "deduction_elderly_care", "deduction_infant_care"]:
				val = flt(val)
			elif field in ["current_age", "is_insured"]:
				val = cint(val)
			doc.set(field, val)

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"success": True, "message": f"员工 {doc.employee_name} 档案参数更新成功！"}


@frappe.whitelist()
def batch_update_employees(employee_names, fieldname, value):
	"""
	批量更新多名员工的指定字段
	"""
	if isinstance(employee_names, str):
		employee_names = json.loads(employee_names)

	if not employee_names:
		frappe.throw("请至少选择一位员工！")

	allowed_fields = [
		"employee_type", "employment_status", "salary_mode", "is_insured",
		"department", "job_title", "base_salary", "post_allowance", "performance_base",
		"meal_allowance", "traffic_allowance", "communication_allowance", "other_allowance",
		"fixed_salary", "commercial_insurance",
		"social_security_base", "housing_fund_base",
		"deduction_child_education", "deduction_continuing_education",
		"deduction_serious_illness", "deduction_housing_loan",
		"deduction_housing_rent", "deduction_elderly_care", "deduction_infant_care"
	]

	if fieldname not in allowed_fields:
		frappe.throw(f"字段 {fieldname} 不支持批量修改！")

	# 类型转换
	if fieldname in ["fixed_salary", "base_salary", "post_allowance", "performance_base",
	                 "meal_allowance", "traffic_allowance", "communication_allowance",
	                 "other_allowance", "commercial_insurance", "social_security_base",
	                 "housing_fund_base", "deduction_child_education", "deduction_continuing_education",
	                 "deduction_serious_illness", "deduction_housing_loan", "deduction_housing_rent",
	                 "deduction_elderly_care", "deduction_infant_care"]:
		val = flt(value)
	elif fieldname in ["is_insured"]:
		val = cint(value)
	else:
		val = str(value).strip()

	updated_count = 0
	for name in employee_names:
		if frappe.db.exists("Ashan Employee Salary Profile", name):
			doc = frappe.get_doc("Ashan Employee Salary Profile", name)
			doc.set(fieldname, val)
			doc.save(ignore_permissions=True)
			updated_count += 1

	frappe.db.commit()

	return {
		"success": True,
		"updated_count": updated_count,
		"message": f"成功批量修改 {updated_count} 位员工的【{fieldname}】为 {value}！"
	}


@frappe.whitelist()
def set_qifu_social_security_batch(mode="min"):
	"""
	祺富全员社保一键批量设置：
	将所有用工性质为【正式工】的员工社保基数设为最低基数 5124.0 元 (或配置中的 ss_min_base)；
	退休返聘、临时工等非正式用工保持 0 元。
	"""
	company = "天津祺富机械加工有限公司"
	target_base = 5124.0
	setting_name = f"{company}-社保公积金配置"
	if frappe.db.exists("Ashan Insurance Setting", setting_name):
		doc_setting = frappe.get_doc("Ashan Insurance Setting", setting_name)
		target_base = flt(doc_setting.ss_min_base) or 5124.0

	employees = frappe.get_all(
		"Ashan Employee Salary Profile",
		filters={"company": company, "employment_status": "在职"},
		fields=["name", "employee_no", "employee_name", "employee_type", "social_security_base"]
	)

	updated_count = 0
	for emp in employees:
		emp_type = emp.get("employee_type") or "正式工"
		if emp_type == "正式工":
			val = target_base if mode == "min" else 0.0
			doc = frappe.get_doc("Ashan Employee Salary Profile", emp["name"])
			doc.social_security_base = val
			doc.is_insured = 1 if val > 0 else 0
			doc.save(ignore_permissions=True)
			updated_count += 1

	frappe.db.commit()
	return {
		"success": True,
		"updated_count": updated_count,
		"message": f"✅ 已成功将 {updated_count} 位正式工的社保基数设为最低基数 ({target_base:,.2f} 元)！"
	}


@frappe.whitelist()
def set_qifu_housing_fund_batch(mode="min"):
	"""
	祺富全员公积金一键批量设置优化：
	1. 核心资格准入：只有社保基数 > 0 (social_security_base > 0) 的在职参保员工才有资格设置公积金！未参保人员(社保基数=0)自动跳过并保持 0。
	2. 核心白名单豁免：孟祥山 (工号 A0006) 绝对豁免，不受任何一键操作影响并保留原有基数！
	3. mode == 'min': 将符合资格的在保员工公积金基数设为当年配置中的最低基数 (如 2320 元)。
	4. mode == 'zero': 将所有祺富员工(除孟祥山外)公积金基数清零 (0 元)。
	"""
	company = "天津祺富机械加工有限公司"
	target_base = 0.0

	if mode == "min":
		setting_name = f"{company}-社保公积金配置"
		if frappe.db.exists("Ashan Insurance Setting", setting_name):
			doc_setting = frappe.get_doc("Ashan Insurance Setting", setting_name)
			target_base = flt(doc_setting.hf_min_base) or 2320.0
		else:
			target_base = 2320.0

	employees = frappe.get_all(
		"Ashan Employee Salary Profile",
		filters={"company": company, "employment_status": "在职"},
		fields=["name", "employee_no", "employee_name", "social_security_base", "housing_fund_base", "employee_type"]
	)

	updated_count = 0
	skipped_no_insurance = []
	protected_employees = []

	for emp in employees:
		emp_name = (emp.get("employee_name") or "").strip()
		emp_no = (emp.get("employee_no") or "").strip()
		ss_base = flt(emp.get("social_security_base"))

		# 1. 白名单豁免保护
		if emp_name == "孟祥山" or emp_no == "A0006":
			protected_employees.append(f"{emp_name} ({emp_no}) [当前基数: {emp.get('housing_fund_base')}]")
			continue

		# 2. 资格校验：仅社保基数 > 0 才有资格开启公积金
		if mode == "min" and ss_base <= 0:
			skipped_no_insurance.append(f"{emp_name} ({emp_no})")
			continue

		doc = frappe.get_doc("Ashan Employee Salary Profile", emp.get("name"))
		doc.housing_fund_base = target_base
		if doc.salary_mode not in ["税后", "税前", "税前动态工资", "税后管理工资"]:
			doc.salary_mode = "税后"
		doc.save(ignore_permissions=True)
		updated_count += 1

	frappe.db.commit()

	action_desc = f"设置为最低基数 ({target_base} 元)" if mode == "min" else "取消公积金 (设为 0)"
	skip_msg = ""
	if skipped_no_insurance:
		skip_msg = f"<br>⚠️ 已自动跳过 {len(skipped_no_insurance)} 位未缴纳社保人员（社保基数=0）"

	return {
		"success": True,
		"mode": mode,
		"target_base": target_base,
		"updated_count": updated_count,
		"skipped_count": len(skipped_no_insurance),
		"skipped_no_insurance": skipped_no_insurance,
		"protected_employees": protected_employees,
		"message": f"操作成功！已将祺富 {updated_count} 位在保员工公积金{action_desc}。{skip_msg}<br>🛡️ 孟祥山已自动豁免保护！"
	}

@frappe.whitelist()
def get_insurance_setting(company="天津祺富机械加工有限公司", year=2026):
	"""
	获取指定公司与年份的社保公积金费率配置及合计比例
	"""
	setting_name = f"{company}-{year}"
	if not frappe.db.exists("Ashan Insurance Setting", setting_name):
		# 初始化默认记录
		doc = frappe.new_doc("Ashan Insurance Setting")
		doc.company = company
		doc.effective_year = cint(year)
		doc.ss_company_pension = 16.0
		doc.ss_company_unemployment = 0.5
		doc.ss_company_medical = 10.0
		doc.ss_company_other_medical = 0.5
		doc.ss_company_injury = 0.55 if "祺富" in company else 0.35
		doc.ss_person_pension = 8.0
		doc.ss_person_unemployment = 0.5
		doc.ss_person_medical = 2.0
		doc.big_medical_amount_default = 22.0
		doc.big_medical_amount_special = 21.0
		doc.big_medical_special_months = "3,12"
		doc.hf_company_rate = 5.0
		doc.hf_person_rate = 5.0
		doc.ss_min_base = 5013.0 if "祺富" in company else 5124.0
		doc.hf_min_base = 2320.0
		doc.tax_threshold = 5000.0
		doc.save(ignore_permissions=True)
		frappe.db.commit()
	else:
		doc = frappe.get_doc("Ashan Insurance Setting", setting_name)

	# 汇总计算合计比例
	comp_ss_total = round(
		flt(doc.ss_company_pension) + flt(doc.ss_company_unemployment) +
		flt(doc.ss_company_medical) + flt(doc.ss_company_other_medical) +
		flt(doc.ss_company_injury), 4
	)
	pers_ss_total = round(
		flt(doc.ss_person_pension) + flt(doc.ss_person_unemployment) +
		flt(doc.ss_person_medical), 4
	)
	hf_total = round(flt(doc.hf_company_rate) + flt(doc.hf_person_rate), 4)
	overall_rate = round(comp_ss_total + pers_ss_total + hf_total, 4)

	res = doc.as_dict()
	res.update({
		"total_ss_company_rate": comp_ss_total,
		"total_ss_person_rate": pers_ss_total,
		"total_hf_rate": hf_total,
		"total_overall_rate": overall_rate
	})
	return res

@frappe.whitelist()
def save_insurance_setting(company, year, data):
	"""
	保存/更新指定公司与年份的社保公积金费率与基数配置
	"""
	if isinstance(data, str):
		data = json.loads(data)

	setting_name = f"{company}-{year}"
	if frappe.db.exists("Ashan Insurance Setting", setting_name):
		doc = frappe.get_doc("Ashan Insurance Setting", setting_name)
	else:
		doc = frappe.new_doc("Ashan Insurance Setting")
		doc.company = company
		doc.effective_year = cint(year)

	for k, v in data.items():
		if hasattr(doc, k):
			if k in ["effective_year"]:
				setattr(doc, k, cint(v))
			elif k in ["company", "big_medical_special_months"]:
				setattr(doc, k, str(v or "").strip())
			else:
				setattr(doc, k, flt(v))

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"success": True,
		"message": f"🎉【{company}】{year} 年度社保公积金配置保存成功！合计比例与薪酬测算已即时联动生效。",
		"doc": get_insurance_setting(company, year)
	}


