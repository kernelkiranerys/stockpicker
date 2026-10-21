from celery import shared_task
from feedback.weekly_review import review_failed_trades


@shared_task
def run_weekly_review():
    """Weekly: review failed trades and extract lessons."""
    lessons = review_failed_trades(lookback_days=7)
    return {"lessons_created": lessons}