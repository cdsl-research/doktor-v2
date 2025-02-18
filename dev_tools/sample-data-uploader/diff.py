import glob
import json

pdf_files = set(f.replace(".pdf", "") for f in glob.glob("*.pdf"))

with open("papers.json") as f:
    dat = json.load(f)
    reg_files = set(p["paper_url_id"] for p in dat)

print("Not found in paper.json")
for l in pdf_files - reg_files:
    print("\t", l, l + ".pdf")

print("PDF files are not found")
for l in reg_files - pdf_files:
    print("\t", l)
