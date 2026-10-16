This is a genuinely ambitious and smart project. You're essentially building a personal quantitative research desk. Here is the blueprint for how to do it, mapping Bloomberg's professional data to free sources, and outlining the architecture for your AI-driven terminal.

The Blueprint: Your Free AI Terminal

You are building a Research-Backtesting Loop. Here is the architecture:

Data Layer: Free APIs feeding into a local database.
Intelligence Layer: Vector DB of texts + LLM for analysis.
Signal Layer: LLM generates actionable signals based on data + text.
Execution Layer: Paper trading API receives the signal.
Feedback Layer: Results are fed back to refine the LLM's prompts/weights.

The Tech Stack

Database: PostgreSQL (with TimescaleDB for time-series data). It's free, open-source, and handles both relational data (company info) and time-series (prices) perfectly.
Vector DB: ChromaDB or Qdrant (local, free). ChromaDB is Python-native and easiest to start with.
LLM: Ollama. Run local models like Llama 3 (8B or 70B if you have the RAM/VRAM) or Mistral. This ensures privacy, zero API costs, and uncensored analysis. Alternatively, use the Venice.ai API if you want to offload compute but keep privacy.
Paper Trading: Alpaca API. They offer a free paper trading API with real-time market data that executes simulated trades. It's built for developers.
Backtesting: Backtrader (Python library). It integrates with Pandas dataframes and allows you to test strategies on historical data before live paper trading.
Frontend: Streamlit (Python). You can build a decent dashboard in a weekend without frontend experience.

Data Mapping: Bloomberg vs. Free Alternatives

This is what professionals see on Bloomberg and where you get the same data for free.

Company Fundamentals (Bloomberg: FA, RV)

Professionals use this to compare valuation and financial health.

SEC EDGAR API: The source of truth for 10-Ks, 10-Qs, and 8-Ks. You can pull XBRL data (structured financials) directly. This is what Bloomberg parses to show you P/E ratios.
Financial Modeling Prep (FMP): Free tier gives you 250 API calls/day. Covers income statements, balance sheets, cash flow, and ratios. Cleaner than scraping EDGAR yourself.
Yahoo Finance (yfinance library): Unofficial but reliable for historical prices, splits, dividends, and basic fundamentals.

Macro & Economic Data (Bloomberg: ECO, ECOW)

Professionals use this to understand the environment stocks operate in.

FRED API: As discussed. Get Treasury yields, inflation, employment.
Econoday / Investing.com Economic Calendar: Free calendars showing when data is released and consensus estimates. Crucial for day trading around releases.

Ownership & Flow (Bloomberg: OWN, INSR)

Professionals use this to see what the "smart money" is doing.

OpenInsider.com: Free, scraped from SEC Form 4 filings. Shows insider buying/selling in real-time.
WhaleWisdom (Free tier): Aggregates 13F filings (institutional holdings). Lets you see what hedge funds bought/sold last quarter.

News & Sentiment (Bloomberg: N, NSOURCE)

Professionals use this to get ahead of market reactions.

Finnhub (Free tier): Real-time company news and press releases.
NewsAPI.org (Free tier): Aggregate news from major outlets.
GDELT Project: Free, massive database of global news events. You can query it for mentions of your companies and get sentiment scores.

Supply Chain (Bloomberg: SPLC)

This is Bloomberg's proprietary edge. They map who sells to whom.

   DIY via 10-Ks: You will use your LLM to extract this. Pull the "Risk Factors" and "Business" sections of 10-Ks from EDGAR. Prompt your LLM: "Extract all named customers, suppliers, and competitors from this text." Store these relationships in your Postgres DB.

Building the Intelligence Layer

This is where your system becomes more than just a data aggregator.

Populating the Vector DB

Source Texts: Download PDFs of Porter's books, Dorsey's book, academic papers on mean reversion, and every 10-K for your target companies (Centrica, Amazon, Fertilizer stocks, Airlines).
Chunking: Break texts into 500-word chunks.
Embedding: Use a local embedding model (e.g., all-MiniLM-L6-v2 via HuggingFace) to convert chunks to vectors.
Storage: Store in ChromaDB with metadata (company, year, source type).

