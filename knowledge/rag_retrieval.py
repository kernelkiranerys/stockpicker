from pgvector.django import CosineDistance
from knowledge.models import KnowledgeChunk, KnowledgeDocument
from knowledge.embeddings import embed_query


def retrieve(query, signal_type="general", top_k=5):
    """Retrieve relevant knowledge chunks via semantic search.
    Returns list of dicts with text, score, category, document_title.
    """
    query_embedding = embed_query(query)
    if not query_embedding:
        return []

    category_map = {
        "day_trade": ["day_trading", "technical_analysis", "options"],
        "medium_turnaround": ["technical_analysis", "options", "market_psychology"],
        "seasonal_swing": ["sector_rotation", "value_investing", "sec_filings", "macro_fundamentals"],
    }

    preferred_categories = category_map.get(signal_type, [])

    qs = KnowledgeChunk.objects.filter(embedding__isnull=False)

    if preferred_categories:
        qs_filtered = qs.filter(category__in=preferred_categories)
        if qs_filtered.exists():
            qs = qs_filtered

    results = qs.annotate(
        distance=CosineDistance("embedding", query_embedding)
    ).order_by("distance")[:top_k]

    return [
        {
            "text": chunk.text,
            "score": 1 - chunk.distance if hasattr(chunk, "distance") else 0,
            "category": chunk.category,
            "document_title": chunk.document.title,
            "chunk_id": chunk.id,
        }
        for chunk in results
    ]