from celery import Celery
from celery.schedules import crontab

app = Celery("stockpicker")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # --- Intraday (15-min during US market hours 9:30-16:00 ET = 14:30-21:00 UTC) ---
    "fetch-ohlcv-15m": {
        "task": "data.tasks.fetch_ohlcv_15m",
        "schedule": crontab(minute="*/15", hour="14-21", day_of_week="1-5"),
    },
    "fetch-benchmark-price": {
        "task": "data.tasks.fetch_benchmark_price",
        "schedule": crontab(minute="*/15", hour="14-21", day_of_week="1-5"),
    },
    "revalue-sandbox-positions": {
        "task": "sandbox.tasks.revalue_positions",
        "schedule": crontab(minute="*/15", hour="14-21", day_of_week="1-5"),
    },
    "record-sandbox-equity": {
        "task": "sandbox.tasks.record_equity_point",
        "schedule": crontab(minute="*/15", hour="14-21", day_of_week="1-5"),
    },
    # --- Hourly ---
    "fetch-news": {
        "task": "data.tasks.fetch_news",
        "schedule": crontab(minute=0),
    },
    "fetch-reddit": {
        "task": "data.tasks.fetch_reddit_posts",
        "schedule": crontab(minute=15),
    },
    "fetch-options": {
        "task": "data.tasks.fetch_options_data",
        "schedule": crontab(minute=30),
    },
    "score-news-sentiment": {
        "task": "sentiment.tasks.score_news_sentiment",
        "schedule": crontab(minute=45),
    },
    "score-reddit-sentiment": {
        "task": "sentiment.tasks.score_reddit_sentiment",
        "schedule": crontab(minute=50),
    },
    "aggregate-daily-sentiment": {
        "task": "sentiment.tasks.aggregate_daily_sentiment",
        "schedule": crontab(minute=55),
    },
    "ai-expert-batch-fast": {
        "task": "ai_expert.tasks.run_expert_batch",
        "schedule": crontab(minute=5),
    },
    "compute-technicals": {
        "task": "signals.tasks.compute_technicals",
        "schedule": crontab(minute=10),
    },
    # --- Daily (post-close US market ~21:00 UTC) ---
    "fetch-ohlcv-daily": {
        "task": "data.tasks.fetch_ohlcv_daily",
        "schedule": crontab(minute=0, hour="21", day_of_week="1-5"),
    },
    "fetch-fundamentals": {
        "task": "data.tasks.fetch_fundamentals",
        "schedule": crontab(minute=30, hour="21", day_of_week="1-5"),
    },
    "fetch-insider-trades": {
        "task": "data.tasks.fetch_insider_trades",
        "schedule": crontab(minute=0, hour="22", day_of_week="1-5"),
    },
    "generate-day-trade-signals": {
        "task": "signals.tasks.generate_day_trade_signals",
        "schedule": crontab(minute=30, hour="22", day_of_week="1-5"),
    },
    "generate-medium-signals": {
        "task": "signals.tasks.generate_medium_signals",
        "schedule": crontab(minute=0, hour="23", day_of_week="1-5"),
    },
    "generate-seasonal-signals": {
        "task": "signals.tasks.generate_seasonal_signals",
        "schedule": crontab(minute=30, hour="23", day_of_week="1-5"),
    },
    "ai-expert-watchlist-deep": {
        "task": "ai_expert.tasks.run_expert_deep",
        "schedule": crontab(minute=0, hour="0", day_of_week="2-6"),
    },
    "aggregate-daily-final": {
        "task": "sentiment.tasks.aggregate_daily_sentiment",
        "schedule": crontab(minute=30, hour="0", day_of_week="2-6"),
    },
    # --- Weekly ---
    "fetch-13f-holdings": {
        "task": "data.tasks.fetch_13f_holdings",
        "schedule": crontab(minute=0, hour=6, day_of_week=6),
    },
    "fetch-macro": {
        "task": "data.tasks.fetch_macro_indicators",
        "schedule": crontab(minute=30, hour=6, day_of_week=6),
    },
    "recompute-industry-rotation": {
        "task": "signals.tasks.recompute_industry_rotation",
        "schedule": crontab(minute=0, hour=7, day_of_week=6),
    },
    "refresh-seasonal-patterns": {
        "task": "signals.tasks.refresh_seasonal_patterns",
        "schedule": crontab(minute=30, hour=7, day_of_week=6),
    },
    "knowledge-reembed": {
        "task": "knowledge.tasks.reembed_new",
        "schedule": crontab(minute=0, hour=8, day_of_week=6),
    },
    "record-signal-outcomes": {
        "task": "signallog.tasks.record_signal_outcomes",
        "schedule": crontab(minute=0, hour=9, day_of_week=6),
    },
    # --- New: Screening pipeline ---
    "weekly-fundamental-screen": {
        "task": "screener.tasks.run_weekly_fundamental_screen",
        "schedule": crontab(minute=0, hour=5, day_of_week=6),
    },
    "daily-screening-pipeline": {
        "task": "screener.tasks.run_daily_screening_pipeline",
        "schedule": crontab(minute=0, hour="13", day_of_week="1-5"),
    },
    "daily-regime-check": {
        "task": "screener.tasks.run_regime_check",
        "schedule": crontab(minute=0, hour="13", day_of_week="1-5"),
    },
    "detect-market-regime": {
        "task": "signals.tasks.detect_market_regime",
        "schedule": crontab(minute=0, hour="13", day_of_week="1-5"),
    },
    # --- New: Backtesting ---
    "weekly-backtest": {
        "task": "backtest.tasks.run_weekly_backtest",
        "schedule": crontab(minute=0, hour=10, day_of_week=6),
    },
    "seasonal-backtest": {
        "task": "backtest.tasks.run_seasonal_backtest",
        "schedule": crontab(minute=30, hour=10, day_of_week=6),
    },
    # --- New: Feedback loop ---
    "weekly-feedback-review": {
        "task": "feedback.tasks.run_weekly_review",
        "schedule": crontab(minute=0, hour=11, day_of_week=6),
    },
    # --- New: Supply chain ---
    "quarterly-supply-chain": {
        "task": "supplychain.tasks.extract_supply_chains",
        "schedule": crontab(minute=0, hour=12, day_of_week=6, month_of_year="1,4,7,10"),
    },
    # --- New: Alpaca sync ---
    "sync-alpaca-positions": {
        "task": "sandbox.tasks.sync_alpaca_positions_task",
        "schedule": crontab(minute="*/5", hour="14-21", day_of_week="1-5"),
    },
}