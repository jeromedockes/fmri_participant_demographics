from scanning_horizon import _get_ns_sample_sizes


def n_participants_from_labelbuddy_docs(documents):
    texts = []
    for doc in documents:
        abs_start, abs_end = doc["metadata"]["field_positions"]["abstract"]
        texts.append(doc["text"][abs_start:abs_end])
    return n_participants_from_texts(texts)


def n_participants_from_texts(article_texts):
    result = []
    for text in article_texts:
        groups = _get_ns_sample_sizes.estimate_n(text)
        if not groups:
            result.append(None)
        else:
            result.append(sum((g[1] for g in groups)))
    return result