The Prediction Engine

You don't just ask the LLM "Will AMZN go up?" You build a pipeline:

Data Aggregation: Python script pulls current price, 50-day EMA, 200-day EMA, RSI, and current FRED macro data (e.g., 10-year yield).
Context Retrieval: Query ChromaDB with the current state. E.g., "What does the mean-reversion strategy say about RSI between 40-60 and price below 200-day EMA?"
LLM Synthesis: Feed the LLM the current data + retrieved context. Prompt: "Based on the seasonal strategy for AMZN (Oct entry, Feb exit), current technicals [insert data], and macro context [insert data], generate a signal: BUY, SELL, or HOLD. Provide reasoning."
Signal Output: The LLM outputs a structured JSON: {"action": "BUY", "confidence": 0.75, "reasoning": "..."}.

The Feedback Loop (Self-Improvement)

This is the hardest part. LLMs don't "learn" automatically. You have to build the learning loop.

Phase 1: Backtesting
Take historical data (e.g., 2020-2023).
Run your LLM pipeline on each day in history.
Use Backtrader to simulate executing the LLM's signals.
Measure: Win rate, average return, max drawdown.

Phase 2: Prompt Optimization
If the strategy fails, the problem is likely the prompt or the context.
Do not try to fine-tune the model immediately. Do refine the prompt.
   Example: If the LLM tells you to buy AMZN in October but it dumps, check the macro data. Did you feed it the 10-year yield? If not, add that to the prompt: "Consider the 10-year Treasury yield. If it is rising rapidly, reduce confidence in long equity positions."

Phase 3: Live Paper Trading
Once backtested, connect to Alpaca.
Run the pipeline daily before market open.
If the LLM says BUY, send the order to Alpaca.
Track results in a spreadsheet.

Phase 4: The "Learning"
Every week, run a script:
       Fetch the trades Alpaca executed.
       Check if they were profitable.
       If not, ask the LLM: "This trade failed. Here is the context you used. What did you miss?"
       Store this reflection in a "Lessons Learned" table in Postgres.
       Include this table in future prompts: "Past mistakes to avoid: [insert recent lessons]."

How Professionals Use This Data (Your Learning Path)

To build this, you need to understand what the data means. Here is the translation:

Technicals (Price, Volume, EMAs)
Pro View: They don't use RSI to find "oversold" stocks. They use it to measure momentum divergence. If price makes a new high but RSI makes a lower high, professionals see distribution (sellers stepping in). Your LLM needs to check for divergence, not just absolute RSI levels.

Fundamentals (P/E, EV/EBITDA)
   Pro View: They don't compare P/E to the S&P 500. They compare it to the company's own historical range and its direct competitors. For your seasonal strategy, you want to know if AMZN is cheap relative to its own 5-year average. Your LLM should query: "Is current P/E in the bottom quartile of AMZN's 5-year range?"

Macro (Yields, Inflation)
   Pro View: They don't just look at the yield. They look at the change in yield. A 5% 10-year yield is fine if it's been 5% for a year. If it went from 2% to 5% in 3 months, that's a shock. Your LLM needs the delta, not just the level: "Has the 10-year yield risen >50bps in the last 30 days?"

Insider Ownership (INSR)
   Pro View: They ignore stock options and routine sales. They look for cluster buying (multiple insiders buying at once) and open market purchases (not option exercises). Your LLM should filter OpenInsider data: "Are there >3 open market buys by officers (not directors) in the last 30 days?"

Supply Chains (SPLC)
Pro View: If a major supplier has an earnings miss, the customer might benefit (lower input costs) or suffer (supply disruption). Your LLM should monitor news for companies you identified as suppliers to AMZN or Centrica.

Next Steps

