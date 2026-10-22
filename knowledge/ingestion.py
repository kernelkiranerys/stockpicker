import textwrap
from knowledge.models import KnowledgeDocument, KnowledgeChunk


def chunk_text(text, chunk_size=512, overlap=64):
    """Split text into chunks of approximately chunk_size tokens with overlap.
    Uses word-based splitting (approximation for token count).
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words)
        chunks.append({
            "text": chunk,
            "token_count": len(chunk_words),
            "chunk_index": len(chunks),
        })
        if end >= len(words):
            break
        start = end - overlap

    return chunks


def process_document(doc_id):
    """Process a KnowledgeDocument: chunk its content and store chunks."""
    doc = KnowledgeDocument.objects.get(id=doc_id)
    chunks = chunk_text(doc.content)
    KnowledgeChunk.objects.filter(document=doc).delete()
    for chunk_data in chunks:
        KnowledgeChunk.objects.create(
            document=doc,
            chunk_index=chunk_data["chunk_index"],
            text=chunk_data["text"],
            category=doc.category,
            token_count=chunk_data["token_count"],
        )
    doc.chunk_count = len(chunks)
    doc.is_processed = True
    doc.save(update_fields=["chunk_count", "is_processed"])
    return len(chunks)