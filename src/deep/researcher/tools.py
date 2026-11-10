from typing import List, Dict
from duckduckgo_search import DDGS


def search_web(query: str, max_results: int = 4) -> List[Dict[str, str]]:
    """Search DuckDuckGo and return a list of formatted results with title, snippet, and link."""
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                }
                for r in raw_results
            ]
    except Exception as e:
        print(f"⚠️ Search error for '{query}': {e}")
        return []


def format_search_results(results: List[Dict[str, str]]) -> str:
    """Format search results into a clean string for LLM prompts."""
    if not results:
        return "No web results found."
    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(f"[{i}] {r['title']}\nSnippet: {r['snippet']}\nURL: {r['url']}")
    return "\n\n".join(formatted)

