import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from umamusume_web_crawler.web.biligame import (
    fetch_biligame_wikitext_expanded,
    search_biligame_titles,
)
from umamusume_web_crawler.web.parse_wiki_infobox import (
    parse_wiki_page,
    wiki_page_to_llm_markdown,
)

async def _run() -> None:
    # 1. Test Search
    keyword = "东海帝皇"
    print(f"Testing search for '{keyword}'...")
    titles = await search_biligame_titles(keyword, limit=5)
    print(f"Search results: {titles}")
    
    if not titles:
        print("No titles found, skipping crawl test.")
        return

    # 2. Test Crawl (Wikitext -> Markdown)
    target_title = titles[0]
    target_url = f"https://wiki.biligame.com/umamusume/{target_title}"
    print(f"Testing crawl for '{target_title}' ({target_url})...")
    
    wikitext = await fetch_biligame_wikitext_expanded(target_url, max_depth=1, max_pages=5)
    page = parse_wiki_page(wikitext, site="biligame")
    markdown = wiki_page_to_llm_markdown(target_title, page, site="biligame")

    output_dir = Path("results") / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "biligame_api.md"
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {len(markdown)} chars to {output_path}")

if __name__ == "__main__":
    asyncio.run(_run())
