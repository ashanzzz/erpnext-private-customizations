import json

log_path = r"C:\Users\ashan\.gemini\antigravity\brain\49a429d8-4554-471e-974e-f9d70d7ec2f8\.system_generated\logs\transcript.jsonl"
with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        data = json.loads(line)
        if data.get('step_index') in [3060, 3061, 3062, 3063, 3064, 3065]:
            print(f"Step {data.get('step_index')}:", json.dumps(data, ensure_ascii=False)[:500])

