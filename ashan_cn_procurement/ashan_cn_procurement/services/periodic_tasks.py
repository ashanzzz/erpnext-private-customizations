# -*- coding: utf-8 -*-
# Copyright (c) 2026, Ashan CN Procurement and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, nowdate, cint, date_diff, add_months, add_days

@frappe.whitelist()
def get_monthly_settlement_status(year=None, month=None):
    """
    获取指定年月的【我的月度任务】（月度报表核定）状态
    支持多主体（吉众、祺富）按用户公司权限与角色严格隔离
    """
    try:
        current_date = getdate(nowdate())

        # 默认核定周期：若未显式传入年月，自动推导上一自然月
        if not year or not month:
            if current_date.month == 1:
                target_year = current_date.year - 1
                target_month = 12
            else:
                target_year = current_date.year
                target_month = current_date.month - 1
        else:
            target_year = cint(year)
            target_month = cint(month)

        period_str = f"{target_year}-{target_month:02d}"
        period_label = f"{target_year}年{target_month}月"

        user = frappe.session.user
        roles = frappe.get_roles(user)
        is_admin = (user == "Administrator") or ("System Manager" in roles) or ("财务主管" in roles) or ("Accounts Manager" in roles)

        # 1. 精准推导当前用户被授权访问的公司
        user_allowed_companies = set()
        if is_admin:
            user_allowed_companies.add("吉众")
            user_allowed_companies.add("祺富")
        else:
            perms = frappe.get_all("User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value")
            for p in perms:
                if "吉众" in p:
                    user_allowed_companies.add("吉众")
                if "祺富" in p:
                    user_allowed_companies.add("祺富")

            if frappe.db.exists("DocType", "Employee"):
                emp_company = frappe.db.get_value("Employee", {"user_id": user}, "company") or ""
                if "吉众" in emp_company:
                    user_allowed_companies.add("吉众")
                if "祺富" in emp_company:
                    user_allowed_companies.add("祺富")

            def_company = frappe.db.get_value("User", user, "company") or frappe.defaults.get_user_default("company") or ""
            if "吉众" in str(def_company):
                user_allowed_companies.add("吉众")
            if "祺富" in str(def_company):
                user_allowed_companies.add("祺富")

            if not user_allowed_companies:
                if any(r in roles for r in ["Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"]):
                    user_allowed_companies.add("吉众")
                if any(r in roles for r in ["Property Operator", "Property Manager", "物业操作员", "物业管理员", "Accounts User"]):
                    user_allowed_companies.add("祺富")

        has_jizhong_perm = ("吉众" in user_allowed_companies) or is_admin
        has_qifu_perm = ("祺富" in user_allowed_companies) or is_admin

        # 角色权限感知
        can_manage_oil = is_admin or any(r in roles for r in ["Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"])
        can_manage_property = is_admin or any(r in roles for r in ["Property Operator", "Property Manager", "物业操作员", "物业管理员", "Accounts User"])

        # 2. 吉众月度报表核定 (天津吉众机电设备有限公司)
        jizhong_items = []
        if has_jizhong_perm and (can_manage_oil or is_admin):
            # A. 油卡明细核定
            oil_status = "unsettled"
            oil_summary = "本期加油及油票明细待核定"

            has_oil_summary = False
            if frappe.db.exists("DocType", "Oil Card Invoice Batch"):
                has_oil_summary = bool(frappe.db.exists("Oil Card Invoice Batch", {
                    "batch_period": period_str,
                    "docstatus": 1
                }))

            if not has_oil_summary and frappe.db.exists("DocType", "Oil Card Monthly Summary"):
                has_oil_summary = bool(frappe.db.exists("Oil Card Monthly Summary", {
                    "period": period_str,
                    "docstatus": 1
                }))

            if has_oil_summary:
                oil_status = "settled"
                oil_summary = f"{period_label} 油卡台账已核定锁定"
            else:
                refuel_count = 0
                if frappe.db.exists("DocType", "Oil Card Refuel Log"):
                    try:
                        refuel_count = frappe.db.count("Oil Card Refuel Log", {
                            "posting_date": ["between", [f"{period_str}-01", f"{period_str}-31"]]
                        })
                    except Exception:
                        refuel_count = 0
                if refuel_count > 0:
                    oil_summary = f"当月有 {refuel_count} 笔加油记录等待核定对账"
                else:
                    oil_summary = "当月尚未录入/核定加油明细"

            jizhong_items.append({
                "id": "oil_card",
                "title": "油卡明细",
                "icon": "⛽",
                "status": oil_status,
                "status_label": "已核定" if oil_status == "settled" else "未核定",
                "action_label": "去核定 ➔" if oil_status != "settled" else "查看台账",
                "route": "/desk/oil-card-ledger",
                "summary_text": oil_summary
            })

            # B. 车辆高速费核定
            has_toll_vehicle = False
            if frappe.db.exists("DocType", "Vehicle Toll Config"):
                try:
                    toll_configs = frappe.get_all("Vehicle Toll Config", fields=["vehicle", "is_active"], filters={"is_active": 1})
                    for tc in toll_configs:
                        veh_name = tc.get("vehicle")
                        veh_comp = frappe.db.get_value("Vehicle", veh_name, "company") if frappe.db.exists("DocType", "Vehicle") else ""
                        if not veh_comp or "吉众" in str(veh_comp):
                            has_toll_vehicle = True
                            break
                except Exception:
                    has_toll_vehicle = False

            if has_toll_vehicle:
                toll_status = "unsettled"
                toll_summary = "高速费通行流水待核定"

                has_toll_sheet = False
                if frappe.db.exists("DocType", "Vehicle Toll Monthly Sheet"):
                    has_toll_sheet = bool(frappe.db.exists("Vehicle Toll Monthly Sheet", {
                        "sheet_period": period_str,
                        "docstatus": 1
                    }))

                if has_toll_sheet:
                    toll_status = "settled"
                    toll_summary = f"{period_label} 高速费月度台账已核定"
                else:
                    toll_summary = "当月高速费通行流水待生成月度账单"

                jizhong_items.append({
                    "id": "highway_toll",
                    "title": "车辆高速费",
                    "icon": "🛣️",
                    "status": toll_status,
                    "status_label": "已核定" if toll_status == "settled" else "未核定",
                    "action_label": "去核定 ➔" if toll_status != "settled" else "查看台账",
                    "route": "/desk/vehicle-toll-monthly-sheet",
                    "summary_text": toll_summary
                })

        # 3. 祺富月度报表核定 (天津祺富机械加工有限公司)
        qifu_items = []
        if has_qifu_perm and (can_manage_property or is_admin):
            # A. 水电费月结 (按月抄表与倍率分摊)
            utility_status = "unsettled"
            utility_summary = "当月水电抄表及倍率分摊待核定"

            has_utility_settle = False
            if frappe.db.exists("DocType", "Property Monthly Settlement"):
                has_utility_settle = bool(frappe.db.exists("Property Monthly Settlement", {
                    "settlement_period": period_str,
                    "settlement_type": ["in", ["水电费月结", "综合月结", "水电月结"]],
                    "docstatus": 1
                }))

            if has_utility_settle:
                utility_status = "settled"
                utility_summary = f"{period_label} 水电费已核定完成并过账"
            else:
                utility_summary = "本期水电抄表与差额分摊未锁定"

            qifu_items.append({
                "id": "utility_settlement",
                "title": "水电费月结",
                "icon": "💡",
                "status": utility_status,
                "status_label": "已核定" if utility_status == "settled" else "未核定",
                "action_label": "去核定 ➔" if utility_status != "settled" else "查看工作台",
                "route": "/desk/property-settlement-workbench",
                "summary_text": utility_summary
            })

        show_jizhong = len(jizhong_items) > 0 and has_jizhong_perm
        show_qifu = len(qifu_items) > 0 and has_qifu_perm

        total_items = (len(jizhong_items) if show_jizhong else 0) + (len(qifu_items) if show_qifu else 0)
        settled_items = (
            sum(1 for i in jizhong_items if i['status'] == 'settled') if show_jizhong else 0
        ) + (
            sum(1 for i in qifu_items if i['status'] == 'settled') if show_qifu else 0
        )

        return {
            "period": period_str,
            "period_label": period_label,
            "current_user": user,
            "is_admin": is_admin,
            "total_items": total_items,
            "settled_items": settled_items,
            "all_done": total_items > 0 and (total_items == settled_items),
            "companies": {
                "jizhong": {
                    "company_name": "天津吉众机电设备有限公司",
                    "short_name": "吉众",
                    "visible": show_jizhong,
                    "items": jizhong_items
                },
                "qifu": {
                    "company_name": "天津祺富机械加工有限公司",
                    "short_name": "祺富",
                    "visible": show_qifu,
                    "items": qifu_items
                }
            }
        }
    except Exception as e:
        frappe.log_error(f"get_monthly_settlement_status error: {str(e)}")
        return {
            "period": f"{target_year}-{target_month:02d}" if "target_year" in locals() else "",
            "period_label": f"{target_year}年{target_month}月" if "target_year" in locals() else "",
            "error": str(e),
            "total_items": 0,
            "settled_items": 0,
            "all_done": False,
            "companies": {}
        }

