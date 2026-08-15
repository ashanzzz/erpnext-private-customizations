"""Server-side reimbursement domain services."""

from __future__ import annotations

from collections.abc import Iterable

import frappe
from frappe import _
from frappe.utils import flt


ACTIVE_RESERVATION_STATUSES = ("Draft", "Submitted")


def normalize_names(values: str | Iterable[str] | None) -> list[str]:
    """Return safe, de-duplicated document names from RPC input."""
    if isinstance(values, str):
        values = frappe.parse_json(values)
    if not isinstance(values, Iterable):
        return []
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def import_purchase_invoice_items(
    reimbursement_request_name: str,
    purchase_invoice_names: str | Iterable[str] | None = None,
    purchase_invoice_item_names: str | Iterable[str] | None = None,
) -> dict:
    """Import permitted, unpaid Purchase Invoice lines into a saved draft.

    The browser only supplies source names.  Amounts, source snapshots, and
    reservations are recalculated on the server immediately before writing.
    """
    request = frappe.get_doc("Reimbursement Request", reimbursement_request_name)
    request.check_permission("write")
    if not request.company:
        frappe.throw(_("请先填写公司并保存报销申请草稿。"))

    candidates = get_purchase_invoice_item_candidates(
        request.company,
        purchase_invoice_names,
        purchase_invoice_item_names,
        {row.source_pi_item for row in request.get("invoice_items") if row.source_pi_item},
    )
    _assert_sources_available(candidates, request.name)
    for candidate in candidates:
        request.append("invoice_items", candidate["row"])
        _create_reservation(request.name, candidate)

    request.save()
    return {
        "imported_count": len(candidates),
        "imported_amount": sum(flt(candidate["row"]["amount"]) for candidate in candidates),
    }


def get_purchase_invoice_item_candidates(
    company: str,
    purchase_invoice_names: str | Iterable[str] | None = None,
    purchase_invoice_item_names: str | Iterable[str] | None = None,
    existing_sources: set[str] | None = None,
) -> list[dict]:
    """Return server-verified source snapshots without writing a reimbursement draft."""
    if not company:
        frappe.throw(_("请先填写公司。"))

    invoice_names = normalize_names(purchase_invoice_names)
    requested_item_names = set(normalize_names(purchase_invoice_item_names))
    if not invoice_names and requested_item_names:
        invoice_names = frappe.get_all(
            "Purchase Invoice Item",
            filters={"name": ["in", requested_item_names]},
            pluck="parent",
        )
    if not invoice_names:
        frappe.throw(_("请选择至少一张采购发票。"))

    permitted_invoices = frappe.get_list(
        "Purchase Invoice",
        filters={
            "name": ["in", invoice_names],
            "company": company,
            "docstatus": 1,
            "outstanding_amount": [">", 0],
        },
        fields=["name"],
        order_by="posting_date desc, name desc",
        page_length=len(invoice_names),
    )
    permitted_names = {row.name for row in permitted_invoices}
    unavailable = [name for name in invoice_names if name not in permitted_names]
    if unavailable:
        frappe.throw(_("所选采购发票不可导入、已付清、公司不一致或没有读取权限：{0}").format(", ".join(unavailable)))

    candidates = []
    for invoice_name in invoice_names:
        invoice = frappe.get_doc("Purchase Invoice", invoice_name)
        invoice.check_permission("read")
        selected_items = [
            item for item in invoice.items
            if not requested_item_names or item.name in requested_item_names
        ]
        if requested_item_names and not selected_items:
            continue
        candidates.extend(_make_candidates(invoice, selected_items, existing_sources or set()))

    if not candidates:
        frappe.throw(_("没有可新增的采购发票明细。可能已导入当前单据，或没有选择有效明细。"))

    return candidates


def get_unpaid_purchase_invoice_picker_rows(
    company: str,
    filters: dict | str | None = None,
) -> list[dict]:
    """Return rows for the single-screen unpaid-invoice picker.

    The result is intentionally capped at 100 invoices.  This keeps the Desk
    dialog responsive while users narrow the explicit filters above the list.
    """
    filters = _normalize_filters(filters)
    filters["company"] = company
    invoices, item_rows = _find_unpaid_purchase_invoices(filters)
    item_summaries: dict[str, list[str]] = {row.name: [] for row in invoices}
    for item in item_rows:
        label = item.item_name or item.item_code or item.description
        if label and label not in item_summaries[item.parent]:
            item_summaries[item.parent].append(label)

    return [
        {
            "name": row.name,
            "bill_no": row.bill_no,
            "bill_date": row.bill_date,
            "custom_invoice_type": row.custom_invoice_type,
            "supplier": row.supplier,
            "outstanding_amount": flt(row.outstanding_amount),
            "item_summary": "、".join(item_summaries.get(row.name, [])[:4]),
        }
        for row in invoices
    ]


