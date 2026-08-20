import os
import sys
import json

base_doctype_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\ashan_cn_procurement\doctype"

doctypes = [
    {
        "name": "Ashan Holiday Calendar",
        "module": "Ashan CN Procurement",
        "custom": 0,
        "istable": 0,
        "issingle": 0,
        "track_changes": 1,
        "autoname": "field:calendar_date",
        "fields": [
            {"fieldname": "calendar_date", "fieldtype": "Date", "label": "日期", "reqd": 1, "in_list_view": 1, "unique": 1},
            {"fieldname": "year", "fieldtype": "Int", "label": "年份", "reqd": 1, "in_list_view": 1},
            {"fieldname": "month", "fieldtype": "Int", "label": "月份", "reqd": 1},
            {"fieldname": "day_type", "fieldtype": "Select", "label": "日期属性", "options": "工作日\n周末日\n调休日\n调班日\n法定节假日", "reqd": 1, "in_list_view": 1},
            {"fieldname": "is_workday", "fieldtype": "Check", "label": "是否出勤工作日", "in_list_view": 1},
            {"fieldname": "is_legal_holiday", "fieldtype": "Check", "label": "是否法定节假日", "in_list_view": 1},
            {"fieldname": "is_shift_off", "fieldtype": "Check", "label": "是否调休"},
            {"fieldname": "is_shift_work", "fieldtype": "Check", "label": "是否调班补班"},
            {"fieldname": "holiday_name", "fieldtype": "Data", "label": "节日名称", "in_list_view": 1},
            {"fieldname": "remark", "fieldtype": "Small Text", "label": "备注说明"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}, {"role": "All", "read": 1}]
    },
    {
        "name": "Ashan Employee Salary Profile",
        "module": "Ashan CN Procurement",
        "custom": 0,
        "istable": 0,
        "issingle": 0,
        "track_changes": 1,
        "autoname": "format:{company}-{employee_no}-{employee_name}",
        "fields": [
            {"fieldname": "employee_no", "fieldtype": "Data", "label": "工号", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "fieldtype": "Data", "label": "姓名", "reqd": 1, "in_list_view": 1},
            {"fieldname": "company", "fieldtype": "Link", "options": "Company", "label": "所属公司", "reqd": 1, "in_list_view": 1},
            {"fieldname": "id_card", "fieldtype": "Data", "label": "身份证号", "in_list_view": 1},
            {"fieldname": "mobile", "fieldtype": "Data", "label": "手机号"},
            {"fieldname": "employee_type", "fieldtype": "Select", "label": "人员类型", "options": "正式工\n临时工\n退休返聘\n实习生", "default": "正式工", "in_list_view": 1},
            {"fieldname": "employment_status", "fieldtype": "Select", "label": "在职状态", "options": "在职\n离职\n休假", "default": "在职", "in_list_view": 1},
            {"fieldname": "is_insured", "fieldtype": "Check", "label": "是否参保", "default": "1"},
            {"fieldname": "salary_mode", "fieldtype": "Select", "label": "计薪方式", "options": "税前动态工资\n税后管理工资", "default": "税前动态工资", "reqd": 1, "in_list_view": 1},
            {"fieldname": "fixed_net_salary", "fieldtype": "Currency", "label": "约定税后实发工资 (元)"},
            {"fieldname": "base_salary", "fieldtype": "Currency", "label": "基本工资 (元)", "in_list_view": 1},
            {"fieldname": "base_subsidy", "fieldtype": "Currency", "label": "基本补贴 (元)"},
            {"fieldname": "performance_bonus_base", "fieldtype": "Currency", "label": "绩效奖金基准 (元)"},
            {"fieldname": "position_allowance", "fieldtype": "Currency", "label": "职位津贴 (元)"},
            {"fieldname": "meal_unit_price", "fieldtype": "Currency", "label": "餐补单价 (元/餐)", "default": "15"},
            {"fieldname": "social_security_base", "fieldtype": "Currency", "label": "社保缴费基数 (元)", "default": "5124"},
            {"fieldname": "housing_fund_base", "fieldtype": "Currency", "label": "公积金缴费基数 (元)", "default": "2520"},
            {"fieldname": "special_additional_deduction", "fieldtype": "Currency", "label": "个税专项附加扣除 (元/月)", "default": "0"},
            {"fieldname": "tax_exemption_monthly", "fieldtype": "Currency", "label": "个税起征点 (元/月)", "default": "5000"},
            {"fieldname": "bank_name", "fieldtype": "Data", "label": "开户行"},
            {"fieldname": "bank_account", "fieldtype": "Data", "label": "银行卡号"},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "备注说明"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}, {"role": "All", "read": 1}]
    },
    {
        "name": "Ashan Monthly Attendance",
        "module": "Ashan CN Procurement",
        "custom": 0,
        "istable": 0,
        "issingle": 0,
        "track_changes": 1,
        "autoname": "format:{company}-{period_month}-{employee_no}",
        "fields": [
            {"fieldname": "period_month", "fieldtype": "Data", "label": "考勤月份", "reqd": 1, "in_list_view": 1},
            {"fieldname": "company", "fieldtype": "Link", "options": "Company", "label": "所属公司", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_no", "fieldtype": "Data", "label": "工号", "reqd": 1, "in_list_view": 1},
            {"fieldname": "employee_name", "fieldtype": "Data", "label": "姓名", "reqd": 1, "in_list_view": 1},
            {"fieldname": "attendance_days", "fieldtype": "Float", "label": "整天出勤天数", "in_list_view": 1},
            {"fieldname": "work_hours_regular", "fieldtype": "Float", "label": "基本出勤工时 (h)", "in_list_view": 1},
            {"fieldname": "overtime_regular_1_5", "fieldtype": "Float", "label": "平日加班工时 1.5x (h)", "in_list_view": 1},
            {"fieldname": "overtime_weekend_2_0", "fieldtype": "Float", "label": "周末加班工时 2.0x (h)", "in_list_view": 1},
            {"fieldname": "overtime_holiday_3_0", "fieldtype": "Float", "label": "法定节假日加班工时 3.0x (h)", "in_list_view": 1},
            {"fieldname": "meal_count", "fieldtype": "Int", "label": "餐补次数 (次)", "in_list_view": 1},
            {"fieldname": "daily_records_json", "fieldtype": "Code", "options": "JSON", "label": "每日考勤打卡JSON明细"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}, {"role": "All", "read": 1}]
    },
    {
        "name": "Ashan Payroll Item",
        "module": "Ashan CN Procurement",
        "custom": 0,
        "istable": 1,
        "issingle": 0,
        "fields": [
            {"fieldname": "employee_no", "fieldtype": "Data", "label": "工号", "in_list_view": 1},
            {"fieldname": "employee_name", "fieldtype": "Data", "label": "姓名", "in_list_view": 1},
            {"fieldname": "salary_mode", "fieldtype": "Select", "label": "计薪方式", "options": "税前动态工资\n税后管理工资", "in_list_view": 1},
            {"fieldname": "base_salary", "fieldtype": "Currency", "label": "基本工资标准"},
            {"fieldname": "attendance_days", "fieldtype": "Float", "label": "出勤天数"},
            {"fieldname": "work_hours_regular", "fieldtype": "Float", "label": "基本工时"},
            {"fieldname": "overtime_1_5", "fieldtype": "Float", "label": "平日加班1.5x"},
            {"fieldname": "overtime_2_0", "fieldtype": "Float", "label": "周末加班2.0x"},
            {"fieldname": "overtime_3_0", "fieldtype": "Float", "label": "节日加班3.0x"},
            {"fieldname": "salary_regular_hours", "fieldtype": "Currency", "label": "基本工时工资"},
            {"fieldname": "salary_overtime_1_5", "fieldtype": "Currency", "label": "平日加班费"},
            {"fieldname": "salary_overtime_2_0", "fieldtype": "Currency", "label": "周末加班费"},
            {"fieldname": "salary_overtime_3_0", "fieldtype": "Currency", "label": "节日加班费"},
            {"fieldname": "salary_base_subsidy", "fieldtype": "Currency", "label": "基本补贴"},
            {"fieldname": "salary_performance", "fieldtype": "Currency", "label": "绩效奖金"},
            {"fieldname": "salary_position_allowance", "fieldtype": "Currency", "label": "职位津贴"},
            {"fieldname": "salary_meal_subsidy", "fieldtype": "Currency", "label": "餐补金额"},
            {"fieldname": "salary_adjustment", "fieldtype": "Currency", "label": "工资调整"},
            {"fieldname": "gross_pay", "fieldtype": "Currency", "label": "应发薪资合计", "in_list_view": 1},
            {"fieldname": "social_security_base", "fieldtype": "Currency", "label": "社保基数"},
            {"fieldname": "ss_pension_p", "fieldtype": "Currency", "label": "养老p(8%)"},
            {"fieldname": "ss_medical_p", "fieldtype": "Currency", "label": "医疗p(2%)"},
            {"fieldname": "ss_unemployment_p", "fieldtype": "Currency", "label": "失业p(0.5%)"},
            {"fieldname": "ss_large_medical_p", "fieldtype": "Currency", "label": "大额医疗p(21)"},
            {"fieldname": "social_security_p", "fieldtype": "Currency", "label": "社保合计p"},
            {"fieldname": "housing_fund_base", "fieldtype": "Currency", "label": "公积金基数"},
            {"fieldname": "housing_fund_p", "fieldtype": "Currency", "label": "公积金p(5%)"},
            {"fieldname": "housing_fund_c", "fieldtype": "Currency", "label": "公积金c(5%)"},
            {"fieldname": "special_deduction_total", "fieldtype": "Currency", "label": "五险一金个人扣缴"},
            {"fieldname": "special_additional_deduction", "fieldtype": "Currency", "label": "专项附加扣除"},
            {"fieldname": "cum_gross_income", "fieldtype": "Currency", "label": "累计税前收入"},
            {"fieldname": "cum_tax_exemption", "fieldtype": "Currency", "label": "累计免征额"},
            {"fieldname": "cum_special_deduction", "fieldtype": "Currency", "label": "累计专项扣除"},
            {"fieldname": "cum_additional_deduction", "fieldtype": "Currency", "label": "累计附加扣除"},
            {"fieldname": "cum_taxable_income", "fieldtype": "Currency", "label": "累计应纳税所得额"},
            {"fieldname": "cum_tax_due", "fieldtype": "Currency", "label": "累计应缴税额"},
            {"fieldname": "cum_tax_paid_prior", "fieldtype": "Currency", "label": "以往已缴税额"},
            {"fieldname": "individual_tax", "fieldtype": "Currency", "label": "当月应扣个税", "in_list_view": 1},
            {"fieldname": "net_pay", "fieldtype": "Currency", "label": "实发薪资合计", "in_list_view": 1},
            {"fieldname": "cash_pay", "fieldtype": "Currency", "label": "现金发放工资"},
            {"fieldname": "bill_100", "fieldtype": "Int", "label": "100元张数"},
            {"fieldname": "bill_50", "fieldtype": "Int", "label": "50元张数"},
            {"fieldname": "bill_20", "fieldtype": "Int", "label": "20元张数"},
            {"fieldname": "bill_10", "fieldtype": "Int", "label": "10元张数"},
            {"fieldname": "bill_5", "fieldtype": "Int", "label": "5元张数"},
            {"fieldname": "bill_1", "fieldtype": "Int", "label": "1元张数"}
        ]
    },
    {
        "name": "Ashan Payroll Settlement",
        "module": "Ashan CN Procurement",
        "custom": 0,
        "istable": 0,
        "issingle": 0,
        "track_changes": 1,
        "autoname": "format:{company}-薪资月结-{period_month}",
        "fields": [
            {"fieldname": "period_month", "fieldtype": "Data", "label": "结算月份", "reqd": 1, "in_list_view": 1},
            {"fieldname": "company", "fieldtype": "Link", "options": "Company", "label": "所属公司", "reqd": 1, "in_list_view": 1},
            {"fieldname": "status", "fieldtype": "Select", "label": "状态", "options": "草稿\n已核定锁定\n已发放", "default": "草稿", "reqd": 1, "in_list_view": 1},
            {"fieldname": "full_work_days", "fieldtype": "Float", "label": "当月法定满勤天数", "default": "21"},
            {"fieldname": "full_work_hours", "fieldtype": "Float", "label": "动态满勤工时 (h)", "default": "168"},
            {"fieldname": "fixed_work_hours", "fieldtype": "Float", "label": "固定计薪工时 (h)", "default": "172"},
            {"fieldname": "total_gross_pay", "fieldtype": "Currency", "label": "应发薪资总额 (元)", "in_list_view": 1},
            {"fieldname": "total_social_security_p", "fieldtype": "Currency", "label": "社保个人扣缴总额 (元)"},
            {"fieldname": "total_housing_fund_p", "fieldtype": "Currency", "label": "公积金个人扣缴总额 (元)"},
            {"fieldname": "total_individual_tax", "fieldtype": "Currency", "label": "代扣个税总额 (元)", "in_list_view": 1},
            {"fieldname": "total_net_pay", "fieldtype": "Currency", "label": "实发薪资总额 (元)", "in_list_view": 1},
            {"fieldname": "total_company_cost", "fieldtype": "Currency", "label": "企业人工总成本 (元)"},
            {"fieldname": "locked_at", "fieldtype": "Datetime", "label": "核定锁定时间"},
            {"fieldname": "locked_by", "fieldtype": "Link", "options": "User", "label": "核定人"},
            {"fieldname": "settlement_items", "fieldtype": "Table", "options": "Ashan Payroll Item", "label": "薪资核算明细列表"}
        ],
        "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}, {"role": "All", "read": 1}]
    }
]

