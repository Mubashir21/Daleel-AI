import asyncio
import json
import os

from ingestion.pipeline import scrape_urls
from ingestion.parser import parse_page
from processing.chunker import create_chunk_objects
from processing.embedder import build_embedding_input, safe_embed_batch
from backend.app.db.upsert_vectors import run_upsert

RAW_DELTA_FILE = "data/raw/islamqa_delta.jsonl"
CHUNKS_DELTA_FILE = "data/processed/chunks_delta.jsonl"
EMBEDDED_DELTA_FILE = "data/processed/embedded_chunks_delta.jsonl"

EMBED_BATCH_SIZE = 100


def process_changed_docs(entries):
    """
    entries: list of {"url", "lastmod", "id"} that need to be (re)scraped and
    (re)indexed. Runs scrape -> parse -> chunk -> embed -> upsert for just
    this subset, overwriting the delta files fresh each call. This is the
    single reprocess path shared by the weekly incremental update and the
    one-time lastmod backfill. Returns the number of docs processed.
    """
    if not entries:
        return 0

    os.makedirs(os.path.dirname(RAW_DELTA_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(CHUNKS_DELTA_FILE), exist_ok=True)

    lastmod_by_url = {entry["url"]: entry["lastmod"] for entry in entries}
    pages = asyncio.run(scrape_urls(entries))

    raw_records = []
    for url, html in pages:
        if not html:
            print(f"[UPDATE] Failed to scrape {url}, skipping")
            continue
        raw_records.append(parse_page(html, url, lastmod=lastmod_by_url.get(url)))

    with open(RAW_DELTA_FILE, "w", encoding="utf-8") as f:
        for record in raw_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    chunk_records = []
    for record in raw_records:
        chunk_records.extend(create_chunk_objects(record))

    with open(CHUNKS_DELTA_FILE, "w", encoding="utf-8") as f:
        for chunk in chunk_records:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    with open(EMBEDDED_DELTA_FILE, "w", encoding="utf-8") as f:
        for i in range(0, len(chunk_records), EMBED_BATCH_SIZE):
            batch = chunk_records[i:i + EMBED_BATCH_SIZE]
            texts = [build_embedding_input(chunk) for chunk in batch]
            embeddings = safe_embed_batch(texts)

            for chunk, embedding in zip(batch, embeddings):
                chunk["embedding"] = embedding
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    if chunk_records:
        run_upsert(EMBEDDED_DELTA_FILE, delete_stale=True)

    return len(raw_records)
