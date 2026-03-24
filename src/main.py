"""MCP server for IMAGIN.studio documentation search.

C.O.R.T.Ex. - Context Oriented Retrieval Tool for EXternal logic.
A fully local MCP server that provides semantic search over documentation.
"""

import asyncio
import logging
import time

from fastmcp import Context, FastMCP

from src.config import CHARACTER_LIMIT, SEARCH_TOP_K, SEARCH_TOP_K_MAX
from src.engine.background import is_update_in_progress, schedule_background_update
from src.engine.embedder import Embedder
from src.engine.vector_store import SearchResult, VectorStore
from src.telemetry import install_hooks


logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    name="imagin-docs",
    instructions="Search IMAGIN.studio documentation using the search_docs tool.",
)

# Shared instances (lazy-loaded)
_embedder = Embedder()
_store = VectorStore()


@mcp.tool(
    annotations={
        "title": "Search IMAGIN.studio Documentation",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def search_docs(query: str, ctx: Context, top_k: int = SEARCH_TOP_K) -> str:
    """Search the official IMAGIN.studio technical documentation, integration guides, and knowledge base.

    Use this tool when the user asks 'How do I...' questions, needs explanation on API concepts
    (CDN, referrers, caching, 360 spinner), or needs to debug integration issues.
    Rewrite vague queries into specific technical search terms before calling.

    Args:
        query: Natural language search query. Use specific technical terms rather
               than vague descriptions. Good: "CDN cache invalidation headers".
               Bad: "caching stuff".
        top_k: Number of results to return (1-20, default 5). Use 1-3 for focused
               lookups, 5 for general questions, 10-20 for broad research.

    Returns:
        Formatted documentation snippets, each containing:
        - Source file path and heading hierarchy
        - URL to the documentation page
        - Relevant content excerpt

    Examples:
        - "CDN cache invalidation" → specific feature lookup
        - "360 spinner integration guide" → integration walkthrough
        - "referrer policy configuration" → configuration reference

    Error responses:
        - "Index is not yet built..." → server is starting up, retry in ~30 seconds
        - "Failed to process query..." → try rephrasing with more specific terms
        - "No results found..." → broaden or rephrase the search query
    """
    await ctx.info(f"search_docs called with query: {query}")
    start = time.monotonic()

    # Clamp top_k to valid range
    top_k = max(1, min(top_k, SEARCH_TOP_K_MAX))

    if is_update_in_progress():
        await ctx.info("Background re-index is in progress, serving from existing index")

    if not _store.has_table():
        await ctx.warning("Index not yet built")
        return (
            "Index is not yet built. The server is indexing documentation on first startup. "
            "This typically takes under 30 seconds. Please retry shortly."
        )

    query_vector = _embedder.embed_texts([query])
    if not query_vector:
        await ctx.error("Failed to embed query")
        return (
            "Failed to process query. Try rephrasing with more specific technical terms "
            "(e.g., 'CDN cache invalidation' instead of 'caching')."
        )

    results = _store.search(query_vector[0], top_k=top_k)
    elapsed_ms = (time.monotonic() - start) * 1000

    if not results:
        await ctx.info(f"No results found ({elapsed_ms:.0f}ms)")
        return f"No results found for: '{query}'. Try broader or alternative search terms."

    await ctx.info(f"Returning {len(results)} results ({elapsed_ms:.0f}ms)")
    return _format_results(results)


def _format_results(results: list[SearchResult]) -> str:
    """Format search results into a readable string."""
    parts: list[str] = []
    for i, result in enumerate(results, 1):
        header = f"**Result {i}**"
        source = f"Source: {result.document_path}"
        if result.heading_hierarchy:
            source += f" ({result.heading_hierarchy})"
        lines = [header, source]
        if result.url:
            lines.append(f"URL: {result.url}")
        lines.append(f"\n{result.content}")
        parts.append("\n".join(lines))

    output = "\n\n---\n\n".join(parts)

    if len(output) > CHARACTER_LIMIT:
        truncated = output[:CHARACTER_LIMIT]
        truncated += (
            "\n\n---\n\n**[Response truncated]** "
            "Results exceeded the character limit. "
            "Reduce `top_k` or use a more specific query to get shorter results."
        )
        return truncated

    return output


async def _run_server() -> None:
    """Start background update task then run the MCP stdio server."""
    schedule_background_update(embedder=_embedder, store=_store, force=True)
    await mcp.run_stdio_async()


def main() -> None:
    """Run the MCP server."""
    install_hooks()
    asyncio.run(_run_server())


if __name__ == "__main__":
    main()