for dt in doctypes:
    folder_name = dt["name"].lower().replace(" ", "_")
    target_dir = os.path.join(base_doctype_dir, folder_name)
    os.makedirs(target_dir, exist_ok=True)

    # 1. JSON
    dt_json = {
        "name": dt["name"],
        "doctype": "DocType",
        "engine": "InnoDB",
        "module": dt["module"],
        "custom": dt["custom"],
        "istable": dt["istable"],
        "issingle": dt["issingle"],
        "track_changes": dt.get("track_changes", 0),
        "autoname": dt.get("autoname", ""),
        "fields": dt["fields"],
        "permissions": dt.get("permissions", [])
    }
    with open(os.path.join(target_dir, f"{folder_name}.json"), "w", encoding="utf-8") as f:
        json.dump(dt_json, f, ensure_ascii=False, indent=2)

    # 2. Python
    py_class_name = dt["name"].replace(" ", "")
    py_content = f"""# Copyright (c) 2026, Ashan and contributors
# For license information, please see license.txt

from frappe.model.document import Document

class {py_class_name}(Document):
\tpass
"""
    with open(os.path.join(target_dir, f"{folder_name}.py"), "w", encoding="utf-8") as f:
        f.write(py_content)

    # 3. JS (if not table)
    if not dt["istable"]:
        js_content = f"""// Copyright (c) 2026, Ashan and contributors
// For license information, please see license.txt

frappe.ui.form.on('{dt["name"]}', {{
\t// refresh(frm) {{}}
}});
"""
        with open(os.path.join(target_dir, f"{folder_name}.js"), "w", encoding="utf-8") as f:
            f.write(js_content)

    print(f"Created DocType: {dt['name']} in {target_dir}")
