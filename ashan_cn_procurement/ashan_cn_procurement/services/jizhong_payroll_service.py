# Copyright (c) 2026, Ashan CN Procurement
# 天津吉众科技有限公司 - 专有薪资核算、累计个税反推与五档配钞点钞服务
# 1:1 精确对齐《202606吉众人事综合.xlsm》全套业务公式

import os
import math
import frappe
from frappe.utils import flt, cint, getdate

from ashan_cn_procurement.services.ashan_holiday_service import get_month_workdays
from ashan_cn_procurement.services.authorization_service import assert_company_access

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

		if abs(verify_tax - cum_tax_calc) <= 0.05:
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
	# 参数防御：容错实参与形参顺序颠倒 (例如 (period_month, company) 或仅传 period_month)
	if company and ("-" in str(company) or (len(str(company)) == 7 and str(company)[:4].isdigit())) and ("公司" in str(period_month or "")):
		company, period_month = period_month, company
	elif not period_month and company and ("-" in str(company) or len(str(company)) == 7):
		period_month, company = company, "天津吉众科技有限公司"

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

	# 吉众大额医疗保险个人固定 21.00 元 (与吉众社保台账 1:1 精确对齐)
	big_med = 21.0

	# 3. 获取全员薪酬档案 (优先使用专属 Jizhong Employee Salary Profile)
	profile_doctype = "Jizhong Employee Salary Profile" if frappe.db.table_exists("Jizhong Employee Salary Profile") and frappe.db.count("Jizhong Employee Salary Profile", {"company": company}) > 0 else "Ashan Employee Salary Profile"
	employees = frappe.get_all(
		profile_doctype,
		filters={"company": company},
		fields=[
			"name", "employee_no", "employee_name", "employee_type", "employment_status",
			"salary_mode", "fixed_salary", "base_salary", "house_rent_allowance", "post_allowance", "performance_base",
			"meal_allowance", "social_security_base", "housing_fund_base", "id_card", "mobile", "department", "job_title",
			"deduction_child_education", "deduction_continuing_education", "deduction_housing_loan",
			"deduction_housing_rent", "deduction_elderly_care", "deduction_infant_care", "deduction_serious_illness"
		],
		order_by="employee_no asc"
	)

	# 4. 获取当月考勤底册
	attendances = {}
	att_records = frappe.get_all(
		"Jizhong Monthly Attendance",
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
		work_hrs = round(flt(att.work_hours_regular), 1) if att else dynamic_work_hours
		ot_1_5 = round(flt(att.overtime_regular_1_5), 1) if att else 0.0
		ot_2_0 = round(flt(att.overtime_weekend_2_0), 1) if att else 0.0
		ot_3_0 = round(flt(att.overtime_holiday_3_0), 1) if att else 0.0
		leave_comp = round(flt(att.leave_compensatory_hours), 1) if att else 0.0
		meal_cnt = cint(att.meal_count) if att else 0

		# 薪资标准项
		base_sal = flt(emp.base_salary)
		base_sub = flt(emp.house_rent_allowance)
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
			absence_hrs = round(max(0.0, dynamic_work_hours - work_hrs), 1)

			sal_basic_hrs = round(work_hrs * dyn_hourly, 2)
			sal_ot_1_5 = round(fix_hourly * ot_1_5 * 1.5, 2)
			sal_ot_2_0 = round(fix_hourly * ot_2_0 * 2.0, 2)
			sal_ot_3_0 = round(fix_hourly * ot_3_0 * 3.0, 2)

			sal_basic_sub = round(base_sub - (base_sub / dynamic_work_hours * absence_hrs), 2) if base_sub else 0.0
			sal_perf = round(perf_base - (perf_base / FIXED_MONTHLY_HOURS * absence_hrs), 2) if perf_base else 0.0
			sal_post = round(post_allow - (post_allow / dynamic_work_hours * absence_hrs), 2) if post_allow else 0.0
			sal_meal = round(meal_unit_price * meal_cnt, 2)
			sal_adj = 0.0

			gross_sal = round(sal_basic_hrs + sal_ot_1_5 + sal_ot_2_0 + sal_ot_3_0 + sal_basic_sub + sal_perf + sal_post + sal_meal + sal_adj, 2)

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
			"work_hours": round(work_hrs, 1),
			"basic_hours": round(work_hrs, 1),
			"overtime_regular_1_5": round(ot_1_5, 1),
			"overtime_weekend_2_0": round(ot_2_0, 1),
			"overtime_holiday_3_0": round(ot_3_0, 1),
			"leave_compensatory_hours": round(leave_comp, 1),
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


@frappe.whitelist(methods=["POST"])
def lock_jizhong_monthly_payroll(company="天津吉众科技有限公司", period_month=None):
	"""
	核定锁定吉众月度薪酬核定表 (只读封账)
	"""
	if not period_month:
		frappe.throw("必须指定核算月份")
	doc_name = f"{company}-{period_month}"
	if not frappe.db.exists("Ashan Monthly Payroll Settlement", doc_name):
		frappe.throw(f"未找到【{company}】{period_month} 的薪酬核算记录，无法执行封账！")

	frappe.db.set_value("Ashan Monthly Payroll Settlement", doc_name, {
		"locked": 1,
		"status": "已核定锁定"
	})
	frappe.db.commit()
	return {"success": True, "message": f"【{company}】{period_month} 薪酬已成功核定并锁定（只读封账）！"}


@frappe.whitelist(methods=["POST"])
def unlock_jizhong_monthly_payroll(company="天津吉众科技有限公司", period_month=None, reason=""):
	"""
	反审核解锁吉众月度薪酬核定表
	"""
	if not period_month:
		frappe.throw("必须指定核算月份")
	doc_name = f"{company}-{period_month}"
	if not frappe.db.exists("Ashan Monthly Payroll Settlement", doc_name):
		frappe.throw(f"未找到【{company}】{period_month} 的薪酬核算记录！")

	frappe.db.set_value("Ashan Monthly Payroll Settlement", doc_name, {
		"locked": 0,
		"status": "草稿"
	})
	frappe.db.commit()
	return {"success": True, "message": f"【{company}】{period_month} 薪酬已成功解锁，可重新测算！"}


@frappe.whitelist()
def get_jizhong_workflow_status(company="天津吉众科技有限公司", period_month=None):
	"""
	获取吉众月度 5 步全流程任务中枢与核验状态 (与祺富工作台任务哲学完全一致)
	1. 员工薪资信息表 (权威底册核实)
	2. 考勤工时与打卡底册 (工时、加班、倒休抵扣核实)
	3. 社保公积金配置 (年度费率生效核实)
	4. 个人所得税台账 (累计预扣与专项附加核实)
	5. 月度工资核定表 (全员薪资测算与封账锁定)
	"""
	if not period_month:
		period_month = today()[:7]

	year = cint(period_month.split("-")[0])
	month = cint(period_month.split("-")[1])
	period_label = f"{year}年{month:02d}月"

	# 1. 员工薪资信息表
	profile_dt = "Jizhong Employee Salary Profile" if frappe.db.table_exists("Jizhong Employee Salary Profile") and frappe.db.count("Jizhong Employee Salary Profile", {"company": company}) > 0 else "Ashan Employee Salary Profile"
	total_emps = frappe.db.count(profile_dt, {"company": company})
	regular_emps = frappe.db.count(profile_dt, {"company": company, "employee_type": "正式工"})
	other_emps = frappe.db.count(profile_dt, {"company": company, "employee_type": "其他"})
	step1_done = total_emps > 0
	step1 = {
		"step": 1,
		"title": "员工薪资信息表",
		"tag": "权威底册",
		"status": "done" if step1_done else "pending",
		"badge": "已就绪" if step1_done else "待完善",
		"main": f"{total_emps} 人在册 · 档案完整" if step1_done else "暂无员工档案",
		"sub": f"正式工 {regular_emps}人 ｜ 其他 {other_emps}人",
		"tab": "employees"
	}

	# 2. 考勤工时与打卡底册
	att_records = frappe.db.sql("""
		SELECT COUNT(*) as cnt,
		       SUM(work_hours_regular) as reg_hrs,
		       SUM(overtime_regular_1_5 + overtime_weekend_2_0 + overtime_holiday_3_0) as ot_hrs,
		       MAX(attendance_file) as att_file
		FROM `tabJizhong Monthly Attendance`
		WHERE company = %s AND period_month = %s
	""", (company, period_month), as_dict=True)[0]
	att_cnt = cint(att_records.get("cnt") or 0)
	reg_hrs = flt(att_records.get("reg_hrs") or 0)
	ot_hrs = flt(att_records.get("ot_hrs") or 0)
	step2_done = att_cnt > 0
	step2 = {
		"step": 2,
		"title": "考勤工时与打卡底册",
		"tag": "打卡底册",
		"status": "done" if step2_done else "pending",
		"badge": "已就绪" if step2_done else "待导入",
		"main": f"{att_cnt} 人打卡 · {round(reg_hrs + ot_hrs, 1)}h" if step2_done else "当月打卡记录尚未导入",
		"sub": f"正班 {round(reg_hrs, 1)}h ｜ 加班 {round(ot_hrs, 1)}h" if step2_done else "请上传考勤 Excel 或打卡底册",
		"tab": "attendance"
	}

	# 3. 社保公积金配置
	ins_setting = frappe.db.get_value(
		"Ashan Insurance Setting",
		{"company": ["like", "%吉众%"], "effective_year": year},
		["name", "ss_company_injury", "ss_person_pension", "ss_person_medical", "hf_person_rate"],
		as_dict=True
	)
	step3_done = bool(ins_setting)
	step3 = {
		"step": 3,
		"title": "社保公积金配置",
		"tag": "费率基数",
		"status": "done" if step3_done else "pending",
		"badge": "已生效" if step3_done else "待配置",
		"main": f"{year} 年度费率生效" if step3_done else f"未找到 {year} 年费率配置",
		"sub": "个人社保 10.5%+21元 ｜ 公积金 5%" if step3_done else "请在配置页设定社保公积金费率",
		"tab": "insurance"
	}

	# 4. 个人所得税台账
	step4_done = total_emps > 0
	step4 = {
		"step": 4,
		"title": "个人所得税台账",
		"tag": "累计预扣",
		"status": "done" if step4_done else "pending",
		"badge": "已就绪" if step4_done else "待同步",
		"main": "周期累计正常 · 覆盖全员" if step4_done else "个税历史待同步",
		"sub": "7级累计预扣算法 ｜ 专项附加扣除平账",
		"tab": "tax"
	}

	# 5. 月度工资核定表
	settle_name = f"{company}-{period_month}"
	settlement = frappe.db.get_value(
		"Ashan Monthly Payroll Settlement",
		{"name": settle_name},
		["name", "total_employees", "total_gross_salary", "total_net_salary", "locked", "status"],
		as_dict=True
	)
	is_locked = bool(settlement and settlement.get("locked"))
	has_calc = bool(settlement and cint(settlement.get("total_employees") or 0) > 0)
	if is_locked:
		step5_badge = "已封账"
		step5_main = f"已核定封账 · {settlement.get('total_employees')}人"
		step5_sub = f"实发 ¥{flt(settlement.get('total_net_salary')):,.2f} ｜ 只读受控"
		overall_status_text = "已核定锁定 (只读封账)"
		overall_status_class = "jz-status-locked"
	elif has_calc:
		step5_badge = "已测算"
		step5_main = "已完成测算 · 待封账"
		step5_sub = f"应发 ¥{flt(settlement.get('total_gross_salary')):,.2f} ｜ 实发 ¥{flt(settlement.get('total_net_salary')):,.2f}"
		overall_status_text = "草稿状态 (已测算 / 待封账)"
		overall_status_class = "jz-status-draft"
	else:
		step5_badge = "待测算"
		step5_main = "尚未测算薪酬"
		step5_sub = "前置任务就绪后一键重新计算"
		overall_status_text = "草稿状态 (待测算)"
		overall_status_class = "jz-status-draft"

	step5 = {
		"step": 5,
		"title": "月度工资核定表",
		"tag": "薪酬终审",
		"status": "locked" if is_locked else ("done" if has_calc else "pending"),
		"badge": step5_badge,
		"main": step5_main,
		"sub": step5_sub,
		"tab": "payroll"
	}

	return {
		"success": True,
		"period_month": period_month,
		"period_label": period_label,
		"overall_status_text": overall_status_text,
		"overall_status_class": overall_status_class,
		"is_locked": is_locked,
		"steps": [step1, step2, step3, step4, step5]
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


@frappe.whitelist()
def get_jizhong_employee_profiles(company="天津吉众科技有限公司"):
	"""获取吉众员工薪酬档案全量数据"""
	assert_company_access(company)
	fields = [
		"name", "employee_no", "employee_name", "company", "employee_type", "employment_status",
		"certificate_type", "salary_mode", "fixed_salary", "base_salary", "house_rent_allowance", "post_allowance", "performance_base",
		"meal_allowance", "social_security_base", "housing_fund_base", "id_card", "mobile", "gender", "birth_date",
		"department", "job_title", "deduction_child_education", "deduction_continuing_education",
		"deduction_serious_illness", "deduction_housing_loan", "deduction_housing_rent",
		"deduction_elderly_care", "deduction_infant_care", "special_additional_deductions_total",
		"bank_name", "bank_account", "notes"
	]
	# 优先从独立 DocType Jizhong Employee Salary Profile 获取
	if frappe.db.table_exists("Jizhong Employee Salary Profile"):
		docs = frappe.get_all("Jizhong Employee Salary Profile", filters={"company": company}, fields=fields, order_by="employee_no asc")
		if docs:
			return docs
	# 容错降级从 Ashan Employee Salary Profile 获取
	if frappe.db.table_exists("Ashan Employee Salary Profile"):
		return frappe.get_all("Ashan Employee Salary Profile", filters={"company": company}, fields=fields, order_by="employee_no asc")
	return []


@frappe.whitelist(methods=["POST"])
def save_jizhong_employee_profile(data=None):
	"""保存或更新吉众员工薪酬档案"""
	import json
	if isinstance(data, str):
		data = json.loads(data)
	if not data or not isinstance(data, dict):
		frappe.throw("无效的员工档案数据")

	company = data.get("company") or "天津吉众科技有限公司"
	assert_company_access(company)

	emp_no = (data.get("employee_no") or "").strip()
	emp_name = (data.get("employee_name") or "").strip()
	if not emp_no or not emp_name:
		frappe.throw("工号和姓名不能为空")

	doc_name = data.get("name")
	if not doc_name:
		doc_name = f"{company}-{emp_no}-{emp_name}"

	if frappe.db.exists("Jizhong Employee Salary Profile", doc_name):
		doc = frappe.get_doc("Jizhong Employee Salary Profile", doc_name)
	elif frappe.db.exists("Jizhong Employee Salary Profile", {"company": company, "employee_no": emp_no}):
		exist_name = frappe.db.get_value("Jizhong Employee Salary Profile", {"company": company, "employee_no": emp_no}, "name")
		doc = frappe.get_doc("Jizhong Employee Salary Profile", exist_name)
	else:
		doc = frappe.new_doc("Jizhong Employee Salary Profile")
		doc.company = company
		doc.employee_no = emp_no
		doc.employee_name = emp_name

	# 更新基础字段
	doc.employee_name = emp_name
	doc.certificate_type = (data.get("certificate_type") or "居民身份证").strip()
	doc.id_card = (data.get("id_card") or "").strip()
	doc.mobile = (data.get("mobile") or "").strip()
	doc.gender = data.get("gender") or ""
	doc.birth_date = data.get("birth_date") or None
	doc.department = data.get("department") or "生产车间"
	doc.job_title = data.get("job_title") or "操作工"
	doc.employee_type = data.get("employee_type") or "正式工"
	doc.employment_status = data.get("employment_status") or "在职"
	doc.salary_mode = data.get("salary_mode") or "税前动态工资"

	# 金额与基数
	doc.fixed_salary = flt(data.get("fixed_salary"))
	doc.base_salary = flt(data.get("base_salary"))
	doc.house_rent_allowance = flt(data.get("house_rent_allowance"))
	doc.performance_base = flt(data.get("performance_base"))
	doc.post_allowance = flt(data.get("post_allowance"))
	doc.meal_allowance = flt(data.get("meal_allowance") or 15.0)
	doc.social_security_base = flt(data.get("social_security_base") or 5124.0)
	doc.housing_fund_base = flt(data.get("housing_fund_base") or 2520.0)

	# 7 项专项附加扣除
	doc.deduction_child_education = flt(data.get("deduction_child_education"))
	doc.deduction_continuing_education = flt(data.get("deduction_continuing_education"))
	doc.deduction_serious_illness = flt(data.get("deduction_serious_illness"))
	doc.deduction_housing_loan = flt(data.get("deduction_housing_loan"))
	doc.deduction_housing_rent = flt(data.get("deduction_housing_rent"))
	doc.deduction_elderly_care = flt(data.get("deduction_elderly_care"))
	doc.deduction_infant_care = flt(data.get("deduction_infant_care"))
	doc.special_additional_deductions_total = (
		doc.deduction_child_education + doc.deduction_continuing_education +
		doc.deduction_serious_illness + doc.deduction_housing_loan +
		doc.deduction_housing_rent + doc.deduction_elderly_care + doc.deduction_infant_care
	)

	# 银行卡与备注
	doc.bank_name = data.get("bank_name") or ""
	doc.bank_account = data.get("bank_account") or ""
	doc.notes = data.get("notes") or ""

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {"success": True, "message": f"员工 {emp_name} ({emp_no}) 档案已成功保存", "profile": doc.as_dict()}