def search_unpaid_purchase_invoices(
    txt: str = "",
    start: int | str = 0,
    page_len: int | str = 20,
    filters: dict | str | None = None,
) -> list[tuple]:
    """Backward-compatible Frappe link search for the former native picker."""
    filters = _normalize_filters(filters)
    invoices, _ = _find_unpaid_purchase_invoices(filters, txt)
    start, page_len = max(int(start or 0), 0), min(max(int(page_len or 20), 1), 100)
    return [
        (
            row.name,
            row.bill_no or "",
            row.supplier or "",
            row.custom_invoice_type or "",
            row.bill_date or "",
            flt(row.outstanding_amount),
        )
        for row in invoices[start : start + page_len]
    ]


def _find_unpaid_purchase_invoices(filters: dict, txt: str = "") -> tuple[list, list]:
    """Find permission-scoped parent invoices and their display-only item rows."""
    company = filters.get("company")
    if not company:
        return [], []

    invoice_filters: list[list] = [
        ["company", "=", company],
        ["docstatus", "=", 1],
        ["outstanding_amount", ">", 0],
    ]
    _add_like_filter(invoice_filters, "bill_no", filters.get("bill_no"))
    _add_exact_filter(invoice_filters, "custom_invoice_type", filters.get("custom_invoice_type"))
    _add_like_filter(invoice_filters, "supplier", filters.get("supplier"))
    _add_range_filter(invoice_filters, "bill_date", filters.get("bill_date_from"), filters.get("bill_date_to"))
    _add_range_filter(
        invoice_filters,
        "outstanding_amount",
        filters.get("min_outstanding_amount"),
        filters.get("max_outstanding_amount"),
        minimum_operator=">",
    )
    or_filters = []
    if txt := txt.strip():
        search_text = f"%{txt}%"
        or_filters = [["name", "like", search_text], ["bill_no", "like", search_text], ["supplier", "like", search_text]]

    invoices = frappe.get_list(
        "Purchase Invoice",
        filters=invoice_filters,
        or_filters=or_filters,
        fields=["name", "bill_no", "bill_date", "custom_invoice_type", "supplier", "outstanding_amount"],
        order_by="bill_date desc, posting_date desc, name desc",
        page_length=100,
    )
    if not invoices:
        return [], []

    allowed_names = [row.name for row in invoices]
    item_filters: dict = {"parent": ["in", allowed_names], "parenttype": "Purchase Invoice"}
    if item_name := (filters.get("item_name") or "").strip():
        item_filters["item_name"] = ["like", f"%{item_name}%"]

    # Child rows do not have independent Desk permissions.  Parent invoices
    # above are already permission-scoped; this query only adds display text.
    item_rows = frappe.get_all(
        "Purchase Invoice Item",
        filters=item_filters,
        fields=["parent", "item_name", "item_code", "description"],
        order_by="idx asc",
        page_length=1000,
    )
    if filters.get("item_name"):
        matched_names = {row.parent for row in item_rows}
        invoices = [row for row in invoices if row.name in matched_names]
    return invoices, item_rows


def _normalize_filters(filters: dict | str | None) -> dict:
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    return filters if isinstance(filters, dict) else {}


def _add_like_filter(target: list[list], fieldname: str, value: str | None) -> None:
    if value := (value or "").strip():
        target.append([fieldname, "like", f"%{value}%"])


def _add_exact_filter(target: list[list], fieldname: str, value: str | None) -> None:
    if value := (value or "").strip():
        target.append([fieldname, "=", value])


def _add_range_filter(
    target: list[list],
    fieldname: str,
    minimum: str | float | None,
    maximum: str | float | None,
    minimum_operator: str = ">=",
) -> None:
    if minimum not in (None, "") and maximum not in (None, ""):
        target.append([fieldname, "between", [minimum, maximum]])
    elif minimum not in (None, ""):
        target.append([fieldname, minimum_operator, minimum])
    elif maximum not in (None, ""):
        target.append([fieldname, "<=", maximum])


