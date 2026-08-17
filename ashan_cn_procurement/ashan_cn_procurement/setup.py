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
	ui_roles = ["Desk User", "All", "Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"]
	for udt in core_ui_doctypes:
		if not frappe.db.exists("DocType", udt):
			continue
		for role in ui_roles:
			if not frappe.db.exists("Custom DocPerm", {"parent": udt, "role": role, "permlevel": 0}):
				try:
					dp = frappe.new_doc("Custom DocPerm")
					dp.parent = udt
					dp.parenttype = "DocType"
					dp.parentfield = "permissions"
					dp.role = role
					dp.permlevel = 0
					dp.read = 1
					dp.select = 1
					dp.export = 1
					dp.insert(ignore_permissions=True)
				except Exception as e:
					frappe.logger("setup").warning(f"Error adding Custom DocPerm for {udt} / {role}: {e}")

	# 2. 油卡业务 DocType 读写权限
	oil_doctypes = [
		"Oil Card",
		"Oil Card Refuel Log",
		"Oil Card Recharge Log",
		"Oil Card Monthly Closing",
		"Vehicle Archive"
	]
	target_roles = ["Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"]

	for dt in oil_doctypes:
		if not frappe.db.exists("DocType", dt):
			continue
		for role in target_roles:
			is_mgr = "Manager" in role or "管理员" in role
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

			# 油卡档案（Oil Card）：油卡操作员与油卡管理员均严禁新建、修改和删除，仅保留读取权限
			if dt == "Oil Card":
				dp.create = 0
				dp.write = 0
				dp.delete = 0
			else:
				dp.create = 1
				dp.write = 1
				dp.delete = 1 if is_mgr else 0

			dp.save(ignore_permissions=True)

	# 3. 确保 Page oil-card-ledger 拥有这些角色的访问权限
	if frappe.db.exists("Page", "oil-card-ledger"):
		page_doc = frappe.get_doc("Page", "oil-card-ledger")
		existing_roles = {r.role for r in page_doc.roles}
		modified = False
		for role in target_roles:
			if role not in existing_roles:
				page_doc.append("roles", {"role": role})
				modified = True
		if modified:
			page_doc.save(ignore_permissions=True)

	frappe.db.commit()