@frappe.whitelist()
def get_compliance_expiry_status():
    """
    获取【我的临期预警】状态列表（合同、车辆、设备、员工资质）
    支持天数智能分级、红黄绿 SLA 预警与一键弹窗快速记录完成/核定
    """
    try:
        today = getdate(nowdate())
        user = frappe.session.user
        roles = frappe.get_roles(user)
        is_admin = (user == "Administrator") or ("System Manager" in roles) or ("财务主管" in roles) or ("Accounts Manager" in roles)

        # 公司权限判定
        user_allowed_companies = set()
        if is_admin:
            user_allowed_companies.add("吉众")
            user_allowed_companies.add("祺富")
        else:
            perms = frappe.get_all("User Permission", filters={"user": user, "allow": "Company"}, pluck="for_value")
            for p in perms:
                if "吉众" in p: user_allowed_companies.add("吉众")
                if "祺富" in p: user_allowed_companies.add("祺富")
            if frappe.db.exists("DocType", "Employee"):
                emp_company = frappe.db.get_value("Employee", {"user_id": user}, "company") or ""
                if "吉众" in emp_company: user_allowed_companies.add("吉众")
                if "祺富" in emp_company: user_allowed_companies.add("祺富")
            if not user_allowed_companies:
                user_allowed_companies.add("吉众")
                user_allowed_companies.add("祺富")

        has_jizhong = ("吉众" in user_allowed_companies) or is_admin
        has_qifu = ("祺富" in user_allowed_companies) or is_admin

        expiry_items = []

        # 1. 房租与物业租约合同到期 (Property Lease -> 祺富)
        if has_qifu and frappe.db.exists("DocType", "Property Lease"):
            leases = frappe.get_all("Property Lease", fields=["name", "property_name", "company", "end_date", "enabled"], filters={"enabled": 1})
            for l in leases:
                if l.end_date:
                    days = date_diff(l.end_date, today)
                    if days <= 60:
                        level = "danger" if days < 0 else ("warning" if days <= 30 else "info")
                        status_text = f"已逾期 {abs(days)} 天" if days < 0 else f"剩余 {days} 天到期"
                        suggested_next = str(add_months(getdate(l.end_date), 12))
                        expiry_items.append({
                            "id": f"lease_{l.name}",
                            "doctype": "Property Lease",
                            "docname": l.name,
                            "category": "合同租约",
                            "icon": "📑",
                            "company": "祺富",
                            "title": f"租赁合同: {l.property_name or l.name}",
                            "due_date": str(l.end_date),
                            "cycle_months": 12,
                            "suggested_next_due": suggested_next,
                            "days_remaining": days,
                            "level": level,
                            "status_text": status_text,
                            "action_label": "办理续租 ➔",
                            "route": f"/desk/property-lease/{l.name}",
                            "is_cyclical": True
                        })

        # 2. 员工外籍工作证与资格证书 (Employee Certificate Item)
        if frappe.db.exists("DocType", "Employee Certificate Item"):
            certs = frappe.get_all("Employee Certificate Item", fields=["name", "certificate_name", "employee", "company", "next_due_date", "cycle_months", "is_active"], filters={"is_active": 1})
            for c in certs:
                comp_name = str(c.company or "")
                match_comp = (has_jizhong and "吉众" in comp_name) or (has_qifu and "祺富" in comp_name) or is_admin
                if match_comp and c.next_due_date:
                    days = date_diff(c.next_due_date, today)
                    if days <= 45:
                        level = "danger" if days < 0 else ("warning" if days <= 20 else "info")
                        status_text = f"已超期 {abs(days)} 天" if days < 0 else f"剩余 {days} 天到期"
                        emp_name = c.employee or "员工"
                        cycle_m = cint(c.cycle_months) or 12
                        suggested_next = str(add_months(today, cycle_m))
                        expiry_items.append({
                            "id": f"cert_{c.name}",
                            "doctype": "Employee Certificate Item",
                            "docname": c.name,
                            "category": "员工资质",
                            "icon": "🪪",
                            "company": "吉众" if "吉众" in comp_name else ("祺富" if "祺富" in comp_name else "公司"),
                            "title": f"{emp_name} - {c.certificate_name}",
                            "due_date": str(c.next_due_date),
                            "cycle_months": cycle_m,
                            "suggested_next_due": suggested_next,
                            "days_remaining": days,
                            "level": level,
                            "status_text": status_text,
                            "action_label": "记录续期 ➔",
                            "route": f"/desk/employee-certificate-item/{c.name}",
                            "is_cyclical": True
                        })

        # 3. 特种设备检验 (Compliance Equipment Item)
        if frappe.db.exists("DocType", "Compliance Equipment Item"):
            eqs = frappe.get_all("Compliance Equipment Item", fields=["name", "equipment_name", "company", "next_due_date", "cycle_months", "is_active"], filters={"is_active": 1})
            for e in eqs:
                comp_name = str(e.company or "")
                match_comp = (has_jizhong and "吉众" in comp_name) or (has_qifu and "祺富" in comp_name) or is_admin
                if match_comp and e.next_due_date:
                    days = date_diff(e.next_due_date, today)
                    if days <= 45:
                        level = "danger" if days < 0 else ("warning" if days <= 20 else "info")
                        status_text = f"检验逾期 {abs(days)} 天" if days < 0 else f"剩余 {days} 天检验"
                        cycle_m = cint(e.cycle_months) or 12
                        suggested_next = str(add_months(today, cycle_m))
                        expiry_items.append({
                            "id": f"eq_{e.name}",
                            "doctype": "Compliance Equipment Item",
                            "docname": e.name,
                            "category": "特种设备",
                            "icon": "⚙️",
                            "company": "吉众" if "吉众" in comp_name else ("祺富" if "祺富" in comp_name else "车间"),
                            "title": f"特检: {e.equipment_name}",
                            "due_date": str(e.next_due_date),
                            "cycle_months": cycle_m,
                            "suggested_next_due": suggested_next,
                            "days_remaining": days,
                            "level": level,
                            "status_text": status_text,
                            "action_label": "记录检验 ➔",
                            "route": f"/desk/compliance-equipment-item/{e.name}",
                            "is_cyclical": True
                        })

        # 4. 环保合规检测 (Environmental Compliance Item)
        if frappe.db.exists("DocType", "Environmental Compliance Item"):
            envs = frappe.get_all("Environmental Compliance Item", fields=["name", "title", "company", "next_due_date", "cycle_months", "is_active"], filters={"is_active": 1})
            for env in envs:
                comp_name = str(env.company or "")
                match_comp = (has_jizhong and "吉众" in comp_name) or (has_qifu and "祺富" in comp_name) or is_admin
                if match_comp and env.next_due_date:
                    days = date_diff(env.next_due_date, today)
                    if days <= 45:
                        level = "danger" if days < 0 else ("warning" if days <= 20 else "info")
                        status_text = f"检测已超期 {abs(days)} 天" if days < 0 else f"剩余 {days} 天检测"
                        cycle_m = cint(env.cycle_months) or 3
                        suggested_next = str(add_months(today, cycle_m))
                        expiry_items.append({
                            "id": f"env_{env.name}",
                            "doctype": "Environmental Compliance Item",
                            "docname": env.name,
                            "category": "环保检测",
                            "icon": "🌱",
                            "company": "祺富" if "祺富" in comp_name else "吉众",
                            "title": f"环保: {env.title}",
                            "due_date": str(env.next_due_date),
                            "cycle_months": cycle_m,
                            "suggested_next_due": suggested_next,
                            "days_remaining": days,
                            "level": level,
                            "status_text": status_text,
                            "action_label": "安排检测 ➔",
                            "route": f"/desk/environmental-compliance-item/{env.name}",
                            "is_cyclical": True
                        })

        # 5. 车辆保险与审验 (Vehicle -> 吉众)
        if has_jizhong and frappe.db.exists("DocType", "Vehicle"):
            vehs = frappe.get_all("Vehicle", fields=["name", "license_plate", "company", "end_date"], filters={})
            for v in vehs:
                if v.end_date:
                    days = date_diff(v.end_date, today)
                    if days <= 30:
                        level = "danger" if days < 0 else ("warning" if days <= 15 else "info")
                        status_text = f"车险逾期 {abs(days)} 天" if days < 0 else f"剩余 {days} 天到期"
                        suggested_next = str(add_months(getdate(v.end_date), 12))
                        expiry_items.append({
                            "id": f"veh_{v.name}",
                            "doctype": "Vehicle",
                            "docname": v.name,
                            "category": "车辆保险",
                            "icon": "🚚",
                            "company": "吉众",
                            "title": f"车辆保险: {v.license_plate or v.name}",
                            "due_date": str(v.end_date),
                            "cycle_months": 12,
                            "suggested_next_due": suggested_next,
                            "days_remaining": days,
                            "level": level,
                            "status_text": status_text,
                            "action_label": "办理续保 ➔",
                            "route": f"/desk/vehicle/{v.name}",
                            "is_cyclical": True
                        })

        # 排序：逾期越严重的排最前
        expiry_items.sort(key=lambda x: x["days_remaining"])

        danger_count = sum(1 for x in expiry_items if x["level"] == "danger")
        warning_count = sum(1 for x in expiry_items if x["level"] == "warning")
        total_count = len(expiry_items)

        return {
            "total_count": total_count,
            "danger_count": danger_count,
            "warning_count": warning_count,
            "all_valid": total_count == 0,
            "items": expiry_items
        }
    except Exception as e:
        frappe.log_error(f"get_compliance_expiry_status error: {str(e)}")
        return {
            "error": str(e),
            "total_count": 0,
            "danger_count": 0,
            "warning_count": 0,
            "all_valid": True,
            "items": []
        }