def reserve_request_sources(request) -> None:
    """Create durable claims when a browser-only selection is first saved."""
    rows = [row for row in request.get("invoice_items") if row.source_pi_item]
    if not rows:
        return
    active_sources = set(
        frappe.get_all(
            "Reimbursement Source Reservation",
            filters={"reimbursement_request": request.name, "status": ["in", ACTIVE_RESERVATION_STATUSES]},
            pluck="source_purchase_invoice_item",
        )
    )
    candidates = [
        {"source_pi": row.source_pi, "source_pi_item": row.source_pi_item, "row": {"amount": row.amount}}
        for row in rows
        if row.source_pi_item not in active_sources
    ]
    _assert_sources_available(candidates, request.name)
    for candidate in candidates:
        _create_reservation(request.name, candidate)


def _create_reservation(request_name: str, candidate: dict) -> None:
    reservation = frappe.get_doc(
        {
            "doctype": "Reimbursement Source Reservation",
            "reimbursement_request": request_name,
            "source_purchase_invoice": candidate["source_pi"],
            "source_purchase_invoice_item": candidate["source_pi_item"],
            "reserved_amount": candidate["row"]["amount"],
            "status": "Draft",
        }
    )
    reservation.insert()


def release_removed_reservations(request) -> None:
    """Release draft claims that no longer have a corresponding child row."""
    source_items = {row.source_pi_item for row in request.get("invoice_items") if row.source_pi_item}
    reservations = frappe.get_all(
        "Reimbursement Source Reservation",
        filters={
            "reimbursement_request": request.name,
            "status": ["in", ACTIVE_RESERVATION_STATUSES],
        },
        pluck="name",
    )
    for name in reservations:
        reservation = frappe.get_doc("Reimbursement Source Reservation", name)
        if reservation.source_purchase_invoice_item not in source_items:
            reservation.status = "Released"
            reservation.save()


def release_all_reservations(request) -> None:
    """Release all claims when a draft reimbursement request is deleted."""
    for name in frappe.get_all(
        "Reimbursement Source Reservation",
        filters={
            "reimbursement_request": request.name,
            "status": ["in", ACTIVE_RESERVATION_STATUSES],
        },
        pluck="name",
    ):
        reservation = frappe.get_doc("Reimbursement Source Reservation", name)
        reservation.status = "Released"
        reservation.save()


def _make_candidates(invoice, items, existing_sources: set[str]) -> list[dict]:
    items = [item for item in items if item.name not in existing_sources]
    source_amounts = [_gross_amount(item) for item in items]
    if not items or not sum(source_amounts):
        return []
    total_source_amount = sum(source_amounts)
    outstanding = flt(invoice.outstanding_amount)
    remaining = outstanding
    candidates = []
    for index, item in enumerate(items):
        amount = remaining if index == len(items) - 1 else flt(source_amounts[index] / total_source_amount * outstanding, 2)
        remaining = flt(remaining - amount, 2)
        candidates.append(
            {
                "source_pi": invoice.name,
                "source_pi_item": item.name,
                "row": {
                    "item_name": item.item_name,
                    "description": item.description,
                    "qty": item.qty,
                    "uom": item.uom,
                    "rate": flt(amount / item.qty, 2) if flt(item.qty) else amount,
                    "amount": amount,
                    "invoice_no": invoice.bill_no,
                    "supplier": invoice.supplier,
                    "source_pi": invoice.name,
                    "source_pi_item": item.name,
                },
            }
        )
    return candidates


def _gross_amount(item) -> float:
    return flt(getattr(item, "custom_gross_amount", 0) or item.amount)


def _assert_sources_available(candidates: list[dict], current_request: str) -> None:
    keys = [candidate["source_pi_item"] for candidate in candidates]
    conflicts = frappe.get_all(
        "Reimbursement Source Reservation",
        filters={"active_source_key": ["in", keys]},
        fields=["source_purchase_invoice_item", "reimbursement_request"],
    )
    other_requests = sorted({row.reimbursement_request for row in conflicts if row.reimbursement_request != current_request})
    if other_requests:
        frappe.throw(_("以下来源明细已被其他报销草稿占用：{0}").format(", ".join(other_requests)))
