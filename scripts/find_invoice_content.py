import json

with open(r'C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if '代收国家重大水利工程建设基金' in line:
            obj = json.loads(line)
            content = obj.get('content', '')
            # 找到发票表格段落
            if '序号\t发票代码' in content or '圣凯' in content:
                print("FOUND INVOICE CONTENT:")
                idx = content.find('序号\t发票代码')
                if idx != -1:
                    print(content[idx:idx+3500])
                else:
                    print(content[:3000])
