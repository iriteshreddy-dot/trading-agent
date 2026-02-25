# Indian Market Context — NSE/BSE Trading Nuances

## Circuit Limits

NSE stocks have 5%/10%/20% daily circuit filters depending on category. Upper circuit = can't buy (no sellers), lower circuit = can't sell (no buyers). Nifty 50 stocks typically have 20% circuits.

- If a stock hits upper circuit, avoid placing buy orders — they won't get filled.
- If a stock hits lower circuit, stop-loss orders won't execute — risk of larger losses.
- Circuit limits reset daily based on previous day's closing price.

## Options Expiry (Thursday)

Weekly Nifty/Bank Nifty expiry causes unusual volume and price action. Reduce signal confidence by 20% on expiry days. Monthly expiry (last Thursday) has even more impact.

- Max pain theory: Price tends to gravitate toward the strike with maximum open interest.
- Increased volatility between 2:00-3:30 PM on expiry days.
- Avoid initiating new positions in the last hour on expiry Thursdays.

## FII/DII Flows

Foreign Institutional Investors and Domestic Institutional Investors. FII selling > Rs.2000 Cr = bearish pressure. FII buying > Rs.2000 Cr = bullish. DII often provides counter-flow. Check via get_fii_dii_data() tool.

- Sustained FII selling over multiple days = stronger bearish signal than single-day selling.
- When FII and DII both sell = very bearish (rare but significant).
- FII flows in derivatives (futures OI) can signal short-term direction.

## Sector Rotation

When FIIs rotate between sectors (e.g., IT to Banking), individual stock technicals may be misleading. Always check sector_performance.

- Money flowing out of defensive sectors (FMCG, Pharma) into cyclicals (Banking, Auto) = risk-on sentiment.
- Money flowing into defensives = risk-off sentiment.
- A stock may show bullish technicals but underperform if its sector is out of favor.

## T+1 Settlement

India uses T+1 settlement. Shares delivered next business day. Affects capital availability for next trade.

- If you sell on Day 1, funds are available on Day 2.
- Intraday trades settle same day (no delivery involved).
- Plan position sizing with settlement in mind — capital may be locked for a day.

## Pre-open Session (9:00-9:15 IST)

Price discovery auction. Gap-up/gap-down determined here. Don't trade based on pre-open prices.

- 9:00-9:08: Order entry, modification, cancellation allowed.
- 9:08-9:12: Order matching, price discovery.
- 9:12-9:15: Buffer period, transition to normal trading.
- The equilibrium price from pre-open becomes the opening price.
- Large gaps (>1%) in pre-open warrant caution — wait for first 15 minutes of regular session.

## High-Volatility Events

Budget Day, RBI Policy Days: High volatility events. Reduce position sizes or avoid new entries.

Key dates to watch:
- **Union Budget**: Usually February 1. Can cause 2-5% swings in index.
- **RBI Monetary Policy**: Bi-monthly (Feb, Apr, Jun, Aug, Oct, Dec). Rate decisions move banking stocks significantly.
- **US Fed decisions**: Impact FII flows and IT sector stocks.
- **Quarterly earnings season**: Jan-Feb, Apr-May, Jul-Aug, Oct-Nov. Individual stock volatility spikes around results.

Strategy adjustments:
- Reduce position sizes to 50% on event days.
- Widen stop-losses by 1-2% to avoid noise-triggered exits.
- Avoid new entries 30 minutes before and after major announcements.
