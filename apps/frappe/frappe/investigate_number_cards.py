import frappe
import json

def execute():
    # Fetch number cards that might be relevant
    cards = frappe.get_all("Number Card", fields=["name", "document_type", "function", "aggregate_function_based_on", "filters_json"])
    relevant_cards = []
    for card in cards:
        if "采购" in card.name or "油耗" in card.name or "报销" in card.name or "油卡" in card.name:
            relevant_cards.append(card)
            
    print(json.dumps(relevant_cards, indent=2, ensure_ascii=False))
