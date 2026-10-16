# Pivot Spec: Research-Backtesting Loop

## Watchlist (10 tickers)
| Symbol | Company | Sector | Exchange | yf_suffix |
|---|---|---|---|---|
| AMZN | Amazon | Consumer/Tech | NASDAQ | |
| CPN | Centrica | Energy | LSE | .L |
| CF | CF Industries | Materials (Fertilizer) | NYSE | |
| NTR | Nutrien | Materials (Fertilizer) | NYSE | |
| MOS | Mosaic | Materials (Fertilizer) | NYSE | |
| DAL | Delta Air Lines | Industrials (Airlines) | NYSE | |
| UAL | United Airlines | Industrials (Airlines) | NASDAQ | |
| AAL | American Airlines | Industrials (Airlines) | NASDAQ | |
| IAG | IAG (British Airways parent) | Industrials (Airlines) | LSE | .L |
| XOM | Exxon Mobil | Energy | NYSE | |

## API Keys needed (user will provide)
- ALPACA_API_KEY, ALPACA_SECRET_KEY (paper trading)
- FMP_API_KEY (Financial Modeling Prep — toggle with yfinance)

## Stack (unchanged)
- Django 5 + HTMX + Postgres + pgvector + Celery + Docker Compose
- Ollama: qwen2.5:7b (fast), qwen2.5:14b-instruct (deep), nomic-embed-text (embeddings)

## New Apps (4)
- screener/ — 7-stage screening pipeline
- backtest/ — Backtrader integration
- feedback/ — Self-improvement loop (Lessons Learned)
- supplychain/ — Supply chain graph from 10-Ks

## Replaced
- signals/engine_composite.py → engine_confluence.py (VWAP + EMA + RSI div + RVOL + ATR + MACD + options)
- sandbox/homemade → Alpaca paper trading API

## New signal files
- signals/engine_vwap.py — Session VWAP, anchored VWAP, cross/pullback/slope/divergence
- signals/engine_rvol.py — Relative volume vs 20-day avg, >2.0 = unusual
- signals/engine_rsi_divergence.py — Price/RSI divergence, trend-adjusted thresholds (80/20)
- signals/engine_regime.py — VIX, Treasury yield deltas, trending vs range-bound
- signals/engine_confluence.py — 4-layer confluence: VWAP + trend + momentum + volume

## New data connectors
- data/connectors/fmp_connector.py — Financial Modeling Prep API
- data/connectors/alpaca_connector.py — Alpaca paper trading + real-time data
- data/connectors/openinsider_scraper.py — OpenInsider Form 4 cluster buying
- yfinance_connector.py — Add 1-min, 5-min intraday bars for VWAP

## Screening pipeline (7 stages, funnel)
1. Fundamental screen (EPS, market cap, sector, valuation) → ~200 stocks
2. Liquidity/volatility filter (vol >5M, spread, daily range >2%, beta >1.2) → 50-100
3. Historical signal correlation (backtest win rate >55%) → ranked candidates
4. Regime detection (VIX, Treasury deltas, trending/range-bound) → strategy mode
5. AI conviction scoring (LLM 0-100, threshold >75) → high-conviction only
6. News/sentiment overlay → filter negative catalysts
7. Execute only >75 conviction in Alpaca

## Backtesting (Backtrader)
- Point-in-time awareness (no look-ahead bias)
- Pre-computed signals (Approach A: run LLM on history first, feed to Backtrader)
- Slippage: 0.1%, Commission: 0.1%
- Metrics: win rate, avg return, max drawdown, Sharpe

## Feedback loop
- Weekly: fetch failed trades → LLM reflection ("what did you miss?") → Lessons Learned table
- Inject lessons into future AI expert prompts
- Track prompt versions and their performance

## Supply chain
- Pull 10-K "Risk Factors" + "Business" sections from SEC EDGAR
- LLM extraction: customers, suppliers, competitors
- Store as CompanyRelationship graph in Postgres
- Monitor news for identified relationships

## AI Expert upgrades
- Include confluence data (VWAP position/slope, EMA relationship, RSI divergence, RVOL)
- Include macro deltas (yield change 30 days, not just level)
- Include regime context ("high-vol trending market")
- Include Lessons Learned from feedback loop
- Conviction scoring 0-100 (not 0-1), threshold >75 for execution
- Pro interpretation: P/E vs 5-year range, insider cluster buying, yield deltas

## Pipeline flow
```
WEEKLY: Fundamental screen → update universe (~200)
DAILY PRE-MARKET: Liquidity/vol filter → 50-100 candidates → Regime detection → rank by historical win rate
INTRADAY: Confluence signals on top candidates → LLM conviction 0-100 → only >75 → Alpaca execute
POST-MARKET: Record trades + outcomes → update signal log
WEEKLY: Backtest recent signals → Feedback review → Lessons Learned → 10-K supply chain extraction
```

## New dependencies
- alpaca-py>=0.20
- backtrader>=1.9.78
- financialmodelingprep>=1.5

## Dashboard pages (updated)
1. Overview (regime indicator, screening funnel status)
2. Watchlist (10 tickers + conviction scores + confluence signals)
3. Screener (candidate funnel, 7-stage pipeline view) ← NEW
4. Ticker Detail (VWAP chart, confluence signals, supply chain, AI expert)
5. Backtest (run history, equity curves, metrics) ← NEW
6. Practice Portfolio (Alpaca paper trading, real positions)
7. Signal Log (hit-rate, by confluence type)
8. Feedback (Lessons Learned, prompt versions) ← NEW
9. Supply Chain (relationship graph) ← NEW
10. Knowledge Base (RAG documents)