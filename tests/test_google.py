import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from umamusume_prompt.web.search import google_search_urls


def test_google_search_urls() -> None:
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GOOGLE_CSE_ID"):
        pytest.skip("GOOGLE_API_KEY or GOOGLE_CSE_ID not set")

    query_str = "爱慕织姬 site:wiki.biligame.com/umamusume"
    results = google_search_urls(search_term=query_str)
    assert isinstance(results, list)
    assert results, "Expected non-empty google search results"


if __name__ == "__main__":
    test_google_search_urls()
