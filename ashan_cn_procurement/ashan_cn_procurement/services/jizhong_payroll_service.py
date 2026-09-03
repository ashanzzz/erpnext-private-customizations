# Copyright (c) 2026, Ashan CN Procurement
# 天津吉众科技有限公司 - 专有薪资核算、累计个税反推与五档配钞点钞服务
# 1:1 精确对齐《202606吉众人事综合.xlsm》全套业务公式

import os
import math
import frappe
from frappe.utils import flt, cint, getdate

from ashan_cn_procurement.services.ashan_holiday_service import get_month_workdays

# 常量定义
FULL_DAY_HOURS = 8.0
FIXED_MONTHLY_DAYS = 21.5
FIXED_MONTHLY_HOURS = FIXED_MONTHLY_DAYS * FULL_DAY_HOURS # 172.0h

# 七级综合累计个税税率表 (速算扣除数按年累计)
TAX_BRACKETS_ANNUAL = [
	(0.0, 36000.0, 0.03, 0.0),
	(36000.0, 144000.0, 0.10, 2520.0),
	(144000.0, 300000.0, 0.20, 16920.0),
	(300000.0, 420000.0, 0.25, 31920.0),
	(420000.0, 660000.0, 0.30, 52920.0),
	(660000.0, 960000.0, 0.35, 85920.0),
	(960000.0, 999999999.0, 0.45, 181920.0),
]


def _get_annual_tax(taxable_income):
	"""根据年累计应纳税所得额计算累计应纳税额"""
	if taxable_income <= 0:
		return 0.0
	for lower, upper, rate, quick_ded in TAX_BRACKETS_ANNUAL:
		if lower < taxable_income <= upper:
			return round(taxable_income * rate - quick_ded, 2)
	# 超出最高档
	return round(taxable_income * 0.45 - 181920.0, 2)


def derive_jizhong_gross_from_net(
	target_net,
	special_deductions_cur=0.0,
	tax_threshold=5000.0,
	prev_gross=0.0,
	prev_threshold=0.0,
	prev_special_ded=0.0,
	prev_additional_ded=0.0,
	prev_tax_paid=0.0,
	cur_additional_ded=0.0,
):
	"""
	1:1 复刻《个人所得税.bas》个人所得税_辅助函数_反推计算应缴所得税
	根据约定税后净发，闭式反推当月税前薪酬、当月代扣个税与累计税金
	"""
	# VBA 原版闭式公式：
	# 目前应纳税所得税 = Round(((以往税前 + 当月税后 - 以往已纳税 - 以往免征 - 以往专项 - 以往附加 - 当月免征 - 当月附加) * 税率 - 速算扣除数) / (1 - 税率), 2)
	# 当月扣个税 = 目前应纳税所得税 - 以往已纳税
	# 反推税前 = 当月税后 + 当月专项扣除 + 当月扣个税

	target_gross = 0.0
	cur_tax = 0.0
	matched_tax = 0.0

	for lower, upper, rate, quick_ded in TAX_BRACKETS_ANNUAL:
		numerator = (
			(prev_gross + target_net - prev_tax_paid - prev_threshold - prev_special_ded - prev_additional_ded - tax_threshold - cur_additional_ded) * rate
			- quick_ded
		)
		if 1.0 - rate == 0:
			continue
		cum_tax_calc = round(numerator / (1.0 - rate), 2)
		if cum_tax_calc < 0:
			tax_this_month = 0.0
			cum_tax_calc = 0.0
		else:
			tax_this_month = round(cum_tax_calc - prev_tax_paid, 2)

		candidate_gross = round(target_net + special_deductions_cur + tax_this_month, 2)

		# 正推验算
		cum_taxable = (prev_gross + candidate_gross) - (prev_threshold + tax_threshold) - (prev_special_ded + special_deductions_cur) - (prev_additional_ded + cur_additional_ded)
		verify_tax = _get_annual_tax(cum_taxable)

		if abs(verify_tax - cum_tax_calc) <= 0.02:
			target_gross = candidate_gross
			cur_tax = max(0.0, tax_this_month)
			matched_tax = verify_tax
			break

	if target_gross <= 0.0:
		# 极低薪资或无须纳税边界
		target_gross = round(target_net + special_deductions_cur, 2)
		cur_tax = 0.0

	return {
		"gross_salary": target_gross,
		"tax_amount": cur_tax,
		"net_salary": target_net,
	}


