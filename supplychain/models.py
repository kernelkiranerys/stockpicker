from django.db import models
from tickers.models import Ticker


class CompanyRelationship(models.Model):
    """Supply chain relationship between companies.
    Extracted from 10-K Risk Factors and Business sections via LLM.
    """
    RELATIONSHIP_TYPES = [
        ("customer", "Customer"),
        ("supplier", "Supplier"),
        ("competitor", "Competitor"),
        ("partner", "Partner"),
        ("distributor", "Distributor"),
    ]

    source_ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="outgoing_relationships")
    target_company = models.CharField(max_length=200)
    target_ticker = models.ForeignKey(Ticker, on_delete=models.SET_NULL, null=True, blank=True, related_name="incoming_relationships")
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)
    context = models.TextField(blank=True, help_text="Source text from 10-K")
    filing_date = models.DateField(null=True, blank=True)
    filing_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("source_ticker", "target_company", "relationship_type")

    def __str__(self):
        return f"{self.source_ticker.symbol} → {self.target_company} ({self.relationship_type})"