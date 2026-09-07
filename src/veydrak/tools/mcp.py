"""
veydrak/mcp.py — Model Context Protocol integration.

Provides:
  - aget_mcp_tools()        → load tools from an MCP server (requires langchain-mcp-adapters)
  - get_fallback_web_tools() → lightweight web_search / web_fetch stubs using urllib
                               so demos always run even without an MCP server.

The tutorial point: MCP makes tool distribution *configuration* instead of *code*.
The same server declared in .cursor/mcp.json gives Cursor the same tools.
"""

import os
from langchain_core.tools import tool, BaseTool

# ---------------------------------------------------------------------------
# MCP server URL — override with MCP_SERVER_URL in .env
# ---------------------------------------------------------------------------
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3001/sse")


# ---------------------------------------------------------------------------
# Real MCP client (requires langchain-mcp-adapters + a running MCP server)
# ---------------------------------------------------------------------------

async def aget_mcp_tools(server_url: str | None = None) -> list[BaseTool]:
    """
    Connect to an SSE-based MCP server and return its tools as LangChain
    BaseTool objects.  Falls back to stubs if the package is missing or
    the server is unreachable.
    """
    url = server_url or MCP_SERVER_URL
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient(
            {
                "web": {
                    "url": url,
                    "transport": "sse",
                }
            }
        )
        tools = await client.get_tools()
        if tools:
            return tools
        # Server responded but returned no tools — fall through
    except Exception:
        pass  # package missing or server unreachable

    # Fallback: return lightweight stubs
    return get_fallback_web_tools()


# ---------------------------------------------------------------------------
# Fallback web tools (no external dependencies)
# ---------------------------------------------------------------------------

def get_fallback_web_tools() -> list[BaseTool]:
    """
    Return simple web_search and web_fetch tools that work without any
    external MCP server.  web_search uses a DuckDuckGo HTML scrape;
    web_fetch uses urllib.
    """

    @tool
    def web_search(query: str) -> str:
        """
        Search the web for a query and return a short summary of results.
        Returns up to 5 result snippets from DuckDuckGo.
        """
        import urllib.request
        import urllib.parse
        import re

        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Extract result snippets from DuckDuckGo HTML
            snippets = re.findall(
                r'class="result__snippet">(.*?)</a>', html, re.DOTALL
            )
            if not snippets:
                snippets = re.findall(
                    r'class="result__snippet"[^>]*>(.*?)</(?:a|span)>',
                    html,
                    re.DOTALL,
                )

            cleaned = []
            for s in snippets[:5]:
                text = re.sub(r"<[^>]+>", "", s).strip()
                if text:
                    cleaned.append(text)

            if cleaned:
                return "\n\n".join(f"{i}. {s}" for i, s in enumerate(cleaned, 1))
            return f"No results found for '{query}'."
        except Exception as e:
            return f"Search error: {e}"

    @tool
    def web_fetch(url: str) -> str:
        """
        Fetch a web page and return its text content (HTML tags stripped).
        Returns at most the first 3000 characters.
        """
        import urllib.request
        import re

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Strip tags, collapse whitespace
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()

            return text[:3000] + ("..." if len(text) > 3000 else "")
        except Exception as e:
            return f"Fetch error: {e}"

    return [web_search, web_fetch]
