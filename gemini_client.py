import os
import json
from html.parser import HTMLParser

import aiohttp


# A simple HTML parser to strip tags and extract text content.
class SimpleHTMLParser(HTMLParser):
    """A simple HTML parser to strip tags and extract text content."""

    def __init__(self):
        super().__init__()
        self.reset()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return "".join(self.text)


async def strip_html(html_content):
    parser = SimpleHTMLParser()
    parser.feed(html_content)
    return parser.get_text()


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
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    def set_api_key(self, api_key):
        self.api_key = api_key

    async def generate_content(self, prompt):
        if not self.api_key:
            return "Error: Gemini API key is not set."

        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        url = f"{self.base_url}?key={self.api_key}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        try:
                            return data["candidates"][0]["content"]["parts"][0]["text"]
                        except (KeyError, IndexError, TypeError):
                            return "Error: Unexpected response format from Gemini API."
                    else:
                        error_text = await response.text()
                        return f"Error: API call failed with status {response.status}. Response: {error_text}"
            except Exception as e:
                return f"An error occurred during the API call: {e}"

    async def search_web(self, query):
        search_url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 "
                "Safari/537.3"
            )
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    search_url, data=params, headers=headers
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        # This is a very basic way to find links.
                        links = []
                        start_str = 'a class="result__a" href="'
                        end_str = '"'
                        start_index = 0
                        while len(links) < 3:
                            start_index = html.find(start_str, start_index)
                            if start_index == -1:
                                break
                            start_index += len(start_str)
                            end_index = html.find(end_str, start_index)
                            link = html[start_index:end_index]
                            if link.startswith("http"):
                                links.append(link)
                            start_index = end_index
                        return links
                    else:
                        return []
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
                            text_content = await strip_html(html_content)
                            scraped_content += text_content + "\n\n"
                except Exception as e:
                    scraped_content += f"Could not scrape {url}: {e}\n\n"

        if not scraped_content.strip():
            return "Could not scrape any content from the web."

        summary_prompt = f"Please summarize the following content about '{topic}':\n\n{scraped_content[:10000]}"
        summary = await self.generate_content(summary_prompt)
        return f"**Research Summary for '{topic}'**\n\n{summary}"
