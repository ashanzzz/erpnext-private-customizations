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
	setup_document_details_custom_fields()
	optimize_all_list_view_columns()
	setup_default_app_system_settings()
	migrate_property_lease_and_rates()
	cleanup_deprecated_sidebar_items()
	sync_all_workspace_sidebars()
	backfill_all_document_details()

def optimize_all_list_view_columns():
	"""
	通过 Property Setter 优化 5 大单据的列表页列展示，确保【单据明细】(custom_doc_details)
	以适当宽度、显著次序在 List View 中呈现
	"""
	try:
		from frappe.custom.doctype.property_setter.property_setter import make_property_setter

		# 1. Reimbursement Request
		make_property_setter("Reimbursement Request", "department", "in_list_view", "0", "Check", for_doctype=False, validate_fields_for_doctype=False)
		make_property_setter("Reimbursement Request", "company", "in_list_view", "0", "Check", for_doctype=False, validate_fields_for_doctype=False)
		make_property_setter("Reimbursement Request", "custom_doc_details", "in_list_view", "1", "Check", for_doctype=False, validate_fields_for_doctype=False)
		make_property_setter("Reimbursement Request", "custom_doc_details", "columns", "3", "Int", for_doctype=False, validate_fields_for_doctype=False)

		# 2. Material Request
		make_property_setter("Material Request", "custom_doc_details", "in_list_view", "1", "Check", for_doctype=False, validate_fields_for_doctype=False)
		make_property_setter("Material Request", "custom_doc_details", "columns", "3", "Int", for_doctype=False, validate_fields_for_doctype=False)

		# 3. Purchase Order
		make_property_setter("Purchase Order", "custom_doc_details", "in_list_view", "1", "Check", for_doctype=False, validate_fields_for_doctype=False)
		make_property_setter("Purchase Order", "custom_doc_details", "columns", "3", "Int", for_doctype=False, validate_fields_for_doctype=False)

		# 4. Purchase Receipt
		make_property_setter("Purchase Receipt", "custom_doc_details", "in_list_view", "1", "Check", for_doctype=False, validate_fields_for_doctype=False)
		make_property_setter("Purchase Receipt", "custom_doc_details", "columns", "3", "Int", for_doctype=False, validate_fields_for_doctype=False)

		# 5. Purchase Invoice
		make_property_setter("Purchase Invoice", "custom_doc_details", "in_list_view", "1", "Check", for_doctype=False, validate_fields_for_doctype=False)
		make_property_setter("Purchase Invoice", "custom_doc_details", "columns", "3", "Int", for_doctype=False, validate_fields_for_doctype=False)

		frappe.db.commit()
	except Exception as e:
		frappe.logger("setup").warning(f"Optimize list view columns failed: {e}")


def setup_document_details_custom_fields():
	"""
	为采购申请、采购订单、物资入库、采购发票、报销申请 5 大单据统一添加【单据明细】(custom_doc_details) 自定义字段
	"""
	custom_fields = {
		"Material Request": [
			{
				"fieldname": "custom_doc_details",
				"label": "单据明细",
				"fieldtype": "Small Text",
				"read_only": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"no_copy": 1,
				"insert_after": "material_request_type",
				"description": "系统根据物料明细子表自动汇总生成"
			}
		],
		"Purchase Order": [
			{
				"fieldname": "custom_doc_details",
				"label": "单据明细",
				"fieldtype": "Small Text",
				"read_only": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"no_copy": 1,
				"insert_after": "supplier_name",
				"description": "系统根据采购物料明细子表自动汇总生成"
			}
		],
		"Purchase Receipt": [
			{
				"fieldname": "custom_doc_details",
				"label": "单据明细",
				"fieldtype": "Small Text",
				"read_only": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"no_copy": 1,
				"insert_after": "supplier_name",
				"description": "系统根据入库物资明细子表自动汇总生成"
			}
		],
		"Purchase Invoice": [
			{
				"fieldname": "custom_doc_details",
				"label": "单据明细",
				"fieldtype": "Small Text",
				"read_only": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"no_copy": 1,
				"insert_after": "supplier_name",
				"description": "系统根据发票物料明细子表自动汇总生成"
			}
		],
		"Reimbursement Request": [
			{
				"fieldname": "custom_doc_details",
				"label": "单据明细",
				"fieldtype": "Small Text",
				"read_only": 1,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"no_copy": 1,
				"insert_after": "applicant",
				"description": "系统根据发票与报销明细子表自动汇总生成"
			}
		]
	}

	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	create_custom_fields(custom_fields, ignore_validate=True)
	frappe.db.commit()


