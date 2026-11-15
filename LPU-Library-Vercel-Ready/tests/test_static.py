from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_frontend_has_no_embedded_admin_secret():
    html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert "local-demo-key-change-me" not in html
    assert "X-Ingest-Key" not in html
    assert "X-Admin-Key" in html
    assert 'id="ragSeed"' in html
    assert "Load 18 demo notes" in html

def test_demo_corpus_contains_18_starter_notes():
    files = list((ROOT / "backend/data/corpus").glob("*.md"))
    assert len(files) == 18

def test_vercel_fastapi_entrypoint_and_cloud_storage_are_configured():
    assert (ROOT / "index.py").exists()
    main = (ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    assert 'app.mount("/", StaticFiles' in main
    assert "verify_admin(x_admin_key)" in main
    db = (ROOT / "backend/app/db.py").read_text(encoding="utf-8")
    assert "pgvector" in db or "vector(1536)" in db
