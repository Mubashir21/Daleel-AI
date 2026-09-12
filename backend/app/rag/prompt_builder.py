def build_context(matches):
    """
    Returns (context_str, source_titles) — source_titles maps each Source
    number to that URL's IslamQA question-title heading, for display purposes
    only (the LLM itself never sees or needs the title).
    """
    if not matches:
        return "", {}

    # Group chunks by URL, preserving first-seen order
    url_to_source = {}
    source_counter = 1
    grouped = {}
    titles = {}

    for match in matches:
        meta = match["metadata"]
        url = meta.get("url", "")

        if url not in url_to_source:
            url_to_source[url] = source_counter
            grouped[url] = []
            source_counter += 1

        grouped[url].append(meta.get("text", "").strip())

        source_number = url_to_source[url]
        if source_number not in titles and meta.get("title"):
            titles[source_number] = meta["title"]

    # Build context blocks grouped by source
    context_parts = []
    for url, chunks in grouped.items():
        source_number = url_to_source[url]
        block = f"[Source {source_number}]\nURL: {url}\n\n"
        block += "\n\n---\n\n".join(f"Chunk:\n{chunk}" for chunk in chunks)
        context_parts.append(block)

    return "\n\n===\n\n".join(context_parts), titles
