from django.contrib import admin
from .models import KnowledgeDocument, KnowledgeChunk


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "source", "uploaded_at", "is_processed", "chunk_count")
    list_filter = ("category", "is_processed")
    search_fields = ("title", "source")


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "token_count", "category")
    list_filter = ("category",)
    search_fields = ("text",)