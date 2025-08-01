def is_relevant_query(nl_query):
    """
    Checks if the user's natural language query contains any relevant keywords.
    """
    keywords = _get_relevant_keywords()
    return _contains_any_keyword(nl_query, keywords)


def _get_relevant_keywords():
    """
    Returns a predefined list of keywords that indicate a relevant query.
    """
    return [
        "Platform",
        "Test_Suite",
        "passing percentage",
        "Release_Version",
        "version",
        "testcase",
        "testcases",
        "executed",
        "passed",
    ]


def _contains_any_keyword(query: str, keywords: list) -> bool:
    """
    Checks if any keyword appears in the query (case-insensitive).
    """
    query_lower = query.lower()
    return any(kw.lower() in query_lower for kw in keywords)
