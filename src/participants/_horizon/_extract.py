from participants._horizon.get_ns_sample_sizes import estimate_n


def extract(doc):
    abs_start, abs_end = doc["meta"]["field_positions"]["abstract"]
    abstract = doc["text"][abs_start:abs_end]
    groups = estimate_n(abstract)
    if not groups:
        return None
    return sum((g[1] for g in groups))
