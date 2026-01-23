import os
import sys

import pytest

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Updated import
from umamusume_web_crawler.web.crawler import crawl_page


@pytest.mark.asyncio
async def test_crawl_page_returns_content() -> None:
    target_url = os.getenv(
        "CRAWLER_TEST_URL",
        "https://wiki.biligame.com/umamusume/爱慕织姬",
    )

    content = await crawl_page(target_url)
    assert isinstance(content, str)
    assert content.strip(), "Expected non-empty crawl content"
    print(content[:2000])


if __name__ == "__main__":
    args = sys.argv[1:] or [__file__]
    pytest.main(args)
