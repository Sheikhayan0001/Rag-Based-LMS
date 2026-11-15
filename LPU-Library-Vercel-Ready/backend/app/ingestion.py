from pathlib import Path
import fitz
from .rag import upsert_document
SUPPORTED={".pdf",".txt",".md"}
def extract_file(path:Path):
    if path.suffix.lower()==".pdf":
        pages=[]
        with fitz.open(path) as pdf:
            for page_no,page in enumerate(pdf,start=1):
                text=page.get_text("text")
                if text.strip(): pages.append((page_no,text))
        return pages
    if path.suffix.lower() in {".txt",".md"}: return [(None,path.read_text(encoding="utf-8",errors="ignore"))]
    return []
def ingest_file(path:Path,book_id=None,title=None,author=None):
    total=0
    for page,text in extract_file(path):
        meta={"document":path.name,"page":page,"book_id":book_id or "","title":title or path.stem,"author":author or "","file_type":path.suffix.lower(),"corpus":"demo" if path.parts and "corpus" in path.parts else "admin_upload"}
        total+=upsert_document(text,meta)
    return total
def ingest_path(path:Path):
    targets=[path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    report=[]
    for file in targets:
        if file.suffix.lower() not in SUPPORTED: continue
        try: report.append({"file":file.name,"chunks":ingest_file(file),"status":"ingested"})
        except Exception as exc: report.append({"file":file.name,"chunks":0,"status":"error","error":str(exc)})
    return report
