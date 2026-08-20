# Copyright (c) 2026, Ashan CN Procurement
import json
import frappe

def check_emp_counts():
	qifu = frappe.get_all("Ashan Employee Salary Profile", filters={"company": "天津祺富机械加工有限公司"}, fields=["name", "employee_no", "employee_name", "employee_type", "fixed_salary", "salary_mode"])
	jizhong = frappe.get_all("Ashan Employee Salary Profile", filters={"company": "天津吉众机电设备有限公司"}, fields=["name", "employee_no", "employee_name", "employee_type", "fixed_salary", "salary_mode"])
	print("Qifu count:", len(qifu), "Sample:", qifu[:2] if qifu else [])
	print("Jizhong count:", len(jizhong), "Sample:", jizhong[:2] if jizhong else [])
	return True


def fix_and_sync_sidebar():
	# 准确的链接配置
	items = [
		{"label": "我的业务 (总控主页)", "type": "Link", "link_type": "Workspace", "link_to": "Home", "icon": "home"},
		
		# 物业与租赁
		{"label": "🏢 物业与租赁", "type": "Section Break", "link_type": "DocType", "icon": "building", "collapsible": 1},
		{"label": "水电费月结工作台*", "type": "Link", "link_type": "Page", "link_to": "property-settlement-workbench", "child": 1},
		{"label": "房租与物业费工作台*", "type": "Link", "link_type": "DocType", "link_to": "Property Lease", "child": 1},
		{"label": "收费标准版本", "type": "Link", "link_type": "DocType", "link_to": "Property Charge Rate", "child": 1},
		{"label": "水电表配置", "type": "Link", "link_type": "DocType", "link_to": "Utility Meter", "child": 1},
		{"label": "月结历史总账", "type": "Link", "link_type": "DocType", "link_to": "Property Monthly Settlement", "child": 1},
		
		# 车辆和车用油管理
		{"label": "🚗 车辆和车用油管理", "type": "Section Break", "link_type": "DocType", "icon": "truck", "collapsible": 1},
		{"label": "油卡综合台账明细台*", "type": "Link", "link_type": "Page", "link_to": "oil-card-ledger", "child": 1},
		{"label": "高速费月度台账*", "type": "Link", "link_type": "DocType", "link_to": "Highway Toll Ledger", "child": 1},
		{"label": "车辆档案", "type": "Link", "link_type": "DocType", "link_to": "Vehicle Fuel Settings", "child": 1},
		{"label": "油卡档案", "type": "Link", "link_type": "DocType", "link_to": "Oil Card", "child": 1},
		{"label": "油卡充值流水", "type": "Link", "link_type": "DocType", "link_to": "Oil Card Recharge", "child": 1},
		{"label": "加油与能耗记录", "type": "Link", "link_type": "DocType", "link_to": "Oil Card Refuel Log", "child": 1},
		{"label": "油票批量录入", "type": "Link", "link_type": "DocType", "link_to": "Oil Card Invoice Batch", "child": 1},
		
		# 财税与发票中心
		{"label": "🏛️ 财税与发票中心", "type": "Section Break", "link_type": "DocType", "icon": "credit-card", "collapsible": 1},
		{"label": "税局发票资料库*", "type": "Link", "link_type": "Page", "link_to": "tax-invoice-center", "child": 1},
		{"label": "订餐与工作餐月结台*", "type": "Link", "link_type": "Page", "link_to": "meal-settlement-workbench", "child": 1},
		{"label": "报销申请", "type": "Link", "link_type": "DocType", "link_to": "Reimbursement Request", "child": 1},
		{"label": "采购发票 (ERP)", "type": "Link", "link_type": "DocType", "link_to": "Purchase Invoice", "child": 1},
		{"label": "税局发票档案", "type": "Link", "link_type": "DocType", "link_to": "Tax Invoice", "child": 1},
		{"label": "发票导入批次", "type": "Link", "link_type": "DocType", "link_to": "Tax Invoice Import Batch", "child": 1},
		{"label": "发票匹配设置", "type": "Link", "link_type": "DocType", "link_to": "Tax Invoice Settings", "child": 1},

		# 人事薪酬与用工
		{"label": "👥 人事薪酬与用工", "type": "Section Break", "link_type": "DocType", "icon": "users", "collapsible": 1},
		{"label": "祺富人事薪酬工作台*", "type": "Link", "link_type": "Page", "link_to": "qifu-hr-salary-workbench", "child": 1},
		{"label": "吉众人事薪酬工作台*", "type": "Link", "link_type": "Page", "link_to": "jizhong-hr-salary-workbench", "child": 1},
		{"label": "月度出勤打卡记录", "type": "Link", "link_type": "DocType", "link_to": "Ashan Monthly Attendance", "child": 1},
		{"label": "月度薪酬核定总表", "type": "Link", "link_type": "DocType", "link_to": "Ashan Monthly Payroll Settlement", "child": 1},
		{"label": "社保公积金设置", "type": "Link", "link_type": "DocType", "link_to": "Ashan Insurance Setting", "child": 1},
		{"label": "法定日历与节假日", "type": "Link", "link_type": "DocType", "link_to": "Ashan Holiday Calendar", "child": 1},

		# 企业合规中心
		{"label": "🛡️ 企业合规中心", "type": "Section Break", "link_type": "DocType", "icon": "shield", "collapsible": 1},
		{"label": "特种设备档案*", "type": "Link", "link_type": "DocType", "link_to": "Special Equipment", "child": 1},
		{"label": "法定检验记录", "type": "Link", "link_type": "DocType", "link_to": "Special Equipment Inspection", "child": 1},
		{"label": "年度检查记录", "type": "Link", "link_type": "DocType", "link_to": "Special Equipment Annual Inspection", "child": 1},
		{"label": "员工证书资质", "type": "Link", "link_type": "DocType", "link_to": "Employee Certificate Item", "child": 1}
	]

	# 校验每一个 DocType 和 Page 是否在数据库存在
	valid_items = []
	for it in items:
		lt = it.get("link_type")
		to = it.get("link_to")
		if lt == "DocType" and to and not frappe.db.exists("DocType", to):
			print(f"Skipping non-existent DocType: {to}")
			continue
		if lt == "Page" and to and not frappe.db.exists("Page", to):
			print(f"Skipping non-existent Page: {to}")
			continue
		if lt == "Workspace" and to and not frappe.db.exists("Workspace", to):
			print(f"Skipping non-existent Workspace: {to}")
			continue
		valid_items.append(it)

	for sb_name in ["Home", "My Business", "ashan_cn_procurement"]:
		frappe.db.delete("Workspace Sidebar Item", {"parent": sb_name})
		if frappe.db.exists("Workspace Sidebar", sb_name):
			doc = frappe.get_doc("Workspace Sidebar", sb_name)
		else:
			doc = frappe.new_doc("Workspace Sidebar")
			doc.name = sb_name
			doc.title = sb_name
			doc.module = "Ashan CN Procurement"
			doc.app = "ashan_cn_procurement"

		doc.items = []
		for it in valid_items:
			doc.append("items", {
				"label": it.get("label"),
				"link_type": it.get("link_type", "DocType"),
				"type": it.get("type", "Link"),
				"link_to": it.get("link_to"),
				"icon": it.get("icon"),
				"child": it.get("child", 0),
				"collapsible": it.get("collapsible", 0),
				"indent": it.get("indent", 0),
				"keep_closed": it.get("keep_closed", 0),
				"show_arrow": it.get("show_arrow", 0)
			})
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
		print(f"Synced {sb_name} with {len(doc.items)} valid items!")

	frappe.db.commit()
	return True
