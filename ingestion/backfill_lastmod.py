"""
One-time script. Run once, locally, before turning on the scheduled
incremental update job.

The ~39k chunks already in Pinecone have no `lastmod` metadata yet, so the
incremental diff (sitemap lastmod vs Pinecone-stored lastmod) has nothing to
compare against. We can't just stamp today's sitemap lastmod onto everything
blindly either — if a page was edited by IslamQA between our original scrape
and today, we'd never know, and the incremental job would treat it as already
up to date forever.

Instead: re-scrape every current sitemap page and compare it against
data/raw/islamqa.jsonl (the original scrape, still present locally). If the
content matches, nothing has actually changed since ingestion — just tag the
lastmod metadata. If it differs (or the doc is brand new), run it through the
normal reprocess pipeline so the correction actually lands.
"""
import asyncio
import json

from ingestion.io import parse_sitemap
from ingestion.utils import extract_id
from ingestion.pipeline import scrape_urls
from ingestion.parser import parse_page
from ingestion.update_pipeline import process_changed_docs
from backend.app.core.config import settings
from backend.app.db.pinecone_client import get_index

SITEMAP_URL = "https://islamqa.info/sitemaps/en/answers/1/sitemap.xml"
LOCAL_RAW_FILE = "data/raw/islamqa.jsonl"
COMPARE_FIELDS = ["title", "question", "summary", "answer"]


def load_local_raw(file_path):
    records = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            records[record["id"]] = record
    return records


def content_matches(local_record, fresh_record):
    return all(
        local_record.get(field) == fresh_record.get(field)
        for field in COMPARE_FIELDS
    )


def run_backfill():
    local_records = load_local_raw(LOCAL_RAW_FILE)

    sitemap_entries = parse_sitemap(SITEMAP_URL)
    for entry in sitemap_entries:
        entry["id"] = extract_id(entry["url"])

    sitemap_ids = {entry["id"] for entry in sitemap_entries}
    removed_ids = set(local_records) - sitemap_ids
    if removed_ids:
        print(f"[BACKFILL] {len(removed_ids)} docs no longer in sitemap, skipping (deletions out of scope)")

    print(f"[BACKFILL] Re-scraping {len(sitemap_entries)} pages to check for drift since original ingestion...")
    lastmod_by_url = {entry["url"]: entry["lastmod"] for entry in sitemap_entries}
    pages = asyncio.run(scrape_urls(sitemap_entries))

    verified_unchanged = []  # (doc_id, lastmod)
    to_reprocess = []        # {"url", "lastmod", "id"}

    for url, html in pages:
        if not html:
            print(f"[BACKFILL] Failed to scrape {url}, leaving untagged for a future run")
            continue

        doc_id = extract_id(url)
        lastmod = lastmod_by_url[url]
        fresh_record = parse_page(html, url, lastmod=lastmod)
        local_record = local_records.get(doc_id)

        if local_record is not None and content_matches(local_record, fresh_record):
            verified_unchanged.append((doc_id, lastmod))
        else:
            to_reprocess.append({"url": url, "lastmod": lastmod, "id": doc_id})

    print(f"[BACKFILL] {len(verified_unchanged)} unchanged (tagging lastmod only), "
          f"{len(to_reprocess)} new/changed (reprocessing)")

    index = get_index()
    for doc_id, lastmod in verified_unchanged:
        index.update(
            id=f"{doc_id}_chunk_0",
            set_metadata={"lastmod": lastmod},
            namespace=settings.pinecone_namespace,
        )

    processed = process_changed_docs(to_reprocess)

    print(f"[BACKFILL DONE] {len(verified_unchanged)} tagged, {processed} reprocessed, "
          f"{len(removed_ids)} skipped (removed from sitemap)")


if __name__ == "__main__":
    run_backfill()