def split_cash_bills(cash_amount):
	"""五档人民币面额贪心拆分 (100, 50, 10, 5, 1)"""
	amt = int(cash_amount)
	b100 = amt // 100
	rem = amt % 100
	b50 = rem // 50
	rem = rem % 50
	b10 = rem // 10
	rem = rem % 10
	b5 = rem // 5
	rem = rem % 5
	b1 = rem
	return b100, b50, b10, b5, b1


@frappe.whitelist(methods=["POST"])
def calculate_jizhong_monthly_payroll(company="天津吉众科技有限公司", period_month=None):
	"""
	执行吉众月度薪酬核算全流程：
	1. 归集考勤工时与倒休抵扣
	2. 动态工作日 (168h/184h) vs 固定平均日 (172h) 双基准计算
	3. 税后管理工资闭式反推
	4. 历史个税累计预扣计算
	5. 现金发放 RoundUp 与五档点钞
	6. 生成或更新 Ashan Monthly Payroll Settlement
	"""
	if not period_month:
		frappe.throw("必须指定核算月份，如 '2026-06' 或 '2026-07'")

	# 1. 动态获取当月法定工作日天数
	year = cint(period_month.split("-")[0])
	month = cint(period_month.split("-")[1])
	dynamic_workdays = get_month_workdays(year, month) or 21
	dynamic_work_hours = dynamic_workdays * FULL_DAY_HOURS # 如 21天 -> 168.0h, 23天 -> 184.0h

	# 2. 获取社保公积金配置
	ins_setting = frappe.db.get_value(
		"Ashan Insurance Setting",
		{"company": ["like", "%吉众%"], "effective_year": year},
		["*"],
		as_dict=True
	) or {}

	ss_person_rate = flt(ins_setting.get("ss_person_pension") or 8.0) + flt(ins_setting.get("ss_person_medical") or 2.0) + flt(ins_setting.get("ss_person_unemployment") or 0.5)
	injury_rate = flt(ins_setting.get("ss_company_injury") or 0.55)
	ss_company_rate = (
		flt(ins_setting.get("ss_company_pension") or 16.0) +
		flt(ins_setting.get("ss_company_medical") or 10.0) +
		flt(ins_setting.get("ss_company_unemployment") or 0.5) +
		flt(ins_setting.get("ss_company_other_medical") or 0.5) +
		injury_rate
	)
	hf_person_rate = flt(ins_setting.get("hf_person_rate") or 5.0)
	hf_company_rate = flt(ins_setting.get("hf_company_rate") or 5.0)
	tax_threshold = 5000.0

	cur_month_num = cint(period_month.split("-")[1])
	# 大额医疗特殊月 (1, 4, 7, 10月为21元，其余22元)
	big_med = 21.0 if cur_month_num in (1, 4, 7, 10) else 22.0

	# 3. 获取全员薪酬档案
	employees = frappe.get_all(
		"Ashan Employee Salary Profile",
		filters={"company": company},
		fields=[
			"name", "employee_no", "employee_name", "employee_type", "employment_status",
			"salary_mode", "fixed_salary", "base_salary", "post_allowance", "performance_base",
			"meal_allowance", "traffic_allowance", "communication_allowance", "other_allowance",
			"social_security_base", "housing_fund_base", "id_card", "mobile", "department", "job_title",
			"deduction_child_education", "deduction_continuing_education", "deduction_housing_loan",
			"deduction_housing_rent", "deduction_elderly_care", "deduction_infant_care", "deduction_serious_illness"
		],
		order_by="employee_no asc"
	)

	# 4. 获取当月考勤底册
	attendances = {}
	att_records = frappe.get_all(
		"Ashan Monthly Attendance",
		filters={"company": company, "period_month": period_month},
		fields=["*"]
	)
	for a in att_records:
		attendances[a.employee_no] = a

	# 5. 归集当前个税周期以往历史累计数据 (自上一年度12月或本年1月起)
	tax_cycle_start = 12
	tax_history = _get_jizhong_tax_history(company, period_month, tax_cycle_start)

	# 6. 初始化或加载 Settlement 单据
	doc_name = f"{company}-{period_month}"
	if frappe.db.exists("Ashan Monthly Payroll Settlement", doc_name):
		doc = frappe.get_doc("Ashan Monthly Payroll Settlement", doc_name)
		doc.items = []
	else:
		doc = frappe.new_doc("Ashan Monthly Payroll Settlement")
		doc.company = company
		doc.period_month = period_month

	doc.status = "草稿"
	doc.locked = 0
	doc.workflow_stage = "草稿"

	total_gross = 0.0
	total_net = 0.0
	total_ss_comp = 0.0
	total_ss_pers = 0.0
	total_hf_comp = 0.0
	total_hf_pers = 0.0
	total_tax = 0.0
	total_cash = 0.0

	# 委托不分钞人员工号集合
	NO_CASH_EMPS = {"L0001"}

	for emp in employees:
		emp_no = emp.employee_no
		emp_name = emp.employee_name
		salary_mode = str(emp.salary_mode or "税前动态工资").strip()
		emp_type = str(emp.employee_type or "正式工").strip()

		att = attendances.get(emp_no)
		full_days = flt(att.attendance_days) if att else 21.75
		half_days = flt(att.half_days) if att else 0.0
		absent_days = flt(att.absent_days) if att else 0.0
		work_hrs = flt(att.work_hours_regular) if att else dynamic_work_hours
		ot_1_5 = flt(att.overtime_regular_1_5) if att else 0.0
		ot_2_0 = flt(att.overtime_weekend_2_0) if att else 0.0
		ot_3_0 = flt(att.overtime_holiday_3_0) if att else 0.0
		leave_comp = flt(att.leave_compensatory_hours) if att else 0.0
		meal_cnt = cint(att.meal_count) if att else 0

		# 薪资标准项
		base_sal = flt(emp.base_salary)
		post_allow = flt(emp.post_allowance)
		perf_base = flt(emp.performance_base)
		fixed_sal = flt(emp.fixed_salary)
		meal_unit_price = flt(emp.meal_allowance or 15.0)

		# 社保与公积金基数处理 (返聘/临时等不扣社保)
		no_insurance = emp_type in ("返聘工", "临时工", "兼职", "实习生")
		ss_base = 0.0 if no_insurance else flt(emp.social_security_base)
		hf_base = 0.0 if no_insurance else flt(emp.housing_fund_base)

		# 专项个人扣除
		ss_pers = round(ss_base * (ss_person_rate / 100.0) + (big_med if ss_base > 0 else 0.0), 2)
		hf_pers = round(hf_base * (hf_person_rate / 100.0), 2)
		ss_comp = round(ss_base * (ss_company_rate / 100.0), 2)
		hf_comp = round(hf_base * (hf_company_rate / 100.0), 2)

		company_cost = round(ss_comp + hf_comp, 2)
		person_special_ded = round(ss_pers + hf_pers, 2)

		# 专项附加扣除
		additional_ded = round(
			flt(emp.deduction_child_education) +
			flt(emp.deduction_continuing_education) +
			flt(emp.deduction_housing_loan) +
			flt(emp.deduction_housing_rent) +
			flt(emp.deduction_elderly_care) +
			flt(emp.deduction_infant_care) +
			flt(emp.deduction_serious_illness),
			2
		)

		# 历史个税累计
		hist = tax_history.get(emp_no, {})
		prev_gross = flt(hist.get("prev_gross", 0.0))
		prev_thresh = flt(hist.get("prev_thresh", 0.0))
		prev_special_ded = flt(hist.get("prev_special_ded", 0.0))
		prev_add_ded = flt(hist.get("prev_add_ded", 0.0))
		prev_tax_paid = flt(hist.get("prev_tax_paid", 0.0))

		# 分项测算
		sal_basic_hrs = 0.0
		sal_ot_1_5 = 0.0
		sal_ot_2_0 = 0.0
		sal_ot_3_0 = 0.0
		sal_basic_sub = 0.0
		sal_perf = 0.0
		sal_post = 0.0
		sal_meal = 0.0
		sal_adj = 0.0
		gross_sal = 0.0
		tax_amt = 0.0
		net_sal = 0.0

		if salary_mode == "税后管理工资":
			# 税后管理工资：各项工时工资置 0，直接以目标净发反推
			target_net = fixed_sal if fixed_sal > 0 else (base_sal if base_sal > 0 else 10000.0)
			res = derive_jizhong_gross_from_net(
				target_net=target_net,
				special_deductions_cur=person_special_ded,
				tax_threshold=tax_threshold,
				prev_gross=prev_gross,
				prev_threshold=prev_thresh,
				prev_special_ded=prev_special_ded,
				prev_additional_ded=prev_add_ded,
				prev_tax_paid=prev_tax_paid,
				cur_additional_ded=additional_ded,
			)
			gross_sal = res["gross_salary"]
			tax_amt = res["tax_amount"]
			net_sal = target_net
			sal_basic_hrs = gross_sal # 管理岗位全额计入基本工时工资
		else:
			# 税前动态工资正算
			dyn_hourly = round(base_sal / dynamic_work_hours, 6) if dynamic_work_hours > 0 else 0.0
			fix_hourly = round(base_sal / FIXED_MONTHLY_HOURS, 6) # 基本工资 / 172.0
			absence_hrs = max(0.0, dynamic_work_hours - work_hrs)

			sal_basic_hrs = round(work_hrs * dyn_hourly, 2)
			sal_ot_1_5 = round(fix_hourly * ot_1_5 * 1.5, 2)
			sal_ot_2_0 = round(fix_hourly * ot_2_0 * 2.0, 2)
			sal_ot_3_0 = round(fix_hourly * ot_3_0 * 3.0, 2)

			sal_basic_sub = round(post_allow - (post_allow / dynamic_work_hours * absence_hrs), 2) if post_allow else 0.0
			sal_perf = round(perf_base - (perf_base / FIXED_MONTHLY_HOURS * absence_hrs), 2) if perf_base else 0.0
			sal_post = 0.0
			sal_meal = round(meal_unit_price * meal_cnt, 2)
			sal_adj = 0.0

			gross_sal = round(sal_basic_hrs + sal_ot_1_5 + sal_ot_2_0 + sal_ot_3_0 + sal_basic_sub + sal_perf + sal_meal + sal_adj, 2)

			# 累计预扣个税计算
			cum_taxable = round(
				(prev_gross + gross_sal) - (prev_thresh + tax_threshold) - (prev_special_ded + person_special_ded) - (prev_add_ded + additional_ded),
				2
			)
			cum_tax = _get_annual_tax(cum_taxable)
			tax_amt = max(0.0, round(cum_tax - prev_tax_paid, 2))
			net_sal = round(gross_sal - person_special_ded - tax_amt, 2)

		person_cost = round(person_special_ded + tax_amt, 2)

		# 现金发放与配钞
		if emp_no in NO_CASH_EMPS or emp_type in ("兼职", "委托"):
			cash_wage = 0.0
			b100 = b50 = b10 = b5 = b1 = 0
		else:
			cash_wage = float(math.ceil(net_sal)) if net_sal > 0 else 0.0
			b100, b50, b10, b5, b1 = split_cash_bills(cash_wage)

		# 累加全局统计
		total_gross += gross_sal
		total_net += net_sal
		total_ss_comp += ss_comp
		total_ss_pers += ss_pers
		total_hf_comp += hf_comp
		total_hf_pers += hf_pers
		total_tax += tax_amt
		total_cash += cash_wage

		# 构建 Child Item
		doc.append("items", {
			"employee_no": emp_no,
			"employee_name": emp_name,
			"department": emp.department,
			"job_title": emp.job_title,
			"employee_type": emp_type,
			"salary_mode": salary_mode,
			"id_card": emp.id_card,
			"mobile": emp.mobile,
			"attendance_days": full_days,
			"half_days": half_days,
			"absent_days": absent_days,
			"work_hours": work_hrs,
			"basic_hours": work_hrs,
			"overtime_regular_1_5": ot_1_5,
			"overtime_weekend_2_0": ot_2_0,
			"overtime_holiday_3_0": ot_3_0,
			"leave_compensatory_hours": leave_comp,
			"meal_count": meal_cnt,
			"meal_unit_price": meal_unit_price,
			"base_salary": base_sal,
			"post_allowance": post_allow,
			"performance_salary": perf_base,
			"salary_basic_hours": sal_basic_hrs,
			"salary_overtime_1_5": sal_ot_1_5,
			"salary_overtime_2_0": sal_ot_2_0,
			"salary_overtime_3_0": sal_ot_3_0,
			"salary_basic_subsidy": sal_basic_sub,
			"salary_performance": sal_perf,
			"salary_post_allowance": sal_post,
			"salary_meal_subsidy": sal_meal,
			"salary_adjustment": sal_adj,
			"gross_salary": gross_sal,
			"ss_base": ss_base,
			"ss_person_total": ss_pers,
			"ss_company_total": ss_comp,
			"hf_base": hf_base,
			"hf_person_total": hf_pers,
			"hf_company_total": hf_comp,
			"special_deductions_total": additional_ded,
			"taxable_income": max(0.0, round(gross_sal - tax_threshold - person_special_ded - additional_ded, 2)),
			"tax_amount": tax_amt,
			"net_salary": net_sal,
			"company_cost_total": company_cost,
			"person_cost_total": person_cost,
			"cash_pay": cash_wage,
			"bills_100": b100,
			"bills_50": b50,
			"bills_10": b10,
			"bills_5": b5,
			"bills_1": b1,
		})

	# 更新父表总额
	doc.total_employees = len(doc.items)
	doc.total_gross_salary = round(total_gross, 2)
	doc.total_net_salary = round(total_net, 2)
	doc.total_social_security_company = round(total_ss_comp, 2)
	doc.total_social_security_person = round(total_ss_pers, 2)
	doc.total_housing_fund_company = round(total_hf_comp, 2)
	doc.total_housing_fund_person = round(total_hf_pers, 2)
	doc.total_tax = round(total_tax, 2)

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"success": True,
		"settlement_name": doc.name,
		"period_month": period_month,
		"total_employees": doc.total_employees,
		"total_gross_salary": doc.total_gross_salary,
		"total_net_salary": doc.total_net_salary,
		"total_tax": doc.total_tax,
		"total_cash": round(total_cash, 2),
	}


