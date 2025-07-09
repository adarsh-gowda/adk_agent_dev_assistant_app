# Build: Recursive Documentation Crawler for ADK / Gemini / Vertex AI

import os
import re
import asyncio
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright

STARTING_URLS = {
    "agent_builder_overview": "https://cloud.google.com/vertex-ai/generative-ai/docs/agent-builder/overview",
    "adk_development": "https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/develop/adk",
    "agent_engine_overview": "https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview",
    "gemini_api_overview": "https://ai.google.dev/gemini-api/docs",
    "gemini_text_generation": "https://ai.google.dev/gemini-api/docs/text-generation",
    "gemini_quickstart": "https://ai.google.dev/gemini-api/docs/quickstart",
    "gemini_models": "https://ai.google.dev/gemini-api/docs/models",
}

MAX_DEPTH = 5
MAX_PAGES = 100
OUTPUT_DIR = "docs"

visited = set()
to_visit = []

os.makedirs(OUTPUT_DIR, exist_ok=True)

def normalize_url(url):
    return url.split("#")[0].rstrip("/")

def is_valid_link(href, base_domain):
    if not href or href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
        return False
    parsed = urlparse(href)
    return parsed.netloc == "" or base_domain in parsed.netloc

async def extract_text(page):
    # Expand all <details> and click "expand" buttons
    await page.evaluate("""() => {
        document.querySelectorAll('details').forEach(el => el.open = true);
        document.querySelectorAll('button').forEach(btn => {
            if (btn.innerText.toLowerCase().includes('expand') || btn.innerText.includes('+')) btn.click();
        });
    }""")
    await page.wait_for_timeout(1000)
    return await page.evaluate("() => document.body.innerText")

async def extract_links(page, base_url):
    anchors = await page.query_selector_all("a")
    links = []
    for a in anchors:
        href = await a.get_attribute("href")
        if href and is_valid_link(href, urlparse(base_url).netloc):
            abs_url = urljoin(base_url, href)
            links.append(normalize_url(abs_url))
    return links

async def crawl_page(playwright, url, depth):
    if url in visited or len(visited) >= MAX_PAGES or depth > MAX_DEPTH:
        return []

    visited.add(url)
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    print(f"📄 Crawling (depth {depth}): {url}")
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(1500)

        text = await extract_text(page)
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", urlparse(url).path.strip("/"))[:100]
        with open(os.path.join(OUTPUT_DIR, f"{slug}.txt"), "w", encoding="utf-8") as f:
            f.write(text)

        links = await extract_links(page, url)
        print(f"🔗 Found {len(links)} links on page.")
        return links

    except Exception as e:
        print(f"❌ Failed to crawl {url}: {e}")
        return []
    finally:
        await browser.close()

async def main():
    async with async_playwright() as playwright:
        for url in STARTING_URLS.values():
            to_visit.append((url, 0))

        while to_visit and len(visited) < MAX_PAGES:
            current_url, depth = to_visit.pop(0)
            new_links = await crawl_page(playwright, current_url, depth)
            for link in new_links:
                if link not in visited:
                    to_visit.append((link, depth + 1))

        print(f"✅ Crawling complete. Total pages saved: {len(visited)}")
        
if __name__ == "__main__":
    asyncio.run(main())