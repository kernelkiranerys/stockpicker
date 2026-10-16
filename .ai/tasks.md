# Task DAG: Pivot Build

## Phase 1: Foundation
- [ ] P1.1 Update requirements.txt (add alpaca-py, backtrader, financialmodelingprep)
- [ ] P1.2 Update .env (add ALPACA_*, FMP_API_KEY placeholders)
- [ ] P1.3 Update settings.py (add screener, backtest, feedback, supplychain to INSTALLED_APPS + new config vars)
- [ ] P1.4 Update config/urls.py (add new app URLs)
- [ ] P1.5 Create 4 new app directories with __init__.py, apps.py, migrations/
- [ ] P1.6 Update seed command (10 real tickers replacing 14 placeholders)
- [ ] P1.7 Rebuild docker image + migrate + reseed

## Phase 2: Data connectors
- [ ] P2.1 data/connectors/fmp_connector.py — FMP API (fundamentals, income stmt, balance sheet, ratios)
- [ ] P2.2 data/connectors/alpaca_connector.py — Alpaca client (paper trading, real-time bars, account, orders)
- [ ] P2.3 data/connectors/openinsider_scraper.py — OpenInsider Form 4 cluster buying
- [ ] P2.4 Update yfinance_connector.py — Add 1-min and 5-min intraday bar fetching
- [ ] P2.5 data/tasks.py — Add new tasks: fetch_intraday_bars, fetch_fmp_fundamentals, sync_alpaca_positions

## Phase 3: Confluence signal engine
- [ ] P3.1 signals/engine_vwap.py — Session VWAP, anchored VWAP, cross/pullback/slope/divergence
- [ ] P3.2 signals/engine_rvol.py — Relative volume (current vs 20-day SMA)
- [ ] P3.3 signals/engine_rsi_divergence.py — Price/RSI divergence detection, 80/20 trend thresholds
- [ ] P3.4 signals/engine_regime.py — VIX, Treasury yield delta, trending vs range-bound, strategy mode
- [ ] P3.5 signals/engine_confluence.py — 4-layer confluence scoring (replaces engine_composite.py)
- [ ] P3.6 signals/models.py — Add ConfluenceSignal model, RegimeState model
- [ ] P3.7 signals/tasks.py — Update: generate_confluence_signals, detect_regime, compute_vwap

## Phase 4: Screening pipeline (screener/ app)
- [ ] P4.1 screener/models.py — ScreenedUniverse, ScreeningResult, RegimeSnapshot
- [ ] P4.2 screener/stage1_fundamentals.py
- [ ] P4.3 screener/stage2_liquidity.py
- [ ] P4.4 screener/stage3_correlation.py
- [ ] P4.5 screener/stage4_regime.py
- [ ] P4.6 screener/stage5_conviction.py
- [ ] P4.7 screener/stage6_news.py
- [ ] P4.8 screener/tasks.py — Weekly screen, daily narrow, intraday pipeline
- [ ] P4.9 screener/views.py + urls.py + templates

## Phase 5: Backtesting (backtest/ app)
- [ ] P5.1 backtest/models.py — BacktestRun, BacktestTrade
- [ ] P5.2 backtest/engine.py — Backtrader integration, point-in-time, pre-computed signals
- [ ] P5.3 backtest/strategies.py — Confluence strategy, seasonal strategy, mean-reversion strategy
- [ ] P5.4 backtest/tasks.py
- [ ] P5.5 backtest/views.py + urls.py + templates

## Phase 6: Feedback loop (feedback/ app)
- [ ] P6.1 feedback/models.py — LessonLearned, PromptVersion, TradeReview
- [ ] P6.2 feedback/weekly_review.py — Failed trade → LLM reflection → lesson
- [ ] P6.3 feedback/prompt_injector.py — Inject lessons into AI expert prompts
- [ ] P6.4 feedback/tasks.py
- [ ] P6.5 feedback/views.py + urls.py + templates

## Phase 7: Supply chain (supplychain/ app)
- [ ] P7.1 supplychain/models.py — CompanyRelationship
- [ ] P7.2 supplychain/extractor.py — 10-K section pull + LLM extraction
- [ ] P7.3 supplychain/monitor.py — News monitoring for relationships
- [ ] P7.4 supplychain/tasks.py
- [ ] P7.5 supplychain/views.py + urls.py + templates

## Phase 8: Upgrade AI expert
- [ ] P8.1 Update prompt_templates.py — confluence data, macro deltas, regime, lessons, conviction 0-100
- [ ] P8.2 Update expert_runner.py — gather confluence data, inject lessons, output conviction 0-100

## Phase 9: Alpaca integration (sandbox replacement)
- [ ] P9.1 sandbox/alpaca_client.py — Alpaca paper trading API client
- [ ] P9.2 sandbox/alpaca_autotrader.py — Conviction >75 → execute order
- [ ] P9.3 Update sandbox/tasks.py — Alpaca position sync, equity tracking
- [ ] P9.4 Update sandbox/views.py + templates — real Alpaca positions

## Phase 10: Dashboard updates
- [ ] P10.1 Update base.html nav (add screener, backtest, feedback, supplychain links)
- [ ] P10.2 Update dashboard/views.py — overview with regime indicator
- [ ] P10.3 Update watchlist template — conviction scores, confluence badges
- [ ] P10.4 Update ticker_detail — VWAP chart, confluence panel, supply chain section
- [ ] P10.5 New screener template
- [ ] P10.6 New backtest template
- [ ] P10.7 New feedback template
- [ ] P10.8 New supplychain template

## Phase 11: Celery schedule
- [ ] P11.1 Update config/celery.py — weekly screen, daily pre-market, intraday confluence, weekly backtest/feedback/10K

## Phase 12: Final verification
- [ ] P12.1 Syntax check all Python
- [ ] P12.2 Docker rebuild + migrate + reseed
- [ ] P12.3 Verify dashboard loads at :9654
- [ ] P12.4 Run data collection + signal generation smoke test
- [ ] P12.5 Update README
- [ ] P12.6 SimpleX notification