from participants import _reading, _summarization


def n_participants_from_labelbuddy_docs(documents):
    return n_participants_from_texts(doc["text"] for doc in documents)


def n_participants_from_texts(article_texts):
    reader = _reading.Reader()
    result = []
    for text in article_texts:
        extracted = _summarization.summarize(reader.extract_from_text(text))
        result.append(extracted.count)
    return result
