# Charter: Stock Picker & Investment Monitor

## Stack
- Python 3.12, Django 5, Django templates + HTMX + Chart.js + Plotly.js
- PostgreSQL 16 + pgvector, Redis 7
- Celery + Celery Beat for scheduling
- Ollama: qwen2.5:7b (fast), qwen2.5:14b-instruct (deep), nomic-embed-text (embeddings)
- Docker Compose deploy

## Directory tree
```
./
  config/          Django settings, celery, urls, wsgi/asgi
  tickers/         Ticker, Exchange, Sector, Industry, Watchlist, Holding models + views
  data/            OHLCV, Fundamental, News, Reddit, Insider, 13F, Options, Macro models + connectors
  sentiment/       SentimentScore, DailySentimentAggregate models + FinBERT/VADER runners
  signals/         Signal, TechnicalIndicator models + scoring engine
  knowledge/       KnowledgeDocument, KnowledgeChunk (pgvector) + RAG retrieval
  ai_expert/       AIExpertReport model + Ollama LLM integration + JSON parser
  sandbox/         Portfolio, Position, Trade, EquityPoint models + AutoTrader + views
  signallog/       SignalLogEntry model + views
  dashboard/       Market overview, watchlist, rotation views + base template
  static/          CSS, JS
```

## Module responsibilities

### tickers/
- `models.py` — Exchange, Sector, Industry, Ticker (yf_symbol property), Watchlist, Holding
- `views.py` — ticker_list, ticker_detail, ticker_refresh (HTMX)
- `urls.py` — list, detail, refresh
- `admin.py` — register all models
- `management/commands/ensure_seed.py` — seed 14 watchlist tickers + exchanges/sectors

### data/
- `models.py` — OHLCV, Fundamental, NewsArticle, RedditPost, InsiderTrade, InstitutionalHolding, OptionsSnapshot, MacroIndicator
- `connectors/yfinance_connector.py` — fetch OHLCV (intraday 15m + daily), fundamentals, option chains
- `connectors/reddit_connector.py` — PRAW scrape r/wallstreetbets, r/stocks, r/investing
- `connectors/finnhub_connector.py` — news headlines (free tier)
- `connectors/sec_edgar.py` — Form 4 insider trades, 13F-HR institutional, 10-K text
- `connectors/fred_connector.py` — macro indicators (rates, CPI)
- `connectors/gdelt_connector.py` — GDELT RSS news fallback
- `tasks.py` — Celery tasks: fetch_ohlcv_15m, fetch_ohlcv_daily, fetch_fundamentals, fetch_news, fetch_reddit, fetch_insider_trades, fetch_13f, fetch_options, fetch_macro

### sentiment/
- `models.py` — SentimentScore, DailySentimentAggregate
- `nlp_finbert.py` — FinBERT sentiment runner (headline → score)
- `nlp_vader.py` — VADER sentiment runner (social text → score)
- `tasks.py` — Celery tasks: score_news_sentiment, score_reddit_sentiment, aggregate_daily_sentiment

### signals/
- `models.py` — Signal, TechnicalIndicator
- `engine_technical.py` — EMA stack, RSI, MACD, Bollinger, ADX, ATR computation
- `engine_sentiment.py` — sentiment trend slope, moving averages
- `engine_options.py` — vol/OI ratio, IV percentile, put/call, unusual activity detection
- `engine_insider.py` — net insider buy/sell scoring
- `engine_seasonal.py` — X-year average monthly returns, seasonal pattern
- `engine_composite.py` — weighted blend → final Signal with confidence
- `tasks.py` — Celery tasks: compute_technicals, generate_day_trade_signals, generate_medium_signals, generate_seasonal_signals, signal_published callback

### knowledge/
- `models.py` — KnowledgeDocument, KnowledgeChunk (pgvector VectorField 768)
- `ingestion.py` — text extraction (PDF, txt, html), chunking (512 tokens, 64 overlap)
- `embeddings.py` — nomic-embed-text via Ollama → 768-dim vectors
- `rag_retrieval.py` — semantic search, category filter, reranking by signal type
- `tasks.py` — Celery tasks: process_document, embed_chunks, reembed_new

