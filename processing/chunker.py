def chunk_text(record, max_chars=2000, min_chars=500):
    chunks = []

    # -------------------
    # Step 0: Build base text
    # -------------------
    text = ""

    if record.get("summary"):
        text += record["summary"].strip() + "\n\n"

    text += record["answer"].strip()

    # -------------------
    # Step 1: Split into paragraphs
    # -------------------
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk = ""

    for para in paragraphs:

        # -------------------
        # Step 2: Detect section markers
        # -------------------
        is_section = para in ["I.", "II.", "III.", "IV.", "V."]

        if is_section:
            # If current chunk is big enough → close it
            if len(current_chunk) >= min_chars:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # Always start new chunk with section marker
            current_chunk += para + "\n\n"
            continue

        # -------------------
        # Step 3: Normal merging logic
        # -------------------
        if len(current_chunk) + len(para) < max_chars:
            current_chunk += para + "\n\n"
        else:
            # If current chunk is big enough → close it
            if len(current_chunk) >= min_chars:
                chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
            else:
                # Too small → force merge
                current_chunk += para + "\n\n"

    # -------------------
    # Step 4: Flush last chunk
    # -------------------
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def create_chunk_objects(record):
    chunks = chunk_text(record)

    chunk_objs = []

    for i, chunk in enumerate(chunks):
        chunk_objs.append({
            "id": f"{record['id']}_chunk_{i}",
            "doc_id": record["id"],
            "chunk_index": i,

            # Content
            "text": chunk,
            "title": record.get("title"),
            "question": record.get("question"),

            # Metadata
            "topics": record.get("topics", []),
            "url": record.get("url"),
            "source": record.get("source", "IslamQA"),

            # Optional
            "date_hijri": record.get("date_hijri"),
            "date_gregorian": record.get("date_gregorian"),
            "lastmod": record.get("lastmod")
        })

    return chunk_objs