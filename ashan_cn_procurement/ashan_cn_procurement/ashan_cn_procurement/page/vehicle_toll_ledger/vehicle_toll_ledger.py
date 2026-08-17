# -*- coding: utf-8 -*-
import json
import calendar
import frappe
from frappe import _
from frappe.utils import now_datetime, cint, flt, getdate

WEEKDAYS_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

def is_toll_manager():
    if frappe.session.user == "Administrator":
        return True
    roles = frappe.get_roles()
    return any(r in ["System Manager", "Oil Card Manager", "油卡管理员"] for r in roles)

def is_toll_user():
    if is_toll_manager():
        return True
    roles = frappe.get_roles()
    return any(r in ["Oil Card Operator", "油卡操作员"] for r in roles)

def get_default_toll_routes():
    return [
        {"id": "r1", "name": "进城收费站"},
        {"id": "r2", "name": "出城收费站"}
    ]

def get_prev_ym(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)

def get_next_ym(year, month):
    return (year + 1, 1) if month == 12 else (year, month + 1)

@frappe.whitelist()
def get_enrolled_vehicles():
    """获取所有入池的高速费车辆列表"""
    configs = frappe.get_list(
        "Vehicle Toll Config",
        filters={"is_active": 1},
        fields=["name", "vehicle", "display_name", "toll_routes", "opening_balance_default"],
        order_by="creation asc"
    )
    result = []
    for c in configs:
        try:
            routes = json.loads(c.toll_routes) if c.toll_routes else get_default_toll_routes()
        except Exception:
            routes = get_default_toll_routes()
        result.append({
            "config_name": c.name,
            "vehicle": c.vehicle,
            "display_name": c.display_name or c.vehicle or c.name,
            "toll_routes": routes,
            "opening_balance_default": flt(c.opening_balance_default)
        })
    return {
        "vehicles": result,
        "is_manager": is_toll_manager()
    }

@frappe.whitelist()
def get_vehicle_monthly_sheet(vehicle_config, year=None, month=None):
    """获取指定车辆、指定年月的高速费月度台账"""
    now = now_datetime()
    year = cint(year) if year else now.year
    month = cint(month) if month else now.month

    # 验证车辆配置存在
    if not frappe.db.exists("Vehicle Toll Config", vehicle_config):
        frappe.throw(_("车辆配置不存在：{0}").format(vehicle_config))

    cfg = frappe.get_doc("Vehicle Toll Config", vehicle_config)
    try:
        toll_routes = json.loads(cfg.toll_routes) if cfg.toll_routes else get_default_toll_routes()
    except Exception:
        toll_routes = get_default_toll_routes()

    _, num_days = calendar.monthrange(year, month)
    doc_name = f"TOLL-{vehicle_config}-{year}-{month}"

    if frappe.db.exists("Vehicle Toll Monthly Sheet", doc_name):
        doc = frappe.get_doc("Vehicle Toll Monthly Sheet", doc_name)
        try:
            routes = json.loads(doc.toll_routes) if doc.toll_routes else toll_routes
        except Exception:
            routes = toll_routes
        try:
            existing_recs = json.loads(doc.daily_records) if doc.daily_records else []
        except Exception:
            existing_recs = []

        existing_days = {r.get("day"): r for r in existing_recs}
        opening_bal = flt(doc.opening_balance)
    else:
        # 新建 — 从上月期末继承
        prev_y, prev_m = get_prev_ym(year, month)
        prev_name = f"TOLL-{vehicle_config}-{prev_y}-{prev_m}"
        if frappe.db.exists("Vehicle Toll Monthly Sheet", prev_name):
            prev_doc = frappe.get_doc("Vehicle Toll Monthly Sheet", prev_name)
            opening_bal = flt(prev_doc.closing_balance)
        else:
            opening_bal = flt(cfg.opening_balance_default)
        existing_days = {}
        routes = toll_routes
        doc = None

    # 获取本月所有预支注入记录（来自 Vehicle Toll Deposit）
    deposit_records = frappe.get_list(
        "Vehicle Toll Deposit",
        filters={
            "vehicle_config": vehicle_config,
            "fiscal_year": year,
            "fiscal_month": month
        },
        fields=["name", "deposit_date", "amount", "deposit_type", "reference_no", "remark"],
        order_by="deposit_date asc"
    )
    # 按日汇总预支金额
    deposit_by_day = {}
    deposit_details_by_day = {}
    for dep in deposit_records:
        d = getdate(dep.deposit_date)
        day_num = d.day
        deposit_by_day[day_num] = deposit_by_day.get(day_num, 0) + flt(dep.amount)
        if day_num not in deposit_details_by_day:
            deposit_details_by_day[day_num] = []
        deposit_details_by_day[day_num].append({
            "name": dep.name,
            "amount": flt(dep.amount),
            "deposit_type": dep.deposit_type,
            "reference_no": dep.reference_no or "",
            "remark": dep.remark or ""
        })

    # 构建每日完整记录
    cur_bal = opening_bal
    tot_exp = 0.0
    tot_dep = 0.0
    full_records = []

    for d in range(1, num_days + 1):
        date_str = f"{year}/{month:02d}/{d:02d}"
        weekday_idx = calendar.weekday(year, month, d)
        weekday_str = WEEKDAYS_CN[weekday_idx]

        existing = existing_days.get(d, {})
        routes_data = existing.get("routes", {})

        # 当天通行费（各路段之和）
        day_exp = sum(flt(routes_data.get(r["id"], 0)) for r in routes)

        # 当天公司注入（来自 Vehicle Toll Deposit，实时读取）
        day_dep = deposit_by_day.get(d, 0.0)
        dep_details = deposit_details_by_day.get(d, [])

        cur_bal = cur_bal - day_exp + day_dep
        tot_exp += day_exp
        tot_dep += day_dep

        full_records.append({
            "day": d,
            "date": date_str,
            "date_display": f"{date_str} {weekday_str}",
            "is_weekend": weekday_idx in [5, 6],
            "routes": routes_data,
            "expense": round(day_exp, 2),
            "deposit": round(day_dep, 2),
            "deposit_details": dep_details,
            "balance": round(cur_bal, 2),
            "remark": existing.get("remark", "")
        })

    is_locked = doc.is_locked if doc else 0
    locked_by = doc.locked_by if doc else None
    locked_at = str(doc.locked_at) if (doc and doc.locked_at) else None

    return {
        "vehicle_config": vehicle_config,
        "vehicle": cfg.vehicle,
        "display_name": cfg.display_name or cfg.vehicle or vehicle_config,
        "year": year,
        "month": month,
        "opening_balance": opening_bal,
        "total_expense": round(tot_exp, 2),
        "total_deposit": round(tot_dep, 2),
        "closing_balance": round(cur_bal, 2),
        "is_locked": is_locked,
        "locked_by": locked_by,
        "locked_at": locked_at,
        "remark": (doc.remark if doc else "") or "",
        "toll_routes": routes,
        "daily_records": full_records,
        "deposit_records": deposit_records,
        "is_manager": is_toll_manager()
    }

