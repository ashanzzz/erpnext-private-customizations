# -*- coding: utf-8 -*-
# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe

def after_migrate():
	"""
	系统迁移后初始化标准与自定义业务角色，并清理废弃角色
	"""
	cleanup_deprecated_roles()
	create_custom_roles()
	setup_doctype_and_page_permissions()
	setup_vehicle_custom_fields()

def setup_vehicle_custom_fields():
	"""
	为 Vehicle 标准 DocType 扩展业务状态（启用/封存）、主要驾驶员以及默认油品型号
	"""
	custom_fields = {
		"Vehicle": [
			{
				"fieldname": "custom_vehicle_status",
				"label": "车辆状态",
				"fieldtype": "Select",
				"options": "正常在用\n封存停用",
				"default": "正常在用",
				"insert_after": "license_plate",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"description": "封存停用后将从油卡加油录入、高速费入池选择中自动隐藏"
			},
			{
				"fieldname": "custom_primary_driver",
				"label": "主要驾驶员",
				"fieldtype": "Data",
				"insert_after": "model",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"description": "车辆主要使用人/驾驶员姓名，与高速费台账联动同步"
			},
			{
				"fieldname": "custom_vehicle_remark",
				"label": "车辆备注/用途",
				"fieldtype": "Data",
				"insert_after": "custom_primary_driver",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"description": "如：应急车、专职配送等，将在台账与选项卡中联动显示"
			},
			{
				"fieldname": "custom_default_fuel_grade",
				"label": "默认/上次加油油号",
				"fieldtype": "Select",
				"options": "0# 柴油\n-10# 柴油\n92# 汽油\n95# 汽油\n98# 汽油\n纯电动\n天然气\n其他",
				"insert_after": "fuel_type",
				"in_list_view": 1,
				"description": "系统自动记忆该车上次加油油品型号，下次加油录入时默认自动带出，也可手动修改"
			}
		]
	}

	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	create_custom_fields(custom_fields, ignore_validate=True)

	# 初始化现有车辆数据
	vehicles = frappe.get_all("Vehicle", fields=["name", "fuel_type", "custom_vehicle_status", "custom_default_fuel_grade", "custom_primary_driver"])
	for v in vehicles:
		v_doc = frappe.get_doc("Vehicle", v.name)
		changed = False
		if not v_doc.custom_vehicle_status:
			v_doc.custom_vehicle_status = "正常在用"
			changed = True
		if not v_doc.custom_default_fuel_grade:
			f_type = (v_doc.fuel_type or "").lower()
			if "diesel" in f_type or "柴油" in f_type:
				v_doc.custom_default_fuel_grade = "0# 柴油"
			elif "petrol" in f_type or "汽油" in f_type:
				v_doc.custom_default_fuel_grade = "92# 汽油"
			elif "electric" in f_type or "纯电" in f_type:
				v_doc.custom_default_fuel_grade = "纯电动"
			elif "gas" in f_type or "天然气" in f_type:
				v_doc.custom_default_fuel_grade = "天然气"
			else:
				v_doc.custom_default_fuel_grade = "0# 柴油"
			changed = True
		# 从 Vehicle Toll Config 同步现有主要驾驶员与备注用途
		if frappe.db.exists("Vehicle Toll Config", v.name):
			t_cfg = frappe.get_doc("Vehicle Toll Config", v.name)
			if not v_doc.custom_primary_driver and t_cfg.primary_user:
				v_doc.custom_primary_driver = t_cfg.primary_user
				changed = True
			if not getattr(v_doc, "custom_vehicle_remark", None):
				d_name = t_cfg.display_name or ""
				if "(" in d_name and ")" in d_name:
					remark_extracted = d_name.split("(")[-1].split(")")[0].strip()
					if remark_extracted:
						v_doc.custom_vehicle_remark = remark_extracted
						changed = True
				elif "（" in d_name and "）" in d_name:
					remark_extracted = d_name.split("（")[-1].split("）")[0].strip()
					if remark_extracted:
						v_doc.custom_vehicle_remark = remark_extracted
						changed = True
		if changed:
			v_doc.save(ignore_permissions=True)

	frappe.db.commit()



def cleanup_deprecated_roles():
	"""
	删除已废弃的业务授权人角色（管理员自身原生拥有全部授权与审核权限）
	"""
	for deprecated_role in ["Authorizer", "业务授权人"]:
		if frappe.db.exists("Role", deprecated_role):
			try:
				frappe.delete_doc("Role", deprecated_role, ignore_permissions=True, force=True)
				frappe.logger("setup").info(f"Removed Deprecated Role: {deprecated_role}")
			except Exception as e:
				frappe.logger("setup").error(f"Failed to remove role {deprecated_role}: {e}")

