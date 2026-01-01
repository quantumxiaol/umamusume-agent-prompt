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


def _build_run_config(
    use_proxy: bool, *, css_selector: str | None = None
) -> CrawlerRunConfig:
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
        css_selector=css_selector,
        word_count_threshold=0,
        wait_until="networkidle",
        wait_for="body",
        delay_before_return_html=0.5,
        remove_overlay_elements=True,
        magic=True,
        scan_full_page=True,
    )


async def crawl_page(url: str, *, use_proxy: bool = False) -> str:
    async with AsyncWebCrawler(verbose=True) as crawler:
        css_selector = None
        if "wiki.biligame.com/umamusume" in url or "mzh.moegirl.org.cn" in url:
            # MediaWiki pages: main content lives under this container.
            css_selector = ".mw-parser-output"
        result = await crawler.arun(
            url=url, config=_build_run_config(use_proxy, css_selector=css_selector)
        )
        # Debugging prints disabled; uncomment for crawl diagnostics.
        # print(f"[crawler] url={url} success={getattr(result, 'success', None)}")
        # print(f"[crawler] status_code={getattr(result, 'status_code', None)}")
        # print(f"[crawler] redirected_url={getattr(result, 'redirected_url', None)}")
        # print(f"[crawler] error_message={getattr(result, 'error_message', None)}")
        # for name in ("markdown", "text", "cleaned_html", "html", "extracted_content"):
        #     value = getattr(result, name, None)
        #     preview = ""
        #     if isinstance(value, str):
        #         preview = value[:200].replace("\n", "\\n")
        #     print(f"[crawler] {name} type={type(value).__name__} preview={preview!r}")
        # Be defensive: Crawl4AI can return dict-like payloads or empty strings.
        def extract_text(value: object) -> str:
            if isinstance(value, str) and value.strip():
                return value
            if isinstance(value, dict):
                for key in (
                    "raw_markdown",
                    "markdown_with_citations",
                    "references_markdown",
                    "markdown",
                    "content",
                    "text",
                    "data",
                    "raw",
                ):
                    candidate = value.get(key)
                    if isinstance(candidate, str) and candidate.strip():
                        return candidate
            if hasattr(value, "raw_markdown"):
                candidate = getattr(value, "raw_markdown", "")
                if isinstance(candidate, str) and candidate.strip():
                    return candidate
            if hasattr(value, "markdown_with_citations"):
                candidate = getattr(value, "markdown_with_citations", "")
                if isinstance(candidate, str) and candidate.strip():
                    return candidate
            return ""

        for attr in (
            "markdown",
            "markdown_v2",
            "text",
            "cleaned_html",
            "html",
            "extracted_content",
        ):
            value = getattr(result, attr, None)
            extracted = extract_text(value)
            if extracted:
                return str(extracted)
        if css_selector:
            fallback_result = await crawler.arun(
                url=url, config=_build_run_config(use_proxy, css_selector=None)
            )
            for attr in (
                "markdown",
                "text",
                "cleaned_html",
                "html",
                "extracted_content",
            ):
                value = getattr(fallback_result, attr, None)
                extracted = extract_text(value)
                if extracted:
                    return str(extracted)
        return ""