@frappe.whitelist()
def save_vehicle_toll_sheet(vehicle_config, year, month, daily_records, toll_routes=None, remark=""):
    """批量保存某辆车月度高速费台账（仅保存通行费矩阵，预支通过 Vehicle Toll Deposit 独立管理）"""
    year = cint(year)
    month = cint(month)

    if not frappe.db.exists("Vehicle Toll Config", vehicle_config):
        frappe.throw(_("车辆配置不存在：{0}").format(vehicle_config))

    if isinstance(daily_records, str):
        daily_records = json.loads(daily_records)

    if isinstance(toll_routes, str):
        toll_routes = json.loads(toll_routes)

    if toll_routes is None:
        cfg = frappe.get_doc("Vehicle Toll Config", vehicle_config)
        try:
            toll_routes = json.loads(cfg.toll_routes) if cfg.toll_routes else get_default_toll_routes()
        except Exception:
            toll_routes = get_default_toll_routes()

    doc_name = f"TOLL-{vehicle_config}-{year}-{month}"
    if frappe.db.exists("Vehicle Toll Monthly Sheet", doc_name):
        doc = frappe.get_doc("Vehicle Toll Monthly Sheet", doc_name)
        if doc.is_locked and not is_toll_manager():
            frappe.throw(_("该月份已核定锁定，仅管理员有权限修改！"))
    else:
        doc = frappe.new_doc("Vehicle Toll Monthly Sheet")
        doc.vehicle_config = vehicle_config
        doc.fiscal_year = year
        doc.fiscal_month = month

    # 获取预支记录（实时从 Vehicle Toll Deposit 中计算）
    deposit_by_day = {}
    dep_list = frappe.get_list(
        "Vehicle Toll Deposit",
        filters={"vehicle_config": vehicle_config, "fiscal_year": year, "fiscal_month": month},
        fields=["deposit_date", "amount"]
    )
    from frappe.utils import getdate as gd
    for dep in dep_list:
        d_day = gd(dep.deposit_date).day
        deposit_by_day[d_day] = deposit_by_day.get(d_day, 0) + flt(dep.amount)

    # 获取期初余额（从已有记录或上月继承）
    if doc.get("__islocal"):
        prev_y, prev_m = get_prev_ym(year, month)
        prev_name = f"TOLL-{vehicle_config}-{prev_y}-{prev_m}"
        if frappe.db.exists("Vehicle Toll Monthly Sheet", prev_name):
            opening_bal = flt(frappe.db.get_value("Vehicle Toll Monthly Sheet", prev_name, "closing_balance"))
        else:
            opening_bal = flt(frappe.db.get_value("Vehicle Toll Config", vehicle_config, "opening_balance_default"))
    else:
        opening_bal = flt(doc.opening_balance)

    # 重新计算汇总
    cur_bal = opening_bal
    tot_exp = 0.0
    tot_dep = 0.0
    sanitized = []

    for r in daily_records:
        day_num = cint(r.get("day"))
        routes_data = r.get("routes", {})
        day_exp = sum(flt(v) for v in routes_data.values())
        day_dep = deposit_by_day.get(day_num, 0.0)
        cur_bal = cur_bal - day_exp + day_dep
        tot_exp += day_exp
        tot_dep += day_dep
        sanitized.append({
            "day": day_num,
            "date": r.get("date", ""),
            "routes": {k: flt(v) for k, v in routes_data.items() if flt(v) > 0},
            "expense": round(day_exp, 2),
            "deposit": round(day_dep, 2),
            "balance": round(cur_bal, 2),
            "remark": (r.get("remark") or "").strip()
        })

    doc.opening_balance = opening_bal
    doc.total_expense = round(tot_exp, 2)
    doc.total_deposit = round(tot_dep, 2)
    doc.closing_balance = round(cur_bal, 2)
    doc.toll_routes = json.dumps(toll_routes, ensure_ascii=False)
    doc.daily_records = json.dumps(sanitized, ensure_ascii=False)
    doc.remark = remark or ""
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": _("高速费月度台账保存成功！"),
        "doc_name": doc.name,
        "closing_balance": doc.closing_balance
    }

