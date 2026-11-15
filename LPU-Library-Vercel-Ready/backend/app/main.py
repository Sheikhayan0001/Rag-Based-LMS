from pathlib import Path
from uuid import uuid4
import asyncio, secrets, tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Header
from fastapi.staticfiles import StaticFiles
from .config import settings, local_path
from .schemas import ChatRequest, ChatResponse, Source
from .db import init_db, add_message, get_messages, delete_conversation, chunk_count
from .rag import retrieve, generate_answer
from .ingestion import ingest_file, ingest_path
from .catalogue import BOOKS

app=FastAPI(title=settings.app_name,version="2.0.0")
ROOT=Path(__file__).resolve().parents[2]
FRONTEND_DIR=ROOT/"frontend"
@app.on_event("startup")
def startup():
    try: init_db()
    except Exception as exc: print(f"Database initialization deferred/failed: {exc}")
@app.get("/api/health")
def health():
    try:
        count=chunk_count()
        ready=bool(settings.ai_gateway_api_key and settings.database_url)
        return {"status":"ok" if ready and count else "degraded","vector_chunks":count,"llm_model":settings.chat_model,"provider":"Vercel AI Gateway","database_configured":bool(settings.database_url),"ai_gateway_configured":bool(settings.ai_gateway_api_key)}
    except Exception as exc:
        return {"status":"degraded","detail":str(exc),"vector_chunks":0,"llm_model":settings.chat_model,"provider":"Vercel AI Gateway"}
@app.get("/api/books")
def books(q:str=""):
    term=q.lower().strip(); return [b for b in BOOKS if not term or term in (b["title"]+" "+b["author"]+" "+b["category"]).lower()]
@app.get("/api/books/{book_id}")
def book_detail(book_id:str):
    book=next((b for b in BOOKS if b["id"]==book_id),None)
    if not book: raise HTTPException(404,"Book not found")
    return book
@app.post("/api/chat",response_model=ChatResponse)
def chat(payload:ChatRequest):
    conversation_id=payload.conversation_id or str(uuid4())
    try:
        history=get_messages(conversation_id); matches=retrieve(payload.question)
        answer=generate_answer(payload.question,matches,history)
        add_message(conversation_id,"user",payload.question); add_message(conversation_id,"assistant",answer)
    except Exception as exc: raise HTTPException(503,f"RAG service unavailable: {exc}")
    sources=[]
    for item in matches:
        m=item["metadata"] or {}; sources.append(Source(document=m.get("document","unknown"),page=m.get("page") or None,chunk_id=str(m.get("chunk_index","")),book_id=m.get("book_id") or None,title=m.get("title") or None,author=m.get("author") or None,excerpt=item["text"][:420]))
    return ChatResponse(conversation_id=conversation_id,answer=answer,sources=sources,retrieval_count=len(matches),grounded=bool(matches))
@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id:str): return {"conversation_id":conversation_id,"messages":get_messages(conversation_id)}
@app.delete("/api/conversations/{conversation_id}")
def clear_conversation(conversation_id:str): delete_conversation(conversation_id); return {"deleted":True}
def verify_admin(key):
    if not settings.admin_ingest_key: raise HTTPException(503,"ADMIN_INGEST_KEY is not configured")
    if not key or not secrets.compare_digest(key,settings.admin_ingest_key): raise HTTPException(401,"Invalid admin key")
@app.post("/api/admin/ingest")
async def upload_document(file:UploadFile=File(...),x_admin_key:str|None=Header(default=None)):
    verify_admin(x_admin_key)
    suffix=Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf",".txt",".md"}: raise HTTPException(415,"Only PDF, TXT and MD files are supported")
    content=await file.read(settings.max_upload_mb*1024*1024+1)
    if len(content)>settings.max_upload_mb*1024*1024: raise HTTPException(413,f"File exceeds {settings.max_upload_mb} MB limit; use smaller files")
    safe=Path(file.filename or ("upload"+suffix)).name
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix,delete=False) as f: f.write(content); tmp=Path(f.name)
        count=await asyncio.to_thread(ingest_file,tmp,title=safe)
    except Exception as exc: raise HTTPException(500,f"Ingestion failed: {exc}")
    finally:
        if tmp: tmp.unlink(missing_ok=True)
    return {"filename":safe,"chunks_indexed":count,"persistent":True}
@app.post("/api/admin/ingest-demo")
def ingest_demo(x_admin_key:str|None=Header(default=None)):
    verify_admin(x_admin_key)
    report=ingest_path(local_path("data/corpus"))
    successful=[item for item in report if item.get("status")=="ingested"]
    failed=[item for item in report if item.get("status")!="ingested"]
    return {"results":report,"ingested_documents":len(successful),"failed_documents":len(failed),"chunks_indexed":sum(x.get("chunks",0) for x in successful),"vector_chunks_total":chunk_count()}

# Keep the frontend mount LAST so /api routes above always take precedence.
# Vercel's FastAPI runtime can promote this mounted directory to its CDN.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