def _get_jizhong_tax_history(company, current_period, tax_cycle_start_month=12):
	"""
	从以往已归档/核定的结算单或历史数据中，提取该税收周期内的累计发生数
	"""
	curr_year = cint(current_period.split("-")[0])
	curr_month = cint(current_period.split("-")[1])

	# 确定周期包含的历史月份列表
	months_in_cycle = []
	if tax_cycle_start_month == 12:
		# 上年12月
		prev_dec = f"{curr_year - 1:04d}-12"
		months_in_cycle.append(prev_dec)
		for m in range(1, curr_month):
			months_in_cycle.append(f"{curr_year:04d}-{m:02d}")
	else:
		for m in range(1, curr_month):
			months_in_cycle.append(f"{curr_year:04d}-{m:02d}")

	if not months_in_cycle:
		return {}

	# 查询历史月度账单
	items = frappe.db.sql(
		"""
		SELECT
			pi.employee_no,
			SUM(pi.gross_salary) as prev_gross,
			SUM(IFNULL(pi.tax_threshold, 5000)) as prev_thresh,
			SUM(pi.ss_person_total + pi.hf_person_total) as prev_special_ded,
			SUM(pi.special_deductions_total) as prev_add_ded,
			SUM(pi.tax_amount) as prev_tax_paid
		FROM `tabAshan Monthly Payroll Item` pi
		JOIN `tabAshan Monthly Payroll Settlement` ps ON pi.parent = ps.name
		WHERE ps.company = %s AND ps.period_month IN %s
		GROUP BY pi.employee_no
		""",
		(company, tuple(months_in_cycle)),
		as_dict=True
	)

	return {it.employee_no: it for it in items}


