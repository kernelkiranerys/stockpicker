from django.conf import settings
from ai_expert.ollama_client import embed
from knowledge.models import KnowledgeChunk


def embed_chunks(doc_id):
    """Generate embeddings for all chunks of a document using nomic-embed-text."""
    from knowledge.models import KnowledgeDocument
    doc = KnowledgeDocument.objects.get(id=doc_id)
    model = settings.OLLAMA_EMBED_MODEL

    for chunk in doc.chunks.filter(embedding__isnull=True):
        embedding = embed(model, chunk.text[:2000])
        if embedding:
            chunk.embedding = embedding
            chunk.save(update_fields=["embedding"])

    return doc.chunks.filter(embedding__isnull=False).count()


def embed_query(text):
    """Generate embedding for a search query."""
    model = settings.OLLAMA_EMBED_MODEL
    return embed(model, text[:2000])