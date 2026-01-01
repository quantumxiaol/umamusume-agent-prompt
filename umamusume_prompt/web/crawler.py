from __future__ import annotations

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig, ProxyConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from umamusume_prompt.config import config


class SingleProxyRotationStrategy:
    def __init__(self, proxy_config: ProxyConfig) -> None:
        self.proxy_config = proxy_config

    async def get_next_proxy(self) -> ProxyConfig:
        return self.proxy_config


_md_generator = DefaultMarkdownGenerator(
    options={
        "ignore_links": True,
        "ignore_images": True,
        "escape_html": False,
        "body_width": 80,
    }
)


def _build_run_config(use_proxy: bool) -> CrawlerRunConfig:
    proxy_url = config.proxy_url()
    proxy = (
        SingleProxyRotationStrategy(ProxyConfig(server=proxy_url))
        if proxy_url and use_proxy
        else None
    )
    return CrawlerRunConfig(
        markdown_generator=_md_generator,
        proxy_rotation_strategy=proxy,
        excluded_selector=".ads, .comments, #sidebar",
    )


async def crawl_page(url: str, *, use_proxy: bool = False) -> str:
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url, config=_build_run_config(use_proxy))
        return result.markdown
