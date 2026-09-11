import asyncio
import aiohttp
from tqdm import tqdm

from ingestion.io import parse_sitemap, write_jsonl
from ingestion.parser import parse_page
from ingestion.utils import extract_id, load_existing_ids

async def fetch_page(session, url, sem):
    async with sem:
        try:
            async with session.get(url) as res:
                res.raise_for_status()
                html = await res.text()
                await asyncio.sleep(0.1)
                return url, html
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")
            return url, None


async def scrape_urls(urls, concurrency=10):
    print(f"[SCRAPER] Starting with {len(urls)} URLs")

    sem = asyncio.Semaphore(concurrency)

    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0"}
    ) as session:

        tasks = [
            fetch_page(session, u["url"], sem)
            for u in urls
        ]

        results = []

        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scraping"):
            url, html = await f
            results.append((url, html))

        return results

async def run_pipeline(sitemap_url, output_file, limit=None):
    urls = parse_sitemap(sitemap_url)

    existing_ids = load_existing_ids(output_file)

    original_len = len(urls)

    urls = [u for u in urls if extract_id(u["url"]) not in existing_ids]

    skipped = original_len - len(urls)
    print(f"[PIPELINE] Skipped {skipped}, remaining {len(urls)}")

    if limit:
        urls = urls[:limit]
        print(f"[PIPELINE] Limiting to {limit} URLs")

    BATCH_SIZE = 200
    success = 0
    failed = 0

    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i+BATCH_SIZE]

        print(f"[BATCH] Processing {i} → {i + len(batch)}")

        lastmod_by_url = {u["url"]: u.get("lastmod") for u in batch}
        pages = await scrape_urls(batch)

        for url, html in pages:
            if not html:
                failed += 1
                continue

            try:
                data = parse_page(html, url, lastmod=lastmod_by_url.get(url))
                write_jsonl(output_file, data)

                success += 1

                if success % 10 == 0:
                    print(f"[PROGRESS] Parsed {success} pages")

            except Exception as e:
                print(f"[PARSE ERROR] {url} -> {e}")
                failed += 1

    print("\n[PIPELINE DONE]")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")