Start Small: Don't build the whole thing at once. Pick one sector (e.g., Fertilizer) and one stock.
Data First: Get yfinance and FRED data flowing into Postgres.
Texts Second: Download 5 fertilizer 10-Ks and the academic papers on fertilizer seasonality. Put them in ChromaDB.
Simple LLM Query: Write a script that asks the LLM: "Given current price [X] and current RSI [Y], and this excerpt on fertilizer seasonality, should I buy?"
Paper Trade: Connect to Alpaca and let it run.

How Backtrader Works: The Mechanics

Backtrader operates on a principle called event-driven simulation. It doesn't just look at a spreadsheet and calculate "if I bought here and sold here." It recreates the experience of trading day by day, where your strategy only knows what has happened up to that point.

The Core Concept: Point-in-Time Awareness

This is the critical difference. In a naive backtest, you load all data and calculate signals. Your strategy can "see the future." Backtrader prevents this.

Here's how it works mechanically:

The Data Feed

You load historical data into a Pandas DataFrame, then wrap it in a Backtrader data feed:

Backtrader stores this internally as a series of "bars." Each bar is one day (or whatever timeframe you choose) with OHLCV data.

The Strategy Class

Your trading logic lives in a bt.Strategy subclass:

The Engine (Cerebro)

Backtrader's engine is called Cerebro. It orchestrates everything:

What Actually Happens Under the Hood

When you call cerebro.run(), here is the exact sequence:

Cerebro loads all bars into memory in chronological order.
It calls your strategy's init once. Indicators are calculated but only using data up to the warmup period.
It begins iterating through bars one at a time, oldest first.
For each bar, it calls your strategy's next() method.
Inside next(), you can access the current bar's data and all prior bars, but never future bars.
If you call self.buy(), Cerebro creates an order. The order executes on the NEXT bar's open price by default (you can change this).
Cerebro updates your portfolio value, tracks commissions, and records the trade.
It moves to the next bar and repeats.
When all bars are processed, it returns the final portfolio value and trade history.

The Point-in-Time Enforcement

This is what makes it realistic:

Your strategy literally cannot see January 16's data while it's on January 15. This prevents look-ahead bias, which is the #1 reason backtests fail in real trading.

Integrating Your LLM Signals

This is where it gets interesting for your project. You have two approaches:

Approach A: Pre-Compute Signals (Faster, Simpler)

Run your LLM pipeline on all historical dates first, store signals in a CSV, then feed them to Backtrader:

Approach B: Live LLM Calls (Slower, More Realistic)

Call the LLM during the backtest itself. This is slower but tests the actual pipeline:

The Metrics Backtrader Gives You

After cerebro.run(), you can extract detailed performance:

Common Pitfalls to Avoid

Survivorship Bias: If your historical data only includes stocks that still exist, your results are inflated. Use a survivorship-bias-free database like the one from the Norgate Data plugin for Backtrader.
Overfitting: If you tune your LLM prompts until the backtest looks great, you've fit to noise. Test on data the LLM never saw during prompt development.
Ignoring Slippage: Set realistic slippage. cerebro.broker.setslippageperc(perc=0.001) simulates getting a slightly worse price than you expect.
Transaction Costs: Include commissions. They kill high-frequency strategies. cerebro.broker.setcommission(commission=0.001) is roughly what a discount broker charges.

For Your Specific Setup

Since you're building the full pipeline (data → vector DB → LLM → signal → backtest), I'd recommend Approach A (pre-compute) for your first iteration. Here's why:

You can debug the LLM output separately from the backtest logic
Running the LLM on 3 years of daily data takes hours; doing it inside Backtrader makes iteration painful
You can store the LLM's reasoning alongside the signal and review it later

Once the pre-computed version works, switch to Approach B to test the live pipeline end-to-end.

Short-Term Signals Used in Automated Day Trading

The search results paint a clear picture: successful automated day trading isn't about using 20 indicators. It's about a focused stack of 3-4 indicators that measure different things. A 2024 survey of 1,200 profitable day traders found that 89% use three or fewer indicators. Here are the signals that actually work and why Python libraries like Backtrader, VectorBT, and Zipline were built to test them.

The Core Signal Stack

The standard professional setup is: VWAP (session reference) + one trend indicator (SuperTrend or EMA) + one momentum oscillator (RSI or MACD). More than four indicators produces conflicting signals and slower decisions—both costly in fast-moving markets.