@frappe.whitelist()
def get_jizhong_payroll_overview(company="天津吉众科技有限公司", period_month=None):
	"""
	获取指定期间吉众薪酬大宽表、现金配钞、个税明细等完整数据
	"""
	if not period_month:
		latest = frappe.db.get_value(
			"Ashan Monthly Payroll Settlement",
			{"company": company},
			"period_month",
			order_by="period_month desc"
		)
		period_month = latest or getdate().strftime("%Y-%m")

	doc_name = f"{company}-{period_month}"
	if not frappe.db.exists("Ashan Monthly Payroll Settlement", doc_name):
		return {"settlement": None, "items": []}

	doc = frappe.get_doc("Ashan Monthly Payroll Settlement", doc_name)
	items = [it.as_dict() for it in doc.items]

	# 计算配钞汇总
	bill_summary = {
		"total_cash": sum(flt(it.get("cash_pay", 0)) for it in items),
		"bills_100": sum(cint(it.get("bills_100", 0)) for it in items),
		"bills_50": sum(cint(it.get("bills_50", 0)) for it in items),
		"bills_10": sum(cint(it.get("bills_10", 0)) for it in items),
		"bills_5": sum(cint(it.get("bills_5", 0)) for it in items),
		"bills_1": sum(cint(it.get("bills_1", 0)) for it in items),
	}

	return {
		"settlement": doc.as_dict(),
		"items": items,
		"bill_summary": bill_summary,
	}


