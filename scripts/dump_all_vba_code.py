import os
import sys
from oletools.olevba import VBA_Parser

sys.stdout.reconfigure(encoding='utf-8')

xlsm_path = r"d:\SynologyDrive团队\antigravity\erpnext16\temp_screenshots\202606吉众人事综合.xlsm"
vb = VBA_Parser(xlsm_path)

output_file = r"d:\SynologyDrive团队\antigravity\erpnext16\scripts\extracted_vba_macros.txt"

with open(output_file, 'w', encoding='utf-8') as out:
    if vb.detect_vba_macros():
        for (filename, stream_path, vba_filename, vba_code) in vb.extract_macros():
            out.write(f"\n{'='*60}\n")
            out.write(f"MODULE: {vba_filename} | STREAM: {stream_path}\n")
            out.write(f"{'='*60}\n\n")
            out.write(vba_code)
            out.write("\n\n")
    else:
        out.write("No VBA macros found.\n")

print(f"All VBA macros extracted to: {output_file}")