VWAP — The King of Intraday Signals

VWAP (Volume Weighted Average Price) is the single most important day trading indicator, used by 78% of profitable traders as their primary reference for intraday fair value and institutional order flow. It calculates the average price weighted by volume throughout the trading session, resetting each day.

What bots look for:
VWAP Cross: Price moving from below VWAP to above it (bullish) or above to below (bearish). A completed close moving from at or below VWAP to above it, with both observations in the same anchor window, is a testable entry rule.
VWAP Pullback/Rejection: Price pulls back to VWAP and bounces off it. VWAP acts as dynamic support/resistance. In range-bound markets, VWAP pullbacks highlight trading opportunities because prices deviating significantly from VWAP often revert back.
VWAP Slope: The slope of VWAP hints at market momentum. A rising VWAP slope confirms bullish momentum; a flat VWAP suggests consolidation.
VWAP Divergence: Price makes higher highs while VWAP makes lower highs—this signals weakening bullish momentum and potential reversal.

Why it works for bots: VWAP is an institutional benchmark. Price above VWAP means buyers are in control; below means sellers dominate. Institutional traders benchmark their execution against VWAP, making VWAP levels technically significant in ways that don't apply equally to forex or crypto.

EMA Combinations — Trend Direction

The 9-period and 20-period EMA combination identifies short-term momentum direction and provides dynamic support and resistance levels that update with each candle. Moving averages are used by 72% of surveyed profitable traders.

What bots look for:
EMA Cross: 9 EMA crosses above 20 EMA (bullish) or below (bearish)
Price vs EMA: Price holding above both VWAP and the 9 EMA gives more confidence the move has legs.
EMA as Filter: Price above 50-EMA and holding above VWAP intraday = strong alignment.

RSI — Momentum and Exhaustion

RSI produces exact numeric values that translate directly into buy/sell rules, which is why it's great for bots. It compares recent gains to recent losses over a set period—usually 14 periods.

What bots look for:
Overbought/Oversold: Above 70 signals overbought (potential pullback); below 30 signals oversold (potential buying opportunity).
Divergence at Extremes: Price makes a new intraday high but the 9-period RSI prints a lower high above 70, while volume contracts on the second push. That divergence—price up, momentum down, participation down—is a legitimate exhaustion signal. Short the break of the divergence candle's low, stop above the high, target VWAP.
Trend-Adjusted Thresholds: In strong trends, shift thresholds to 80/20 so you're not fighting momentum. In a genuine uptrend, RSI holding between 40 and 80 is normal and repeated 70+ readings are a sign of strength, not an automatic short signal.

Relative Volume (RVOL) — The Confirmation Layer

Relative volume above 2.0 signals unusual interest in a stock, and trades taken on stocks with RVOL above 2.0 produce 35% higher average profits than trades on average-volume stocks. RVOL is used by 65% of surveyed profitable traders.

What bots look for:
RVOL > 2.0: Unusual interest, breakout likely to sustain
Volume Confirmation on VWAP Breaks: A move above VWAP accompanied by rising volume points to bullish momentum. Weak volume usually means the move won't stick. Price moves on high volume are more likely to sustain. A breakout on 3x average volume is far more reliable than one on thin volume.
Volume Contraction on Pushes: If price makes a new high but volume contracts on the second push, the move is exhausting.

ATR — Volatility for Stop Placement

ATR (Average True Range) is used for position sizing and stop placement. 

What bots look for:
Stop Placement: Set stops at 1.5x or 2x ATR from entry to account for normal volatility
Position Sizing: Larger ATR = smaller position size to maintain consistent risk per trade
Volatility Regime Filter: Rising ATR = trending market; falling ATR = consolidation

MACD — Momentum Confirmation

MACD is used for momentum confirmation.

What bots look for:
MACD Line Cross Signal Line: Classic momentum shift signal
Histogram Expansion/Contraction: Growing histogram = momentum accelerating; shrinking = decelerating
Zero Line Cross: MACD moving above zero = bullish momentum; below zero = bearish

