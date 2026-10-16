# Project Status

## What's Done

### Core Infrastructure
- Django 5 + HTMX + Postgres + pgvector + Celery + Docker Compose (5 services)
- 13 Django apps, 181 files, 6,821 lines of Python
- All 9 dashboard pages live at `localhost:9654` (returning 200)
- Celery beat schedule with 30+ scheduled tasks (intraday, daily, weekly, quarterly)
- Ollama integration: qwen2.5:7b (fast), qwen2.5:14b-instruct (deep), nomic-embed-text (embeddings)

### Watchlist (10 tickers, seeded)
AMZN, CNA.L (Centrica), CF, NTR, MOS (fertilizer), DAL, UAL, AAL, IAG.L (British Airways), XOM

### Data Layer (6 connectors)
- **yfinance** — daily OHLCV, intraday 1m/5m bars for VWAP, fundamentals, option chains, SPY benchmark
- **FMP** (Financial Modeling Prep) — income statement, balance sheet, cash flow, ratios, key metrics, P/E 5-year percentile
- **Alpaca** — paper trading API client (account, positions, market orders, real-time quotes, intraday bars)
- **OpenInsider scraper** — Form 4 cluster buying detection (multiple officers, open market only, excludes option exercises)
- **SEC EDGAR** — Form 4 insider trades, 13F-HR institutional holdings, 10-K section extraction for supply chain
- **Finnhub + GDELT + Reddit (PRAW)** — news headlines, social sentiment

### Signal Engine (confluence model)
- **engine_vwap.py** — Session VWAP, anchored VWAP, cross/pullback/slope/divergence detection
- **engine_rvol.py** — Relative volume vs 20-day average, >2.0 = unusual, volume trend
- **engine_rsi_divergence.py** — Price/RSI divergence (bullish/bearish), trend-adjusted thresholds (80/20 in strong trends)
- **engine_regime.py** — VIX, Treasury yield deltas (30-day bps change), yield curve, SPY trend, regime classification (trending_bull/bear, range_bound, high/low volatility)
- **engine_confluence.py** — 4-layer confluence: VWAP direction + trend alignment + momentum confirmation + volume must align. Weighted composite with per-signal-type weights.
- **Existing engines retained** — engine_technical.py (EMA/RSI/MACD/Bollinger/ADX/ATR), engine_sentiment.py, engine_options.py, engine_insider.py, engine_seasonal.py

### Screening Pipeline (7 stages, funnel)
1. **Fundamental screen** — market cap >$2B, positive EPS, sector filter
2. **Liquidity/volatility filter** — avg volume >5M, daily range >2%, beta >1.0
3. **Historical signal correlation** — backtest win rate per stock, >55% threshold
4. **Regime detection** — VIX/yield deltas/SPY trend → strategy mode selection
5. **AI conviction scoring** — LLM generates 0-100 score, threshold >75 for execution
6. **News/sentiment overlay** — filter stocks with negative catalysts (3+ negative headlines)
7. **Execute** — only >75 conviction proceeds to Alpaca

### Backtesting (Backtrader integration)
- Point-in-time awareness (no look-ahead bias)
- Pre-computed signal approach (Approach A from trading.md)
- Slippage (0.1%) and commission (0.1%) simulation
- Metrics: total return, win rate, max drawdown, Sharpe ratio, avg win/loss, trade count
- Weekly + seasonal backtest tasks scheduled

### Feedback Loop (self-improvement)
- Weekly review of failed trades
- LLM reflection: "This trade failed. Here is the context you used. What did you miss?"
- Lessons Learned table stored in Postgres
- Active lessons injected into future AI expert prompts
- TradeReview records track each reviewed trade

### Supply Chain Analysis
- Pulls 10-K "Business" and "Risk Factors" sections from SEC EDGAR
- LLM extracts named customers, suppliers, competitors
- CompanyRelationship graph stored in Postgres
- Quarterly extraction task scheduled

### AI Expert (upgraded)
- Prompt includes: confluence data (VWAP position/slope, EMA relationship, RSI divergence, RVOL)
- Macro deltas (yield change 30 days, not just level)
- Regime context ("high-vol trending market")
- P/E vs company's own 5-year range
- Insider cluster buying detection
- Supply chain relationships
- Past Lessons Learned from feedback loop
- Conviction scoring 0-100 (threshold >75 for execution)
- RAG retrieval from pgvector knowledge base

