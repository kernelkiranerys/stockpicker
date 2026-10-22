from celery import shared_task
from knowledge.ingestion import process_document
from knowledge.embeddings import embed_chunks


@shared_task
def process_new_documents():
    """Process any unprocessed KnowledgeDocuments."""
    from knowledge.models import KnowledgeDocument
    for doc in KnowledgeDocument.objects.filter(is_processed=False):
        try:
            process_document(doc.id)
            embed_chunks.delay(doc.id)
        except Exception as e:
            print(f"Knowledge processing error for {doc.title}: {e}")


@shared_task
def reembed_new():
    """Re-embed any chunks that don't have embeddings yet."""
    from knowledge.models import KnowledgeDocument
    for doc in KnowledgeDocument.objects.filter(is_processed=True):
        try:
            embed_chunks(doc.id)
        except Exception as e:
            print(f"Embedding error for {doc.title}: {e}")