Advanced Signals Bots Test

Options Flow Overlay

When VWAP, EMAs, and RVOL align for a long setup and simultaneous call sweeps appear on the options tape, the confluence creates a multi-layered signal that chart indicators alone cannot produce. This is an eighth dimension that adds unique signal value.

Opening Range Breakout

Pre-market levels and the opening range (first 15-30 minutes) define the day's initial equilibrium.  Bots test breakouts above/below this range with volume confirmation.

Stochastic Oscillator — Faster Momentum

Stochastic is faster and more sensitive than RSI. It produces more signals but also more noise. Use it for short-term strategies where you need quicker entries. A bullish signal occurs when the faster %K line crosses above the slower %D line, particularly when both are below 20.

Anchored VWAP — Event-Based

Anchor VWAP from the open, a gap, or a swing high/low. Trade reactions at the anchored line as moving support/resistance with clear entry and exit rules. This is different from standard VWAP because it doesn't reset daily—it tracks fair value from a specific event.

How Bots Combine These Signals (The Confluence Model)

The key insight from the research is that no single indicator works standalone. Bots test confluence:

Step 1 — VWAP Direction: Is price above or below VWAP? This defines intraday bias.

Step 2 — Trend Alignment: Is SuperTrend/EMA aligned with VWAP direction?

Step 3 — Momentum Confirmation: Is RSI/MACD showing momentum in the same direction, not overextended?

Step 4 — Volume Confirmation: Is the RVOL above 1.5 on the setup bar?

All three layers pointing the same way = highest-quality setup.

What This Means for Your AI Terminal

For your project, your LLM shouldn't just look at one indicator. It should evaluate confluence. Your prompt to the LLM should include:

Current price vs VWAP (above/below, distance from VWAP)
VWAP slope (rising/falling/flat)
9 EMA and 20 EMA relationship (crossed, spreading, converging)
RSI value and whether it's diverging from price
RVOL (current volume vs average volume)
ATR (for stop distance suggestion)

Then ask the LLM: "Given these 6 data points, is there confluence for a long or short setup? What's the confidence level?"

The research shows that trades taken when all three layers (VWAP + trend + momentum) align with volume confirmation produce significantly better results than trades taken on any single indicator signal. 

One thing the search results don't cover well: intraday timeframes. Most of these indicators are tested on 1-minute, 5-minute, or 15-minute charts for day trading. What timeframe are you planning to have your LLM analyze—1-minute bars, 5-minute, or daily? This matters because VWAP behavior and signal frequency change dramatically across timeframes.


How Trading Bots Pick Stocks: The Screening Phase

This is the question most retail traders never ask. They focus entirely on entry/exit signals and ignore the screening layer that determines which stocks get analyzed in the first place. The search results reveal a multi-stage pipeline that professionals use.

Stage 1: Fundamental Screening (The Universe Filter)

Before any technical analysis happens, bots define a tradable universe using fundamental criteria:

EPS (Earnings Per Share): Filter for profitable companies
Market Cap: Exclude micro-caps that are easily manipulated
Sector: Focus on sectors that match the strategy (e.g., tech for momentum, utilities for mean reversion)
Valuation Metrics: P/E, P/B, EV/EBITDA ranges

This is user-defined and tailored to each trader's specific strategy or risk appetite. Your LLM terminal should start here. For your seasonal/mean-reversion strategy, you'd screen for:
Mid-to-large cap stocks (market cap > $2B)
Positive EPS (profitable companies)
Specific sectors (energy, consumer discretionary, agriculture)
Stocks with historical seasonal patterns

Stage 2: Liquidity and Volatility Filters

This is where most stocks get eliminated. Based on the criteria of liquidity and volatility, a few specific sectors dominate the attention of AI models.

Liquidity Requirements:
Average daily volume > 5-10 million shares
Tight bid-ask spreads (< 0.05%)
Stocks that allow high-frequency trading bots to scalp pennies all day long without ever running out of buyers or sellers

