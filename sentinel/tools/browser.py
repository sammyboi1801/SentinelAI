# FILE: tools/browser.py
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from sentinel.core.config import ConfigManager

cfg = ConfigManager()


def search_web(query):
    """
    Smart Search: Tries Tavily (Advanced RAG), falls back to DuckDuckGo.
    """
    # 1. Try Tavily
    tavily_key = cfg.get_key("tavily")
    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            response = client.get_search_context(query=query, search_depth="basic", max_tokens=1500)
            return f"[Source: Tavily]\n{response}"
        except ImportError:
            pass
        except Exception:
            pass

    try:
        results = DDGS().text(query, max_results=4)
        summary = []
        for r in results:
            summary.append(f"Title: {r.get('title')}\nLink: {r.get('href')}\nSnippet: {r.get('body')}\n")

        if not summary:
            return "No results found on DuckDuckGo."
        return "[Source: DuckDuckGo]\n" + "\n".join(summary)
    except Exception as e:
        return f"Search completely failed: {e}"


def open_url(url):
    """Scrapes text content from a URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            return f"Error: Status code {resp.status_code}"

        soup = BeautifulSoup(resp.content, 'html.parser')
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)

        return clean_text[:4000] + "..."
    except Exception as e:
        return f"Error reading page: {e}"


def read_webpage(url):
    return open_url(url)