def create_custom_roles():
	"""
	自动创建业务拓展专用的管理员与操作员角色
	"""
	roles = [
		{
			"role_name": "Oil Card Manager",
			"description": "油卡综合台账管理员：具备月度核定与直接解锁权限，可查看百公里油耗、行驶里程与开票状态，具备单据删除与调整特权授权。"
		},
		{
			"role_name": "Oil Card Operator",
			"description": "油卡操作员：具备加油录入、充值录入、新建车辆、本月核定与申请取消核定权限。"
		},
		{
			"role_name": "油卡管理员",
			"description": "油卡综合台账管理员（中文别名角色）"
		},
		{
			"role_name": "油卡操作员",
			"description": "油卡操作员（中文别名角色）"
		}
	]

	for r in roles:
		if not frappe.db.exists("Role", r["role_name"]):
			doc = frappe.new_doc("Role")
			doc.role_name = r["role_name"]
			doc.description = r["description"]
			doc.desk_access = 1
			doc.insert(ignore_permissions=True)
			frappe.logger("setup").info(f"Created Role: {r['role_name']}")

	frappe.db.commit()

def setup_doctype_and_page_permissions():
	"""
	为所有前台角色配置核心 UI 单据（Page、Workspace、Sidebar）以及油卡模块 DocType 与 Page 权限
	"""
	# 1. 核心前台 UI 渲染所必需的基础单据读取权限
	core_ui_doctypes = [
		"Page",
		"Workspace",
		"Workspace Sidebar",
		"Workspace Sidebar Item",
		"Dashboard Chart",
		"Number Card"
	]
	ui_roles = ["System Manager", "Desk User", "All", "Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"]
	for udt in core_ui_doctypes:
		if not frappe.db.exists("DocType", udt):
			continue
		for role in ui_roles:
			existing = frappe.db.get_value("Custom DocPerm", {"parent": udt, "role": role, "permlevel": 0}, "name")
			if existing:
				dp = frappe.get_doc("Custom DocPerm", existing)
			else:
				dp = frappe.new_doc("Custom DocPerm")
				dp.parent = udt
				dp.parenttype = "DocType"
				dp.parentfield = "permissions"
				dp.role = role
				dp.permlevel = 0
			dp.read = 1
			dp.select = 1
			dp.export = 1
			if role == "System Manager":
				dp.write = 1
				dp.create = 1
				dp.delete = 1
			dp.save(ignore_permissions=True)

	# 2. 油卡与车用油、高速费业务 DocType 读写权限
	oil_doctypes = [
		"Oil Card",
		"Oil Card Recharge",
		"Oil Card Refuel Log",
		"Oil Card Invoice Batch",
		"Oil Card Invoice Batch Item",
		"Oil Card Monthly Closing",
		"Vehicle Toll Config",
		"Vehicle Toll Monthly Sheet",
		"Vehicle Toll Deposit",
		"Vehicle",
		"Environmental Compliance Item",
		"Special Equipment",
		"Special Equipment Inspection",
		"Special Equipment Annual Inspection"
	]
	target_roles = ["System Manager", "Fleet Manager", "Oil Card Manager", "油卡管理员", "Oil Card Operator", "油卡操作员", "Desk User", "All"]

	for dt in oil_doctypes:
		if not frappe.db.exists("DocType", dt):
			continue
		for role in target_roles:
			is_mgr = role in ["System Manager", "Fleet Manager", "Oil Card Manager", "油卡管理员"]
			existing = frappe.db.get_value("Custom DocPerm", {"parent": dt, "role": role, "permlevel": 0}, "name")
			if existing:
				dp = frappe.get_doc("Custom DocPerm", existing)
			else:
				dp = frappe.new_doc("Custom DocPerm")
				dp.parent = dt
				dp.parenttype = "DocType"
				dp.parentfield = "permissions"
				dp.role = role
				dp.permlevel = 0

			dp.read = 1
			dp.report = 1
			dp.export = 1

			# 油卡档案（Oil Card）：操作员仅可读取选择，严禁新建、修改和删除；油卡管理员与系统管理员具备全部原始单据管理权限
			if dt == "Oil Card":
				dp.create = 1 if is_mgr else 0
				dp.write = 1 if is_mgr else 0
				dp.delete = 1 if is_mgr else 0
			else:
				dp.create = 1
				dp.write = 1
				dp.delete = 1 if is_mgr else 0

			dp.save(ignore_permissions=True)

	# 3. 确保 Pages 拥有这些角色的访问权限
	for page_name in ["oil-card-ledger", "vehicle-toll-ledger", "special-equipment-center", "environmental-management"]:
		if frappe.db.exists("Page", page_name):
			page_doc = frappe.get_doc("Page", page_name)
			existing_roles = {r.role for r in page_doc.roles}
			modified = False
			for role in ["System Manager", "Fleet Manager", "Oil Card Manager", "油卡管理员", "Oil Card Operator", "油卡操作员", "Desk User", "All"]:
				if role not in existing_roles:
					page_doc.append("roles", {"role": role})
					modified = True
			if modified:
				page_doc.save(ignore_permissions=True)

	frappe.db.commit()