Volatility Requirements:
Average daily range > 2-3%
Beta > 1.2 (moves more than the market)
If the S&P 500 goes up 1%, a high-beta stock might go up 3%, offering three times the profit potential for the algorithm

Sector Concentration:
Technology and semiconductor sectors are the undisputed kings of volume
Nvidia (NVDA) is a prime example of an "algo-favorite" averaging over 150 million shares traded daily in early 2025

Stage 3: Historical Signal Correlation

This is the key differentiator. Stocks that habitually respond to technical breakouts or mean-reversion signals with repeatable patterns form the backbone of successful algorithmic strategies.

The bot doesn't just pick any liquid stock. It picks stocks that have historically responded well to its specific strategy. This means:

Backtest every stock against your strategy (e.g., RSI bounce, VWAP cross)
Rank stocks by historical win rate when your specific signals fire
Exclude stocks with <55% historical win rate on your signals
Weight toward stocks with predictable, repeatable patterns

For your project, this is critical. Your LLM should maintain a database of which stocks have historically responded well to seasonal/mean-reversion signals. Amazon in October works because it has a proven historical correlation with that seasonal pattern.

Stage 4: Predictive Momentum and EOD Modeling

More sophisticated systems use next-day probabilities driven by AI. This involves:

End-of-day modeling that predicts next-day direction
Pattern recognition on daily charts before the market opens
Pre-market gap analysis
Stocks showing proven, consistent alignment with predictability

Stage 5: Regime Detection (Market Environment Filter)

Before selecting individual stocks, the bot determines the overall market regime:

Trending market: Favor breakout strategies, high-beta stocks
Range-bound market: Favor mean-reversion strategies, lower-beta stocks
High volatility regime: Reduce position sizes, favor mean reversion
Low volatility regime: Increase position sizes, favor momentum

This is a filter that determines which strategy to apply, which then determines which stocks to screen.

Stage 6: The Modern AI Layer — Conviction Scoring

This is where your LLM terminal becomes powerful. Modern AI trading systems use large language models to evaluate each candidate with contextual reasoning.

The pipeline works like this:
Quantitative screening produces a list of candidates (e.g., 200 stocks pass liquidity/volatility filters)
Strategy algorithms run on each candidate (e.g., 16+ strategies including Breakout, Gap and Go, Opening Range Breakout, RSI Bounce)
AI conviction scoring: For each candidate that passes screening and strategy evaluation, a single AI call generates a conviction score from 0 to 100
Only high-conviction candidates (e.g., score > 75) proceed to execution

Stage 7: News and Sentiment Overlay

AI-enhanced systems analyze sentiment and impact of news across thousands of sources simultaneously, incorporating elements of fundamental analysis to assess the potential impact on stock prices.

This includes:
Detecting subtle language changes in central bank communications that might signal policy shifts
Measuring market sentiment across social platforms to gauge retail investor behavior
Filtering out stocks with impending negative catalysts (earnings misses, regulatory actions)

The Complete Selection Pipeline

Here's how this maps to your AI terminal:

What This Means for Your Project

Your LLM terminal needs a screening layer before the signal layer. Here's the architecture:

Weekly: Run fundamental screen (FMP API, SEC EDGAR) → update tradable universe
Daily pre-market: Run liquidity/volatility filter (yfinance) → narrow to 50-100 candidates
Daily pre-market: Run regime detection (FRED data, VIX, Treasury yields) → determine strategy mode
Daily pre-market: Query vector DB for historical signal correlation → rank candidates
Intraday: Run technical signals (VWAP, RSI, EMA) on top candidates only
Intraday: LLM conviction scoring on any stock that produces a technical signal
Intraday: Execute only highest-conviction trades in paper account

The mistake most retail traders make is running technical indicators on every stock and hoping something triggers. Professionals narrow to 20-50 candidates first, then apply signals only to those.

What's your current approach to stock selection? Are you manually picking the handful of stocks you trade (AMZN, Centrica, fertilizer, airlines), or do you want the system to discover candidates automatically? This determines whether you need a full screening pipeline or just a signal engine on a fixed watchlist.