def backfill_all_document_details():
	"""
	批量扫描并回填历史单据的【单据明细】
	"""
	try:
		from ashan_cn_procurement.overrides.document_details import update_doc_details

		doctypes = ["Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Reimbursement Request"]
		for dt in doctypes:
			if not frappe.db.exists("DocType", dt):
				continue
			docs = frappe.get_all(dt, fields=["name"], limit=300)
			for d in docs:
				try:
					doc = frappe.get_doc(dt, d.name)
					update_doc_details(doc)
					if doc.get("custom_doc_details"):
						frappe.db.set_value(dt, d.name, "custom_doc_details", doc.custom_doc_details, update_modified=False)
						if dt == "Purchase Invoice" and hasattr(doc, "custom_items_summary"):
							frappe.db.set_value(dt, d.name, "custom_items_summary", doc.custom_doc_details, update_modified=False)
				except Exception as err:
					frappe.logger("setup").warning(f"Backfill doc details failed for {dt} {d.name}: {err}")

		frappe.db.commit()
	except Exception as e:
		frappe.logger("setup").warning(f"Backfill all document details failed: {e}")


def sync_all_workspace_sidebars():
	"""
	同步所有核心 Workspace 侧边栏（Home, My Business, Ashan CN Procurement 等），
	确保包含完整的【物业与租赁】、【车辆和车用油管理】、【企业合规中心】、【财务与报销】等全部定制功能项。
	"""
	import json, os
	cur_dir = os.path.dirname(os.path.abspath(__file__))
	sidebar_json_path = os.path.join(cur_dir, "ashan_cn_procurement", "workspace_sidebar", "home.json")
	if not os.path.exists(sidebar_json_path):
		return

	with open(sidebar_json_path, "r", encoding="utf-8") as f:
		sidebar_def = json.load(f)

	items_template = sidebar_def.get("items", [])
	target_sidebars = [
		"Home",
		"My Business",
		"Ashan CN Procurement",
		"Property and Lease",
		"Vehicle Fuel Hub",
		"Stock and Inventory",
		"Procurement Management",
		"Company Compliance Center",
		"Accounting and Finance"
	]

	for sb_name in target_sidebars:
		try:
			if frappe.db.exists("Workspace Sidebar", sb_name):
				doc = frappe.get_doc("Workspace Sidebar", sb_name)
			else:
				doc = frappe.new_doc("Workspace Sidebar")
				doc.name = sb_name
				doc.title = sb_name
				doc.header_icon = "home"
				doc.app = "ashan_cn_procurement"

			doc.set("items", [])
			for idx, it in enumerate(items_template, 1):
				it_copy = dict(it)
				it_copy["idx"] = idx
				it_copy["parent"] = sb_name
				it_copy["parenttype"] = "Workspace Sidebar"
				it_copy["parentfield"] = "items"
				doc.append("items", it_copy)

			doc.flags.ignore_permissions = True
			doc.save()
		except Exception as e:
			frappe.logger("setup").warning(f"Failed to sync sidebar {sb_name}: {e}")

	frappe.db.commit()

def cleanup_deprecated_sidebar_items():
	"""
	清理数据库中已废弃的 Property Charge Rate 侧边栏项
	"""
	try:
		frappe.db.sql("DELETE FROM `tabWorkspace Sidebar Item` WHERE link_to = 'Property Charge Rate' OR label = '收费标准版本'")
		frappe.db.commit()
	except Exception as e:
		frappe.logger("setup").warning(f"Clean sidebar items failed: {e}")



def setup_default_app_system_settings():
	"""
	Frappe 16 官方标准机制：将系统默认 App (default_app) 设置为 ashan_cn_procurement
	使 get_default_path() 原生返回 /desk/Workspaces/Home，登录与主页直达业务工作台，不再回退官方应用选择页或空白页。
	"""
	try:
		frappe.db.set_single_value("System Settings", "default_app", "ashan_cn_procurement")
		frappe.db.commit()
	except Exception as e:
		frappe.logger("setup").error(f"Failed to set default_app in System Settings: {e}")

