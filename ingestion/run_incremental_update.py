from ingestion.io import parse_sitemap
from ingestion.utils import extract_id
from ingestion.diff import fetch_pinecone_lastmods, classify_changes
from ingestion.update_pipeline import process_changed_docs

SITEMAP_URL = "https://islamqa.info/sitemaps/en/answers/1/sitemap.xml"


def run_incremental_update():
    entries = parse_sitemap(SITEMAP_URL)
    for entry in entries:
        entry["id"] = extract_id(entry["url"])

    stored_lastmods = fetch_pinecone_lastmods(entry["id"] for entry in entries)
    new_entries, updated_entries = classify_changes(entries, stored_lastmods)

    changed = new_entries + updated_entries
    unchanged_count = len(entries) - len(changed)

    print(f"[UPDATE] {len(new_entries)} new, {len(updated_entries)} updated, {unchanged_count} unchanged")

    if not changed:
        print("[UPDATE] Corpus is up to date, nothing to do")
        return

    processed = process_changed_docs(changed)
    print(f"[UPDATE DONE] Reprocessed {processed} docs")


if __name__ == "__main__":
    run_incremental_update()
