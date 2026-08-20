import os
import json
import glob

def update_sidebars():
    sidebar_dir = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\ashan_cn_procurement\workspace_sidebar"
    for fpath in glob.glob(os.path.join(sidebar_dir, "*.json")):
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        items = data.get("items", [])
        new_items = []
        for it in items:
            if it.get("link_to") == "property-settlement-workbench":
                # Add 水电费月结工作台
                new_items.append({
                    "label": "水电费月结工作台",
                    "link_type": "Page",
                    "type": "Link",
                    "link_to": "property-settlement-workbench",
                    "child": 1,
                    "collapsible": 0,
                    "indent": 0,
                    "keep_closed": 0,
                    "show_arrow": 0,
                    "doctype": "Workspace Sidebar Item"
                })
                # Add 房租与物业费工作台
                new_items.append({
                    "label": "房租与物业费工作台",
                    "link_type": "Page",
                    "type": "Link",
                    "link_to": "lease-settlement-workbench",
                    "child": 1,
                    "collapsible": 0,
                    "indent": 0,
                    "keep_closed": 0,
                    "show_arrow": 0,
                    "doctype": "Workspace Sidebar Item"
                })
            else:
                new_items.append(it)
        data["items"] = new_items

        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated sidebar: {os.path.basename(fpath)}")

def update_workspace():
    ws_path = r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\ashan_cn_procurement\workspace\property_and_lease\property_and_lease.json"
    with open(ws_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Update shortcuts
    shortcuts = data.get("shortcuts", [])
    new_shortcuts = []
    for sc in shortcuts:
        if sc.get("link_to") == "property-settlement-workbench":
            new_shortcuts.append({
                "type": "Page",
                "link_to": "property-settlement-workbench",
                "label": "水电费月结",
                "doctype": "Workspace Shortcut"
            })
            new_shortcuts.append({
                "type": "Page",
                "link_to": "lease-settlement-workbench",
                "label": "房租物业月结",
                "doctype": "Workspace Shortcut"
            })
        else:
            new_shortcuts.append(sc)
    data["shortcuts"] = new_shortcuts

    # Update links
    links = data.get("links", [])
    new_links = []
    for l in links:
        if l.get("link_to") == "property-settlement-workbench":
            new_links.append({
                "type": "Link",
                "label": "水电费月结工作台",
                "hidden": 0,
                "link_type": "Page",
                "link_to": "property-settlement-workbench",
                "onboard": 0,
                "is_query_report": 0,
                "link_count": 0,
                "doctype": "Workspace Link"
            })
            new_links.append({
                "type": "Link",
                "label": "房租与物业费工作台",
                "hidden": 0,
                "link_type": "Page",
                "link_to": "lease-settlement-workbench",
                "onboard": 0,
                "is_query_report": 0,
                "link_count": 0,
                "doctype": "Workspace Link"
            })
        else:
            new_links.append(l)
    data["links"] = new_links

    with open(ws_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"Updated workspace: {os.path.basename(ws_path)}")

if __name__ == "__main__":
    update_sidebars()
    update_workspace()