@frappe.whitelist()
def get_jizhong_history_records(company="天津吉众科技有限公司", period_month=None):
	"""
	获取吉众历史薪酬记录 (支持全部或按账期过滤，穿透 child table)
	"""
	cond = "ps.company = %s"
	params = [company]
	if period_month and period_month != "ALL":
		cond += " AND ps.period_month = %s"
		params.append(period_month)

	items = frappe.db.sql(
		f"""
		SELECT
			pi.*,
			ps.period_month
		FROM `tabAshan Monthly Payroll Item` pi
		JOIN `tabAshan Monthly Payroll Settlement` ps ON pi.parent = ps.name
		WHERE {cond}
		ORDER BY ps.period_month DESC, pi.employee_no ASC
		LIMIT 1000
		""",
		tuple(params),
		as_dict=True
	)
	return items


@frappe.whitelist()
def get_jizhong_insurance_setting(year=2026):
	"""获取吉众专属社保公积金设置"""
	year = cint(year) or 2026
	doc_name = f"天津吉众科技有限公司-{year}"
	if not frappe.db.exists("Ashan Insurance Setting", doc_name):
		doc = frappe.new_doc("Ashan Insurance Setting")
		doc.company = "天津吉众科技有限公司"
		doc.effective_year = year
		doc.ss_company_injury = 0.55
		doc.ss_company_pension = 16.0
		doc.ss_company_medical = 10.0
		doc.ss_company_unemployment = 0.5
		doc.ss_company_other_medical = 0.5
		doc.ss_person_pension = 8.0
		doc.ss_person_medical = 2.0
		doc.ss_person_unemployment = 0.5
		doc.hf_person_rate = 5.0
		doc.hf_company_rate = 5.0
		doc.insert(ignore_permissions=True)
		return doc.as_dict()

	return frappe.get_doc("Ashan Insurance Setting", doc_name).as_dict()


@frappe.whitelist(methods=["POST"])
def update_jizhong_insurance_setting(year=2026, values=None):
	"""保存吉众专属社保公积金设置"""
	import json
	if isinstance(values, str):
		values = json.loads(values)
	year = cint(year) or 2026
	doc_name = f"天津吉众科技有限公司-{year}"
	if frappe.db.exists("Ashan Insurance Setting", doc_name):
		doc = frappe.get_doc("Ashan Insurance Setting", doc_name)
	else:
		doc = frappe.new_doc("Ashan Insurance Setting")
		doc.company = "天津吉众科技有限公司"
		doc.effective_year = year

	if values and isinstance(values, dict):
		for k, v in values.items():
			if hasattr(doc, k):
				setattr(doc, k, flt(v))

	doc.save(ignore_permissions=True)
	return {"success": True, "setting": doc.as_dict()}

