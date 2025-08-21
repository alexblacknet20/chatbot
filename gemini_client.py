import os
import json
import asyncio

import aiohttp
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import google.generativeai as genai


CONFIG_FILE = "settings.json"


def _load_api_key_from_file():
    """Load the API key from the local settings file if it exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("GEMINI_API_KEY")
        except Exception:
            return None
    return None


class GeminiClient:
    def __init__(self, api_key=None):
        # Attempt to read the API key from argument, environment or settings file
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or _load_api_key_from_file()
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def set_api_key(self, api_key):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)

    async def generate_content(self, prompt):
        if not self.api_key:
            return "Error: Gemini API key is not set."

        try:
            model = genai.GenerativeModel("gemini-pro")
            response = await asyncio.to_thread(lambda: model.generate_content(prompt))
            return response.text
        except Exception as e:
            return f"An error occurred during the API call: {e}"

    async def search_web(self, query):
        def _search():
            with DDGS() as ddgs:
                return [r["href"] for r in ddgs.text(query, max_results=3)]

        try:
            return await asyncio.to_thread(_search)
        except Exception:
            return []

    async def scrape_and_summarize(self, topic):
        urls = await self.search_web(topic)
        if not urls:
            return "Could not find any relevant websites for the research topic."

        scraped_content = ""
        async with aiohttp.ClientSession() as session:
            for url in urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            soup = BeautifulSoup(html_content, "html.parser")
                            text_content = soup.get_text(separator=" ", strip=True)
                            scraped_content += text_content + "\n\n"
                except Exception as e:
                    scraped_content += f"Could not scrape {url}: {e}\n\n"

        if not scraped_content.strip():
            return "Could not scrape any content from the web."

        summary_prompt = (
            f"Please summarize the following content about '{topic}':\n\n"
            f"{scraped_content[:10000]}"
        )
        summary = await self.generate_content(summary_prompt)
        return f"**Research Summary for '{topic}'**\n\n{summary}"
