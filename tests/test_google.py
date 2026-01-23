import os
import sys

import pytest

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from umamusume_web_crawler.web.search import google_search_urls
# Import config to ensure API keys are loaded
from umamusume_web_crawler.config import config as crawler_config

# Attempt to load local config if available, similar to server.py
try:
    from umamusume_prompt.config import config as local_config
    crawler_config.apply_overrides(
        google_api_key=local_config.google_api_key,
        google_cse_id=local_config.google_cse_id,
        http_proxy=local_config.http_proxy,
        https_proxy=local_config.https_proxy,
    )
except ImportError:
    pass
# Or ensure it loads from env if local config import fails
if not crawler_config.google_api_key:
    crawler_config.update_from_env()


def test_google_search_urls() -> None:
    if not crawler_config.google_api_key or not crawler_config.google_cse_id:
        pytest.skip("GOOGLE_API_KEY or GOOGLE_CSE_ID not set")

    query_str = "爱慕织姬 site:wiki.biligame.com/umamusume"
    results = google_search_urls(search_term=query_str, num=5)
    assert isinstance(results, list)
    # Depending on network/availability, this might retry or fail, but we check if it returns list
    if results:
        print(f"Found {len(results)} results")
        print(results[0])


if __name__ == "__main__":
    test_google_search_urls()
