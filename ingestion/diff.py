from backend.app.core.config import settings
from backend.app.db.pinecone_client import get_index

FETCH_BATCH_SIZE = 100
PINECONE_CALL_TIMEOUT = 30


def fetch_pinecone_lastmods(doc_ids):
    """
    Returns {doc_id: lastmod} for whatever is currently stored in Pinecone.
    Reads only each doc's first chunk (id `{doc_id}_chunk_0`) — that's the
    one chunk always guaranteed to carry a lastmod tag (the backfill only
    tags chunk_0 for docs it doesn't otherwise reprocess; a reprocessed doc
    gets it on every chunk, chunk_0 included). A missing doc_id in the
    result means it isn't indexed yet.
    """
    index = get_index()
    doc_ids = list(doc_ids)
    lastmods = {}

    for i in range(0, len(doc_ids), FETCH_BATCH_SIZE):
        batch = doc_ids[i:i + FETCH_BATCH_SIZE]
        ids = [f"{doc_id}_chunk_0" for doc_id in batch]

        response = index.fetch(
            ids=ids,
            namespace=settings.pinecone_namespace,
            _request_timeout=PINECONE_CALL_TIMEOUT,
        )

        for doc_id in batch:
            vector = response.vectors.get(f"{doc_id}_chunk_0")
            if vector is not None:
                lastmods[doc_id] = vector.metadata.get("lastmod")

    return lastmods


def classify_changes(sitemap_entries, stored_lastmods):
    """
    sitemap_entries: list of {"url", "lastmod", "id"} from the live sitemap.
    stored_lastmods: {doc_id: lastmod} as currently indexed in Pinecone.
    Returns (new_entries, updated_entries) — unchanged docs are dropped.
    """
    new_entries = []
    updated_entries = []

    for entry in sitemap_entries:
        stored = stored_lastmods.get(entry["id"])

        if stored is None:
            new_entries.append(entry)
        elif stored != entry["lastmod"]:
            updated_entries.append(entry)

    return new_entries, updated_entries