### Paper Trading (sandbox)
- 3 portfolios: Day Trader, Swing, Seasonal
- Homemade autotrader (confidence-weighted position sizing)
- Alpaca integration (real paper trading when API keys provided)
- Equity curve tracking with SPY benchmark
- Performance analytics (win rate, Sharpe, drawdown, by signal source)

### Data Populated
- 6,174 OHLCV bars (daily, 1-year history per ticker)
- 89 technical indicators
- 32 confluence signals
- 1 regime snapshot (trending_bull)
- 3 sandbox portfolios seeded

---

## What's Left To Do

### Requires Your API Keys (in `.env`)
- [ ] **Alpaca** — add `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` to activate real paper trading
- [ ] **FMP** — add `FMP_API_KEY` for clean fundamental data (toggle with yfinance to compare)
- [ ] **Finnhub** — add `FINNHUB_API_KEY` for real-time news
- [ ] **Reddit** — add `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` for social sentiment
- [ ] **FRED** — add `FRED_API_KEY` for macro indicators (VIX, Treasury yields)

### RAG Knowledge Base (empty — needs content)
- [ ] Upload texts on day trading, investing, TA, options, sector rotation, SEC filings via Knowledge Base page
- [ ] Run `docker compose exec worker celery -A config call knowledge.tasks.process_new_documents`
- [ ] Run `docker compose exec worker celery -A config call knowledge.tasks.reembed_new`
- [ ] Suggested sources: Investopedia guides, Buffett shareholder letters, CBOE education, SEC investor.gov, academic papers on mean reversion

### Tuning & Configuration
- [ ] **Signal threshold** — currently set to 0.15 for testing (was 0.55). Raise to 0.30-0.40 for production use once data is flowing.
- [ ] **Conviction threshold** — currently 75 (in settings as CONVICTION_THRESHOLD). Adjust based on how many signals you want to execute.
- [ ] **Position sizing** — currently confidence-weighted. Adjust in sandbox/models.py Portfolio.SIZING_CHOICES.
- [ ] **Confluence weights** — adjust per-signal-type weights in signals/engine_confluence.py WEIGHTS dict.

### Operational
- [ ] **Celery tasks running** — worker and beat are up, but tasks that need API keys (news, Reddit, FRED) will skip silently until keys are added
- [ ] **AI expert batch** — takes 2-3 min per ticker (fetches intraday VWAP + OpenInsider + regime + RAG + LLM). Runs as background Celery task. Test on single ticker first: `docker compose exec web python manage.py shell -c "from ai_expert.expert_runner import run_expert; from tickers.models import Ticker; run_expert(Ticker.objects.get(symbol='AMZN'), 'seasonal_swing')"`
- [ ] **Daily screening pipeline** — run manually first to verify: `docker compose exec web python manage.py shell -c "from screener.tasks import run_daily_screening_pipeline; run_daily_screening_pipeline()"`
- [ ] **Backtest** — run manually: `docker compose exec web python manage.py shell -c "from backtest.tasks import run_weekly_backtest; run_weekly_backtest()"`

### Missing/Incomplete
- [ ] **Options data** — yfinance option chain has Decimal serialization issue in raw JSON field. Options scoring still works via engine_options.py but OptionsSnapshot records fail to save. Fix: convert Decimals to floats in data/tasks.py fetch_options_data before JSON storage.
- [ ] **TimescaleDB** — trading.md suggests TimescaleDB for time-series. Currently using plain Postgres. Can add TimescaleDB extension later if query performance becomes an issue.
- [ ] **Survivorship bias** — backtest uses current ticker list only. For production backtesting, use survivorship-bias-free data (Norgate Data plugin for Backtrader).
- [ ] **Frontend polish** — dashboard is functional but basic. Could add: VWAP chart on ticker detail, confluence layer visualization, screening funnel diagram, supply chain relationship graph (D3.js), backtest equity curve charts.
- [ ] **Streamlit alternative** — trading.md suggests Streamlit. Currently Django+HTMX. Could add a Streamlit app alongside Django for rapid prototyping if desired.
- [ ] **Pre-market gap analysis** — not yet implemented (Stage 4 from trading.md)
- [ ] **Opening range breakout** — signal type mentioned in trading.md, not yet implemented
- [ ] **Stochastic oscillator** — mentioned in trading.md, not yet implemented

### Files to Review
- `.ai/pivot-spec.md` — full pivot specification
- `.ai/tasks.md` — task DAG with completion status
- `trading.md` — original blueprint document
- `AGENTS.md` — local-LLM delegation protocol for development