@frappe.whitelist()
def record_compliance_inspection(doctype, docname, done_date=None, next_due_date=None, notes=None):
    """
    快速记录周期性检测/检验/续租完成，直接就地推进下一周期到期日，无需跳转
    """
    try:
        if not doctype or not docname:
            frappe.throw("缺少 DocType 或单据编号")

        if not frappe.has_permission(doctype, "write"):
            frappe.throw(f"您没有修改 {doctype} 的权限")

        doc = frappe.get_doc(doctype, docname)
        today = getdate(nowdate())
        effective_done_date = getdate(done_date) if done_date else today

        updated_next_due = None

        if doctype == "Environmental Compliance Item":
            cycle = cint(doc.cycle_months) or 3
            doc.last_done_date = effective_done_date
            if next_due_date:
                doc.next_due_date = getdate(next_due_date)
            else:
                doc.next_due_date = add_months(effective_done_date, cycle)
            updated_next_due = str(doc.next_due_date)
            doc.remarks = f"{doc.remarks or ''}\n[{nowdate()}] 已完成检验/处置记录。完成日期: {effective_done_date}，下次到期: {updated_next_due}。备注: {notes or '无'}"
            doc.save()

        elif doctype == "Compliance Equipment Item":
            cycle = cint(doc.cycle_months) or 12
            doc.last_inspection_date = effective_done_date
            if next_due_date:
                doc.next_due_date = getdate(next_due_date)
            else:
                doc.next_due_date = add_months(effective_done_date, cycle)
            updated_next_due = str(doc.next_due_date)
            doc.remarks = f"{doc.remarks or ''}\n[{nowdate()}] 特种设备检验完成。完成日期: {effective_done_date}，下次到期: {updated_next_due}。备注: {notes or '无'}"
            doc.save()

        elif doctype == "Employee Certificate Item":
            cycle = cint(doc.cycle_months) or 12
            doc.issue_date = effective_done_date
            if next_due_date:
                doc.next_due_date = getdate(next_due_date)
            else:
                doc.next_due_date = add_months(effective_done_date, cycle)
            updated_next_due = str(doc.next_due_date)
            doc.remarks = f"{doc.remarks or ''}\n[{nowdate()}] 员工资质/外籍工作证复审续期完成。完成日期: {effective_done_date}，下次到期: {updated_next_due}。备注: {notes or '无'}"
            doc.save()

        elif doctype == "Property Lease":
            if next_due_date:
                doc.end_date = getdate(next_due_date)
            else:
                doc.end_date = add_months(getdate(doc.end_date or today), 12)
            updated_next_due = str(doc.end_date)
            doc.remark = f"{doc.remark or ''}\n[{nowdate()}] 办理续租。新到期日: {updated_next_due}。备注: {notes or '无'}"
            doc.save()

        elif doctype == "Vehicle":
            if next_due_date:
                doc.end_date = getdate(next_due_date)
            else:
                doc.end_date = add_months(getdate(doc.end_date or today), 12)
            updated_next_due = str(doc.end_date)
            doc.save()

        return {
            "success": True,
            "doctype": doctype,
            "docname": docname,
            "done_date": str(effective_done_date),
            "next_due_date": updated_next_due,
            "message": f"已成功更新！下期到期时间已推进至: {updated_next_due}"
        }
    except Exception as e:
        frappe.log_error(f"record_compliance_inspection error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
