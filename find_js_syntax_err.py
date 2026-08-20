with open(r"d:\SynologyDrive团队\antigravity\erpnext16\ashan_cn_procurement\ashan_cn_procurement\public\js\purchase_invoice_tax_calculator.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

stack = []
for i, line in enumerate(lines, 1):
    for char in line:
        if char in '({[':
            stack.append((char, i))
        elif char in ')}]':
            if not stack:
                print(f"Unexpected closing {char} at line {i}")
            else:
                top, top_i = stack.pop()
                if (top == '(' and char != ')') or (top == '{' and char != '}') or (top == '[' and char != ']'):
                    print(f"Mismatched {top} (line {top_i}) with {char} at line {i}")

if stack:
    print(f"Unclosed items: {stack}")
