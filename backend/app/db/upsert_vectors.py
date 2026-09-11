from tqdm import tqdm
import json
from backend.app.core.config import settings

from backend.app.db.pinecone_client import get_index
from backend.app.retrieval.sparse import load_sparse_encoder, encode_sparse, build_sparse_input


def delete_stale_chunks(index, doc_ids, namespace):
    """
    Deletes all existing chunk vectors for the given doc_ids before re-upserting.
    Needed because an edited answer can produce fewer chunks than before, which
    would otherwise leave old, higher-index chunks orphaned in Pinecone.
    """
    for doc_id in doc_ids:
        stale_ids = [
            id_ for page in index.list(prefix=f"{doc_id}_chunk_", namespace=namespace)
            for id_ in page
        ]
        if stale_ids:
            index.delete(ids=stale_ids, namespace=namespace)


def run_upsert(file_path, batch_size=100, delete_stale=False):
    """
    delete_stale: set True when re-upserting a small set of already-indexed docs
    (e.g. the incremental update pipeline) so edited answers with fewer chunks
    than before don't leave orphaned old chunks behind. Skipped by default since
    it's wasted work (one Pinecone list() call per doc) on a fresh bootstrap
    upload where nothing exists yet.
    """

    index = get_index()
    encoder = load_sparse_encoder()

    if delete_stale:
        with open(file_path, "r", encoding="utf-8") as f:
            doc_ids = {str(json.loads(line)["doc_id"]) for line in f}
        delete_stale_chunks(index, doc_ids, settings.pinecone_namespace)

    batch = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Uploading to Pinecone"):
            record = json.loads(line)

            sparse_text = build_sparse_input(record)

            sparse_vector = encode_sparse(encoder, sparse_text, mode="document")

            vector = {
                "id": record["id"],
                "values": record["embedding"],

                "sparse_values": sparse_vector,

                "metadata": {
                    "doc_id": str(record["doc_id"]),
                    "chunk_index": record.get("chunk_index", 0),
                    "text": record.get("text") or "",
                    "title": record.get("title") or "",
                    "question": record.get("question") or "",
                    "topics": record.get("topics") or [],
                    "url": record.get("url") or "",
                    "source": record.get("source") or "IslamQA",
                    "lastmod": record.get("lastmod") or ""
                }
            }

            batch.append(vector)

            if len(batch) == batch_size:
                index.upsert(vectors=batch, namespace=settings.pinecone_namespace)
                batch = []

    # flush remaining
    if batch:
        index.upsert(vectors=batch, namespace=settings.pinecone_namespace)

    print("Hybrid upload complete")


if __name__ == "__main__":
    run_upsert("data/processed/embedded_chunks.jsonl")