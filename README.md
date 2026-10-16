# Stock Picker & Investment Monitor

AI-powered stock research terminal with confluence signal engine, screening pipeline, backtesting, feedback loop, and Alpaca paper trading.

## Architecture: Research-Backtesting Loop

```
WEEKLY: Fundamental screen → update universe
DAILY PRE-MARKET: Liquidity/vol filter → regime detection → rank by historical win rate
INTRADAY: Confluence signals (VWAP+EMA+RSI div+RVOL) → LLM conviction 0-100 → only >75 executes
POST-MARKET: Record outcomes → update signal log
WEEKLY: Backtest (Backtrader) → Feedback review (LLM reflection → Lessons Learned) → 10-K supply chain extraction
```

## Watchlist (10 tickers)
AMZN, CNA.L (Centrica), CF, NTR, MOS (fertilizer), DAL, UAL, AAL, IAG.L (British Airways), XOM

## Stack
- Django 5 + HTMX + Chart.js + Plotly.js
- PostgreSQL + pgvector (RAG knowledge base)
- Celery + Redis (scheduling)
- Ollama: qwen2.5:7b (fast), qwen2.5:14b-instruct (deep), nomic-embed-text (embeddings)
- Docker Compose (web, worker, beat, db, redis)

## Dashboard (port 9654)
1. **Overview** — market summary, regime indicator
2. **Watchlist** — 10 tickers with confluence signals + AI expert verdicts
3. **Screener** — 7-stage screening pipeline funnel, regime snapshot, conviction scores
4. **Signals** — all signals with filters
5. **Ticker Detail** — VWAP chart, confluence panel, technicals, AI expert section
6. **Portfolio** — Alpaca paper trading positions + equity curves
7. **Backtest** — Backtrader run history, returns, win rate, Sharpe, drawdown
8. **Feedback** — Lessons Learned from failed trades, prompt versions
9. **Supply Chain** — customer/supplier/competitor relationships from 10-K LLM extraction
10. **Signal Log** — hit-rate tracking
11. **Knowledge Base** — RAG document management

## Confluence Signal Engine
4 layers must align: VWAP direction + trend alignment (EMA) + momentum (RSI divergence) + volume (RVOL).
Pro interpretation: RSI divergence (not just overbought/oversold), trend-adjusted thresholds (80/20), VWAP slope/pullback/divergence, RVOL >2.0.

## API Keys (in .env)
- ALPACA_API_KEY / ALPACA_SECRET_KEY — paper trading (free at alpaca.markets)
- FMP_API_KEY — Financial Modeling Prep (free at financialmodelingprep.com)
- FINNHUB_API_KEY, REDDIT_CLIENT_ID/SECRET, FRED_API_KEY

## Quick Start
```bash
docker compose up -d
docker compose exec web python manage.py ensure_seed
# Dashboard at http://localhost:9654/dashboard/
```

## Apps
- tickers/ — Ticker, Exchange, Sector, Watchlist models
- data/ — Connectors: yfinance, FMP, Alpaca, Finnhub, Reddit, SEC EDGAR, FRED, GDELT, OpenInsider
- sentiment/ — FinBERT (news) + VADER (Reddit) + AI expert sentiment
- signals/ — Confluence engine: VWAP, RVOL, RSI divergence, regime, composite
- screener/ — 7-stage screening pipeline + regime detection
- backtest/ — Backtrader integration with point-in-time awareness
- feedback/ — Self-improvement loop (Lessons Learned → prompt injection)
- supplychain/ — 10-K LLM extraction of customer/supplier/competitor relationships
- ai_expert/ — Ollama LLM integration, RAG retrieval, conviction 0-100
- knowledge/ — pgvector RAG: document ingestion, embeddings, semantic retrieval
- sandbox/ — Alpaca paper trading + homemade portfolio backup
- signallog/ — Signal hit-rate tracking