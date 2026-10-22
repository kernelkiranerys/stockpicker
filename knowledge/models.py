from django.db import models
from pgvector.django import VectorField


class KnowledgeDocument(models.Model):
    CATEGORY_DAY_TRADING = "day_trading"
    CATEGORY_VALUE_INVESTING = "value_investing"
    CATEGORY_TECHNICAL = "technical_analysis"
    CATEGORY_OPTIONS = "options"
    CATEGORY_SECTOR_ROTATION = "sector_rotation"
    CATEGORY_SEC_FILINGS = "sec_filings"
    CATEGORY_PSYCHOLOGY = "market_psychology"
    CATEGORY_MACRO = "macro_fundamentals"
    CATEGORY_GENERAL = "general"

    CATEGORY_CHOICES = [
        (CATEGORY_DAY_TRADING, "Day Trading"),
        (CATEGORY_VALUE_INVESTING, "Value Investing"),
        (CATEGORY_TECHNICAL, "Technical Analysis"),
        (CATEGORY_OPTIONS, "Options"),
        (CATEGORY_SECTOR_ROTATION, "Sector Rotation"),
        (CATEGORY_SEC_FILINGS, "SEC Filings"),
        (CATEGORY_PSYCHOLOGY, "Market Psychology"),
        (CATEGORY_MACRO, "Macro & Fundamentals"),
        (CATEGORY_GENERAL, "General"),
    ]

    title = models.CharField(max_length=300)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)
    source = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(blank=True)
    content = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    chunk_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class KnowledgeChunk(models.Model):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.IntegerField()
    text = models.TextField()
    embedding = VectorField(dimensions=768, null=True, blank=True)
    category = models.CharField(max_length=50, blank=True)
    token_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]

    def __str__(self):
        return f"{self.document.title} [{self.chunk_index}]"