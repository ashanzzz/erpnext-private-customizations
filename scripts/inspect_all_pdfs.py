import sys
import pypdf
sys.stdout.reconfigure(encoding='utf-8')
for fpath in [
    r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.user_uploaded\media_1786978206826.pdf",
    r"C:\Users\ashan\.gemini\antigravity\brain\062db5c0-afb5-4a31-90f4-1728b7cf9460\.user_uploaded\media_1786978206886.pdf"
]:
    print(f"=== {fpath} ===")
    r = pypdf.PdfReader(fpath)
    for p in r.pages:
        print(p.extract_text())
