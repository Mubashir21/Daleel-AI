from bs4 import BeautifulSoup

def parse_page(html, url, lastmod=None):
    soup = BeautifulSoup(html, "html.parser")

    # -------------------
    # TITLE
    # -------------------
    title = soup.select_one('[data-sut="question-title"]')
    title = title.get_text(strip=True) if title else None

    # -------------------
    # DATE
    # -------------------
    date = soup.select_one('[data-sut="publication-date"]')
    date_text = date.get_text(strip=True) if date else None

    date_hijri, date_gregorian = None, None
    if date_text:
        parts = [p.strip() for p in date_text.split(",")]
        if len(parts) == 2:
            date_hijri, date_gregorian = parts

    # -------------------
    # VIEWS
    # -------------------
    views = soup.select_one('[data-sut="view-count"]')
    views = int(views.get_text(strip=True).replace(",", "")) if views else None

    # -------------------
    # QUESTION
    # -------------------
    question_section = soup.select_one('section:has([data-sut="question-number"])')
    question_text = None
    if question_section:
        p = question_section.find("p")
        if p:
            question_text = p.get_text(strip=True)

    # -------------------
    # SUMMARY (optional)
    # -------------------
    summary_section = soup.find("section", class_="tw-bg-paperSummary")
    summary_text = None
    if summary_section:
        p = summary_section.find("p")
        if p:
            summary_text = p.get_text(strip=True)

    # -------------------
    # ANSWER
    # -------------------
    answer_div = soup.select_one('[data-sut="answer-text"]')  # VERY IMPORTANT
    answer_text = None
    if answer_div:
        paragraphs = answer_div.find_all("p")
        answer_text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)

    # -------------------
    # TOPICS
    # -------------------
    topics = []
    topic_links = soup.select('[data-gtm="link-topic"]')
    for t in topic_links:
        txt = t.get_text(strip=True)
        if txt:
            topics.append(txt)

    # -------------------
    # ID
    # -------------------
    id_ = url.rstrip("/").split("/")[-1]

    # -------------------
    # SOURCE
    # -------------------
    source = soup.select_one('[data-sut="fatwa-source"]')
    source = source.get_text(strip=True) if source else None

    return {
        "id": id_,
        "title": title,
        "question": question_text,
        "summary": summary_text,
        "answer": answer_text,
        "topics": topics,
        "date_hijri": date_hijri,
        "date_gregorian": date_gregorian,
        "views": views,
        "url": url,
        "source": source,
        "lastmod": lastmod
    }