### ai_expert/
- `models.py` — AIExpertReport (structured JSON output fields)
- `ollama_client.py` — Ollama API client (chat completion, model selection)
- `prompt_templates.py` — system prompts per signal type, data formatting
- `output_parser.py` — parse LLM JSON response → AIExpertReport fields
- `expert_runner.py` — orchestrate: gather data + RAG → prompt → LLM → parse → store
- `tasks.py` — Celery tasks: run_expert_batch (hourly 7B), run_expert_deep (daily 14B watchlist)

### sandbox/
- `models.py` — Portfolio, Position, Trade, EquityPoint (with computed properties)
- `autotrader.py` — signal listener: BUY → open position (confidence-weighted), SELL → close position
- `revaluation.py` — 15-min position revaluation + equity curve + SPY benchmark
- `analytics.py` — win rate, Sharpe, max drawdown, avg win/loss, win rate by source
- `views.py` — sandbox_overview (3 portfolio tabs), sandbox_detail (equity chart, positions, trades, analytics), reset, equity_data (JSON), trades_data (JSON)
- `tasks.py` — Celery tasks: revalue_positions, record_equity_point, execute_signal_trade

### signallog/
- `models.py` — SignalLogEntry
- `views.py` — signal_log (hit-rate table, outcomes)
- `tasks.py` — Celery task: record_signal_outcome (check if signal was right after N days)

### dashboard/
- `views.py` — market_overview, watchlist, industry_rotation
- `templates/base.html` — dark theme, navbar, all nav links
- `templates/dashboard/overview.html` — sector heatmap, macro, watchlist quick view
- `templates/dashboard/watchlist.html` — 14 tickers with signals + AI expert verdicts
- `templates/dashboard/rotation.html` — sector YoY/seasonal strength

## Public interface signatures (authoritative)

### tickers.views
- `ticker_list(request) -> HttpResponse`
- `ticker_detail(request, symbol: str) -> HttpResponse`
- `ticker_refresh(request, symbol: str) -> HttpResponse`  (HTMX partial)

### data.connectors.yfinance_connector
- `fetch_ohlcv(ticker: Ticker, interval: str = "1d", period: str = "1y") -> list[dict]`
- `fetch_intraday_ohlcv(ticker: Ticker, interval: str = "15m") -> list[dict]`
- `fetch_fundamentals(ticker: Ticker) -> dict`
- `fetch_option_chain(ticker: Ticker) -> dict`

### data.connectors.reddit_connector
- `fetch_posts(subreddits: list[str], tickers: list[Ticker], limit: int = 100) -> list[dict]`

### data.connectors.finnhub_connector
- `fetch_news(tickers: list[Ticker]) -> list[dict]`

### data.connectors.sec_edgar
- `fetch_form4(ticker: Ticker) -> list[dict]`
- `fetch_13f(ticker: Ticker) -> list[dict]`

### data.connectors.fred_connector
- `fetch_indicators(series_ids: list[str]) -> list[dict]`

### sentiment.nlp_finbert
- `score_headline(text: str) -> tuple[float, float]`  (score, confidence)

### sentiment.nlp_vader
- `score_text(text: str) -> tuple[float, float]`

### signals.engine_composite
- `generate_signal(ticker: Ticker, signal_type: str) -> Signal | None`

### knowledge.rag_retrieval
- `retrieve(query: str, signal_type: str, top_k: int = 5) -> list[dict]`

### ai_expert.expert_runner
- `run_expert(ticker: Ticker, signal_type: str, model: str) -> AIExpertReport`

### ai_expert.ollama_client
- `chat(model: str, system: str, prompt: str) -> str`

### sandbox.autotrader
- `execute_buy(portfolio: Portfolio, signal: Signal) -> Trade | None`
- `execute_sell(portfolio: Portfolio, signal: Signal) -> Trade | None`

### sandbox.analytics
- `compute_performance(portfolio: Portfolio) -> dict`

## Conventions
- All models use BigAutoField
- DecimalField for all prices/quantities (max_digits=16, decimal_places=6 for prices)
- JSONField for raw API responses
- timezone-aware datetimes throughout
- Celery tasks in `tasks.py` per app, autodiscovered by config.celery
- Templates extend `base.html`, use HTMX for partial updates
- Views use Django ORM, no DRF
- No external JS build — CDN for HTMX, Chart.js, Plotly