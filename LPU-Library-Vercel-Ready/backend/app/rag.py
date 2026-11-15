import hashlib, requests
from .config import settings
from .db import connect

GATEWAY="https://ai-gateway.vercel.sh/v1"
def _headers():
    if not settings.ai_gateway_api_key:
        raise RuntimeError("AI_GATEWAY_API_KEY is not configured in Vercel environment variables.")
    return {"Authorization":f"Bearer {settings.ai_gateway_api_key}","Content-Type":"application/json"}

def embed_texts(texts):
    response=requests.post(GATEWAY+"/embeddings",headers=_headers(),json={"model":settings.embedding_model,"input":texts},timeout=40)
    response.raise_for_status()
    data=response.json().get("data",[])
    if len(data) != len(texts):
        raise RuntimeError(f"Embedding service returned {len(data)} vectors for {len(texts)} inputs.")
    vectors=[item["embedding"] for item in sorted(data,key=lambda x:x.get("index",0))]
    if any(len(vector) != 1536 for vector in vectors):
        raise RuntimeError("Embedding dimension mismatch. The configured model must return 1536-dimensional vectors.")
    return vectors

def split_text(text):
    text=" ".join(text.split())
    if not text: return []
    size,overlap=settings.chunk_size,settings.chunk_overlap
    chunks=[]; start=0
    while start<len(text):
        end=min(start+size,len(text))
        if end<len(text):
            boundary=text.rfind(" ",start+int(size*.75),end)
            if boundary>start: end=boundary
        chunks.append(text[start:end].strip())
        if end>=len(text): break
        start=max(end-overlap,start+1)
    return [c for c in chunks if c]

def upsert_document(text, metadata):
    chunks=split_text(text)
    if not chunks:return 0
    vectors=embed_texts(chunks)
    source=metadata.get("document","unknown")
    rows=[]
    for i,(chunk,vector) in enumerate(zip(chunks,vectors)):
        digest=hashlib.sha256(f"{source}:{metadata.get('page')}:{i}:{chunk}".encode()).hexdigest()
        clean={k:(v if v is not None else "") for k,v in {**metadata,"chunk_index":i}.items() if isinstance(v,(str,int,float,bool))}
        rows.append((digest,chunk,clean,"["+",".join(str(float(x)) for x in vector)+"]"))
    with connect() as con:
        con.executemany("""INSERT INTO library_chunks(id,content,metadata,embedding) VALUES (%s,%s,%s,%s::vector)
        ON CONFLICT(id) DO UPDATE SET content=EXCLUDED.content, metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding""",
        [(a,b,__import__('json').dumps(c),d) for a,b,c,d in rows])
    return len(rows)

def retrieve(question):
    vector=embed_texts([question])[0]
    v="["+",".join(str(float(x)) for x in vector)+"]"
    with connect() as con:
        rows=con.execute("""SELECT content,metadata,(embedding <=> %s::vector) AS distance
        FROM library_chunks ORDER BY embedding <=> %s::vector LIMIT %s""",(v,v,settings.top_k)).fetchall()
    return [{"text":r["content"],"metadata":r["metadata"],"distance":float(r["distance"])} for r in rows]

def generate_answer(question,retrieved,history):
    context="\n\n".join(f"[Source {i+1}] {x['metadata'].get('document','unknown')} (page {x['metadata'].get('page') or 'not specified'}):\n{x['text']}" for i,x in enumerate(retrieved))
    if not retrieved: context="No relevant library passages were retrieved."
    system=("You are the LPU Library AI Librarian. Answer clearly and helpfully. Use ONLY the supplied library context for factual claims about library materials. If context is missing or insufficient, say so plainly. Never invent book titles, authors, quotations, page numbers, or citations. Cite supporting passages inline as [Source 1], [Source 2].")
    messages=[{"role":"system","content":system}]
    for item in history[-6:]:
        if item["role"] in ("user","assistant"): messages.append({"role":item["role"],"content":item["content"][:3500]})
    messages.append({"role":"user","content":f"LIBRARY CONTEXT:\n{context}\n\nSTUDENT QUESTION:\n{question}"})
    response=requests.post(GATEWAY+"/chat/completions",headers=_headers(),json={"model":settings.chat_model,"messages":messages,"temperature":0.2},timeout=50)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
