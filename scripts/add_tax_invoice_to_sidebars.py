import os
import json
import glob

def update_sidebars():
    sidebar_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\ashan_cn_procurement\workspace_sidebar"
    files = glob.glob(os.path.join(sidebar_dir, "*.json"))

    tax_inv_item = {
        "label": "税局发票",
        "link_type": "Page",
        "type": "Link",
        "link_to": "tax-invoice-center",
        "url": "/desk/tax-invoice-center",
        "child": 1,
        "collapsible": 0,
        "indent": 0,
        "keep_closed": 0,
        "show_arrow": 0,
        "doctype": "Workspace Sidebar Item"
    }

    for f_path in files:
        with open(f_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = data.get("items", [])
        # Check if tax-invoice-center already in items
        if any(it.get("link_to") == "tax-invoice-center" for it in items):
            continue

        new_items = []
        for it in items:
            if it.get("link_to") == "Purchase Invoice":
                new_items.append(tax_inv_item)
            new_items.append(it)

        data["items"] = new_items

        with open(f_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated sidebar: {os.path.basename(f_path)}")

if __name__ == '__main__':
    update_sidebars()