@frappe.whitelist()
def add_toll_deposit(vehicle_config, deposit_date, amount, deposit_type="现金预支", reference_no="", remark=""):
    """快捷新增公司预支/充值记录"""
    if not frappe.db.exists("Vehicle Toll Config", vehicle_config):
        frappe.throw(_("车辆配置不存在：{0}").format(vehicle_config))

    amount = flt(amount)
    if amount <= 0:
        frappe.throw(_("预支金额必须大于 0！"))

    from frappe.utils import getdate
    d = getdate(deposit_date)

    dep = frappe.new_doc("Vehicle Toll Deposit")
    dep.vehicle_config = vehicle_config
    dep.deposit_date = deposit_date
    dep.amount = amount
    dep.deposit_type = deposit_type
    dep.reference_no = reference_no or ""
    dep.remark = remark or ""
    dep.fiscal_year = d.year
    dep.fiscal_month = d.month
    dep.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": _("预支/充值记录已保存：￥{0:,.2f}").format(amount),
        "doc_name": dep.name
    }

@frappe.whitelist()
def delete_toll_deposit(deposit_name):
    """删除预支记录"""
    if not frappe.db.exists("Vehicle Toll Deposit", deposit_name):
        frappe.throw(_("预支记录不存在！"))
    frappe.delete_doc("Vehicle Toll Deposit", deposit_name, ignore_permissions=True)
    frappe.db.commit()
    return {"success": True}