def migrate_property_lease_and_rates():
	"""
	平滑数据合并：将现存 Property Charge Rate 记录数据无缝回填至 Property Lease 中
	并确保出租方 Supplier、税率 5% 等字段初始化
	"""
	# 1. 确保发票中的出租方 Supplier 存在
	sample_landlords = [
		{"name": "圣凯（天津）工业有限公司", "tax_id": "9112011667149649XU", "alias": "圣凯工业"},
		{"name": "天津金利达物业管理有限公司", "alias": "金利达物业"}
	]
	for l in sample_landlords:
		if not frappe.db.exists("Supplier", l["name"]):
			try:
				s_doc = frappe.new_doc("Supplier")
				s_doc.supplier_name = l["name"]
				s_doc.supplier_group = "Services" if frappe.db.exists("Supplier Group", "Services") else "All Supplier Groups"
				s_doc.tax_id = l.get("tax_id") or ""
				s_doc.insert(ignore_permissions=True)
			except Exception as e:
				frappe.logger("setup").warning(f"Create landlord supplier failed: {e}")

	# 2. 如果存在旧的 Charge Rate 记录，回填进 Lease
	if frappe.db.exists("DocType", "Property Charge Rate"):
		try:
			rates = frappe.get_all("Property Charge Rate", fields=["*"], order_by="effective_from DESC")
			for r in rates:
				p_lease = r.get("property_lease")
				if p_lease and frappe.db.exists("Property Lease", p_lease):
					doc = frappe.get_doc("Property Lease", p_lease)
					doc.rent_pricing_mode = r.get("rent_pricing_mode") or "按年总金额 (元/年)"
					doc.rent_annual_amount = r.get("rent_annual_amount") or 0.0
					doc.rent_monthly_amount = r.get("rent_monthly_amount") or 0.0
					doc.rent_daily_rate = r.get("rent_daily_rate") or 0.0
					doc.rent_monthly_rate = r.get("rent_monthly_rate") or 0.0
					doc.rent_annual_rate = r.get("rent_annual_rate") or 0.0
					doc.rent_tax_rate = r.get("rent_tax_rate") or 5.0
					doc.is_tax_inclusive = 1

					doc.property_fee_mode = r.get("property_fee_mode") or "房租含物业"
					doc.property_fee_pricing_mode = r.get("property_fee_pricing_mode") or "按月单价 (元/㎡·月)"
					doc.property_fee_monthly_rate = r.get("property_fee_monthly_rate") or 0.0
					doc.property_fee_annual_amount = r.get("property_fee_annual_amount") or 0.0
					doc.property_fee_monthly_amount = r.get("property_fee_monthly_amount") or 0.0
					doc.property_fee_daily_rate = r.get("property_fee_daily_rate") or 0.0
					doc.property_fee_annual_rate = r.get("property_fee_annual_rate") or 0.0
					doc.property_fee_tax_rate = r.get("property_fee_tax_rate") or 6.0
					doc.property_fee_is_tax_inclusive = 1

					if not doc.supplier:
						doc.supplier = "圣凯（天津）工业有限公司"
					doc.save(ignore_permissions=True)
		except Exception as e:
			frappe.logger("setup").warning(f"Migrate property charge rate to lease failed: {e}")

	# 3. 确保天津祺富机械加工有限公司拥有发票中的 930㎡ 仓库记录
	sample_lease_name = "天津祺富机械加工有限公司-仓库-930平米"
	if not frappe.db.exists("Property Lease", sample_lease_name):
		try:
			comp = "天津祺富机械加工有限公司"
			if not frappe.db.exists("Company", comp):
				companies = frappe.get_all("Company", fields=["name"], limit=1)
				comp = companies[0].name if companies else None

			if comp:
				doc = frappe.new_doc("Property Lease")
				doc.property_name = "仓库-930平米 (空港中环南路106号)"
				doc.company = comp
				doc.supplier = "圣凯（天津）工业有限公司"
				doc.area = 930.0
				doc.property_certificate_no = "115011400759"
				doc.location_address = "天津市东丽区空港经济区中环南路106号"
				doc.start_date = "2026-07-01"
				doc.end_date = "2027-06-30"
				doc.enabled = 1

				doc.rent_pricing_mode = "按年总金额 (元/年)"
				doc.is_tax_inclusive = 1
				doc.rent_tax_rate = 5.0
				doc.rent_annual_amount = 238800.0
				doc.property_fee_mode = "房租含物业"
				doc.remark = "发票号码: 26122000001028974306，不动产经营租赁服务专票"
				doc.insert(ignore_permissions=True)
		except Exception as e:
			frappe.logger("setup").warning(f"Create sample lease record failed: {e}")

	frappe.db.commit()


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
		"Special Equipment Annual Inspection",
		"Property Lease",
		"Property Charge Rate",
		"Utility Meter",
		"Property Monthly Settlement",
		"Tax Invoice",
		"Tax Invoice Item",
		"Tax Invoice Import Batch",
		"Tax Invoice Settings",
		"Tax Invoice Company Mapping"
	]
	target_roles = ["System Manager", "Accounts Manager", "Accounts User", "Fleet Manager", "Oil Card Manager", "油卡管理员", "Oil Card Operator", "油卡操作员", "Desk User", "All"]

	for dt in oil_doctypes:
		if not frappe.db.exists("DocType", dt):
			continue
		for role in target_roles:
			is_mgr = role in ["System Manager", "Accounts Manager", "Fleet Manager", "Oil Card Manager", "油卡管理员"]
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
			elif dt in ["Tax Invoice", "Tax Invoice Import Batch"]:
				dp.create = 1 if is_mgr else 0
				dp.write = 1 if is_mgr else 0
				dp.delete = 1 if role == "System Manager" else 0
			else:
				dp.create = 1
				dp.write = 1
				dp.delete = 1 if is_mgr else 0

			dp.save(ignore_permissions=True)

	# 3. 确保 Pages 拥有这些角色的访问权限
	for page_name in ["oil-card-ledger", "vehicle-toll-ledger", "special-equipment-center", "environmental-management", "property-settlement-workbench", "lease-settlement-workbench", "tax-invoice-center"]:
		if frappe.db.exists("Page", page_name):
			page_doc = frappe.get_doc("Page", page_name)
			existing_roles = {r.role for r in page_doc.roles}
			modified = False
			for role in ["System Manager", "Accounts Manager", "Accounts User", "Fleet Manager", "Oil Card Manager", "油卡管理员", "Oil Card Operator", "油卡操作员", "Desk User", "All"]:
				if role not in existing_roles:
					page_doc.append("roles", {"role": role})
					modified = True
			if modified:
				page_doc.save(ignore_permissions=True)

	frappe.db.commit()




