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
	为油卡操作员和管理员配置 DocType 与 Page 权限
	"""
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
			if not frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role, "permlevel": 0}):
				try:
					dp = frappe.new_doc("Custom DocPerm")
					dp.parent = dt
					dp.parenttype = "DocType"
					dp.parentfield = "permissions"
					dp.role = role
					dp.permlevel = 0
					dp.read = 1
					dp.write = 1
					dp.create = 1
					dp.delete = 1 if "Manager" in role or "管理员" in role else 0
					dp.report = 1
					dp.export = 1
					dp.insert(ignore_permissions=True)
				except Exception as e:
					frappe.logger("setup").warning(f"Error adding Custom DocPerm for {dt} / {role}: {e}")

	# 确保 Page oil-card-ledger 拥有这些角色的访问权限
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


