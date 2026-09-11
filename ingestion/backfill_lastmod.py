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
import concurrent.futures
import json
import sys

from ingestion.io import parse_sitemap
from ingestion.utils import extract_id
from ingestion.pipeline import scrape_urls
from ingestion.parser import parse_page
from ingestion.update_pipeline import process_changed_docs
from backend.app.core.config import settings
from backend.app.db.pinecone_client import get_index

SITEMAP_URL = "https://islamqa.info/sitemaps/en/answers/1/sitemap.xml"
LOCAL_RAW_FILE = "data/raw/islamqa.jsonl"
FAILED_URLS_FILE = "data/raw/backfill_failed_urls.txt"
CHECKPOINT_FILE = "data/raw/backfill_checkpoint.json"
COMPARE_FIELDS = ["title", "question", "summary", "answer"]

# A single Pinecone call with no timeout can hang indefinitely and take the
# whole run down with it (observed firsthand: one stalled `update()` call
# blocked the tagging loop for 15+ minutes with no progress and no error).
PINECONE_CALL_TIMEOUT = 30

# Tagging is one HTTP round-trip per doc with nothing to batch (Pinecone has
# no bulk "update N docs with different metadata each" call) — sequential,
# ~15k of these would take hours. Fan them out instead, mirroring the
# scraper's bounded-concurrency pattern.
TAG_CONCURRENCY = 20


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


def run_backfill(urls_filter=None, resume=False):
    """
    urls_filter: when given, restricts the pass to just these URLs (e.g. a
    retry of whatever failed to scrape last time) instead of the whole
    sitemap. The "removed from sitemap" check only makes sense on a full
    pass, so it's skipped when filtering.

    resume: skip the (slow) re-scrape + compare phase entirely and load the
    tagging/reprocess decisions straight from CHECKPOINT_FILE, written by a
    previous run right before it started tagging. Use this if a run got
    interrupted or stuck partway through tagging — no need to pay for
    re-scraping ~15k pages again just to get back to the same decisions.
    """
    if resume:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
        verified_unchanged = [tuple(pair) for pair in checkpoint["verified_unchanged"]]
        to_reprocess = checkpoint["to_reprocess"]
        removed_ids = set(checkpoint["removed_ids"])
        still_failed = checkpoint["still_failed"]
        print(f"[BACKFILL] Resumed from checkpoint: {len(verified_unchanged)} to tag, "
              f"{len(to_reprocess)} to reprocess")
    else:
        local_records = load_local_raw(LOCAL_RAW_FILE)

        sitemap_entries = parse_sitemap(SITEMAP_URL)
        for entry in sitemap_entries:
            entry["id"] = extract_id(entry["url"])

        removed_ids = set()
        if urls_filter is not None:
            sitemap_entries = [e for e in sitemap_entries if e["url"] in urls_filter]
            print(f"[BACKFILL] Retrying {len(sitemap_entries)} previously failed URLs")
        else:
            sitemap_ids = {entry["id"] for entry in sitemap_entries}
            removed_ids = set(local_records) - sitemap_ids
            if removed_ids:
                print(f"[BACKFILL] {len(removed_ids)} docs no longer in sitemap, skipping (deletions out of scope)")

        print(f"[BACKFILL] Re-scraping {len(sitemap_entries)} pages to check for drift since original ingestion...")
        lastmod_by_url = {entry["url"]: entry["lastmod"] for entry in sitemap_entries}
        pages = asyncio.run(scrape_urls(sitemap_entries))

        verified_unchanged = []  # (doc_id, lastmod)
        to_reprocess = []        # {"url", "lastmod", "id"}
        still_failed = []

        for url, html in pages:
            if not html:
                print(f"[BACKFILL] Failed to scrape {url}, leaving untagged for a future run")
                still_failed.append(url)
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

        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "verified_unchanged": verified_unchanged,
                "to_reprocess": to_reprocess,
                "removed_ids": list(removed_ids),
                "still_failed": still_failed,
            }, f)
        print(f"[BACKFILL] Checkpoint saved to {CHECKPOINT_FILE} before tagging "
              f"(rerun with --resume if this run gets interrupted)")

    def tag_one(index, doc_id, lastmod):
        try:
            index.update(
                id=f"{doc_id}_chunk_0",
                set_metadata={"lastmod": lastmod},
                namespace=settings.pinecone_namespace,
                _request_timeout=PINECONE_CALL_TIMEOUT,
            )
            return True
        except Exception as e:
            print(f"[BACKFILL] Failed to tag {doc_id}: {e}")
            return False

    index = get_index()
    tag_failed = 0

    print(f"[BACKFILL] Tagging {len(verified_unchanged)} docs ({TAG_CONCURRENCY} at a time)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=TAG_CONCURRENCY) as executor:
        futures = [
            executor.submit(tag_one, index, doc_id, lastmod)
            for doc_id, lastmod in verified_unchanged
        ]
        for i, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            if not future.result():
                tag_failed += 1
            if i % 500 == 0:
                print(f"[BACKFILL] Tagged {i}/{len(verified_unchanged)}...")

    processed = process_changed_docs(to_reprocess)

    if still_failed:
        with open(FAILED_URLS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(still_failed))
        print(f"[BACKFILL] {len(still_failed)} URLs still failed to scrape, written to {FAILED_URLS_FILE} "
              f"(rerun with --retry-failed once ready)")

    print(f"[BACKFILL DONE] {len(verified_unchanged) - tag_failed} tagged, {tag_failed} tag failures, "
          f"{processed} reprocessed, {len(removed_ids)} skipped (removed from sitemap), "
          f"{len(still_failed)} still failing to scrape")


if __name__ == "__main__":
    if "--resume" in sys.argv:
        run_backfill(resume=True)
    elif "--retry-failed" in sys.argv:
        with open(FAILED_URLS_FILE, "r", encoding="utf-8") as f:
            retry_urls = {line.strip() for line in f if line.strip()}
        run_backfill(urls_filter=retry_urls)
    else:
        run_backfill()