@frappe.whitelist()
def close_vehicle_toll_sheet(vehicle_config, year, month):
    """月度核定锁定"""
    if not is_toll_manager():
        frappe.throw(_("仅油卡/系统管理员具备执行月度核定的权限！"))

    year = cint(year)
    month = cint(month)
    doc_name = f"TOLL-{vehicle_config}-{year}-{month}"

    if not frappe.db.exists("Vehicle Toll Monthly Sheet", doc_name):
        frappe.throw(_("未找到该月份的台账记录，请先保存数据后再进行核定！"))

    doc = frappe.get_doc("Vehicle Toll Monthly Sheet", doc_name)
    doc.is_locked = 1
    doc.locked_by = frappe.session.user
    doc.locked_at = now_datetime()
    doc.save(ignore_permissions=True)

    # 级联更新下月期初（若下月已存在则更新，否则下次打开时自动继承）
    next_y, next_m = get_next_ym(year, month)
    next_name = f"TOLL-{vehicle_config}-{next_y}-{next_m}"
    if frappe.db.exists("Vehicle Toll Monthly Sheet", next_name):
        next_doc = frappe.get_doc("Vehicle Toll Monthly Sheet", next_name)
        if not next_doc.is_locked:
            next_doc.opening_balance = doc.closing_balance
            # 重新级联计算下月
            try:
                recs = json.loads(next_doc.daily_records) if next_doc.daily_records else []
                routes = json.loads(next_doc.toll_routes) if next_doc.toll_routes else get_default_toll_routes()
                dep_map = {}
                dep_list = frappe.get_list(
                    "Vehicle Toll Deposit",
                    filters={"vehicle_config": vehicle_config, "fiscal_year": next_y, "fiscal_month": next_m},
                    fields=["deposit_date", "amount"]
                )
                from frappe.utils import getdate as gd2
                for dep in dep_list:
                    dday = gd2(dep.deposit_date).day
                    dep_map[dday] = dep_map.get(dday, 0) + flt(dep.amount)

                c_bal = flt(next_doc.opening_balance)
                t_exp = 0.0
                t_dep = 0.0
                for r in recs:
                    exp = flt(r.get("expense", 0))
                    dep = dep_map.get(cint(r.get("day")), 0.0)
                    c_bal = c_bal - exp + dep
                    r["deposit"] = round(dep, 2)
                    r["balance"] = round(c_bal, 2)
                    t_exp += exp
                    t_dep += dep
                next_doc.total_expense = round(t_exp, 2)
                next_doc.total_deposit = round(t_dep, 2)
                next_doc.closing_balance = round(c_bal, 2)
                next_doc.daily_records = json.dumps(recs, ensure_ascii=False)
            except Exception as e:
                frappe.log_error(str(e), "Vehicle Toll Sheet — cascade next month")
            next_doc.save(ignore_permissions=True)

    frappe.db.commit()
    return {
        "success": True,
        "message": _("{0} {1}年{2}月高速费台账已核定锁定！期末结存 ￥{3:,.2f} 将自动结转至下月。").format(
            vehicle_config, year, month, doc.closing_balance
        ),
        "closing_balance": doc.closing_balance,
        "locked_by": doc.locked_by,
        "locked_at": str(doc.locked_at)
    }

@frappe.whitelist()
def reopen_vehicle_toll_sheet(vehicle_config, year, month):
    """取消核定解锁"""
    if not is_toll_manager():
        frappe.throw(_("仅管理员具备取消月度核定的权限！"))

    year = cint(year)
    month = cint(month)
    doc_name = f"TOLL-{vehicle_config}-{year}-{month}"
    if not frappe.db.exists("Vehicle Toll Monthly Sheet", doc_name):
        frappe.throw(_("未找到该月份的台账记录！"))

    doc = frappe.get_doc("Vehicle Toll Monthly Sheet", doc_name)
    doc.is_locked = 0
    doc.locked_by = None
    doc.locked_at = None
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "message": _("{0} {1}年{2}月已解锁，恢复录入状态。").format(vehicle_config, year, month)
    }

@frappe.whitelist()
def add_vehicle_to_toll(vehicle, display_name=None, toll_routes=None, opening_balance=0):
    """将车辆加入高速费管理入池"""
    if frappe.db.exists("Vehicle Toll Config", vehicle):
        doc = frappe.get_doc("Vehicle Toll Config", vehicle)
        doc.is_active = 1
        if display_name:
            doc.display_name = display_name
        if toll_routes:
            doc.toll_routes = json.dumps(toll_routes, ensure_ascii=False) if isinstance(toll_routes, list) else toll_routes
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.new_doc("Vehicle Toll Config")
        doc.vehicle = vehicle
        doc.display_name = display_name or vehicle
        doc.is_active = 1
        doc.toll_routes = json.dumps(
            (toll_routes if isinstance(toll_routes, list) else json.loads(toll_routes))
            if toll_routes else get_default_toll_routes(),
            ensure_ascii=False
        )
        doc.opening_balance_default = flt(opening_balance)
        doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "config_name": doc.name}

@frappe.whitelist()
def remove_vehicle_from_toll(vehicle_config):
    """从高速费管理中停用车辆（不删除历史数据）"""
    if not frappe.db.exists("Vehicle Toll Config", vehicle_config):
        frappe.throw(_("车辆配置不存在！"))
    frappe.db.set_value("Vehicle Toll Config", vehicle_config, "is_active", 0)
    frappe.db.commit()
    return {"success": True}

@frappe.whitelist()
def update_vehicle_toll_routes(vehicle_config, toll_routes):
    """更新车辆的收费站列配置"""
    if not frappe.db.exists("Vehicle Toll Config", vehicle_config):
        frappe.throw(_("车辆配置不存在！"))
    if isinstance(toll_routes, list):
        toll_routes = json.dumps(toll_routes, ensure_ascii=False)
    frappe.db.set_value("Vehicle Toll Config", vehicle_config, "toll_routes", toll_routes)
    frappe.db.commit()
    return {"success": True}
