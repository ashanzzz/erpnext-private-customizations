import sys
import pypdf
sys.stdout.reconfigure(encoding='utf-8')
reader = pypdf.PdfReader(r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.user_uploaded\media_1786978206771.pdf")
print("=== EXTRACTED TEXT ===")
for p in reader.pages:
    print(p.extract_text())
