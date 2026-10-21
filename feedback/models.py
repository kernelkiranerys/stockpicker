from django.db import models


class LessonLearned(models.Model):
    """A lesson extracted from a failed trade via LLM reflection."""
    lesson = models.TextField()
    context = models.TextField(blank=True, help_text="The data/context that led to the failed trade")
    ticker_symbol = models.CharField(max_length=20, blank=True)
    signal_type = models.CharField(max_length=25, blank=True)
    trade_date = models.DateField(null=True, blank=True)
    pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    llm_reflection = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.lesson[:80]


class PromptVersion(models.Model):
    """Track versions of the AI expert prompt with their performance."""
    version = models.CharField(max_length=20, unique=True)
    prompt_text = models.TextField()
    changes = models.TextField(blank=True, help_text="What changed from previous version")
    avg_conviction = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    avg_pnl = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class TradeReview(models.Model):
    """Weekly review of a trade outcome."""
    signal_id = models.IntegerField()
    ticker_symbol = models.CharField(max_length=20)
    action = models.CharField(max_length=10)
    entry_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    exit_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    outcome = models.CharField(max_length=10)
    context_snapshot = models.JSONField(default=dict, blank=True)
    llm_analysis = models.TextField(blank=True)
    lesson = models.ForeignKey(LessonLearned, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reviewed_at"]