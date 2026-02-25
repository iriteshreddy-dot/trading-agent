# Nifty 50 — Angel One Symbol Mapping

Last updated: February 2026

These are the Nifty 50 constituent stocks with their Angel One SmartAPI symbol tokens. The format is `{tradingsymbol: symboltoken}` as returned by the `get_nifty50_symbols()` tool. All symbols use the `-EQ` suffix indicating equity segment on NSE.

| Symbol | Angel One Token |
|--------|----------------|
| ADANIENT-EQ | 25 |
| ADANIPORTS-EQ | 15083 |
| APOLLOHOSP-EQ | 157 |
| ASIANPAINT-EQ | 236 |
| AXISBANK-EQ | 5900 |
| BAJAJ-AUTO-EQ | 16669 |
| BAJFINANCE-EQ | 317 |
| BAJAJFINSV-EQ | 16675 |
| BEL-EQ | 383 |
| BPCL-EQ | 526 |
| BHARTIARTL-EQ | 10604 |
| BRITANNIA-EQ | 547 |
| CIPLA-EQ | 694 |
| COALINDIA-EQ | 20374 |
| DRREDDY-EQ | 881 |
| EICHERMOT-EQ | 910 |
| GRASIM-EQ | 1232 |
| HCLTECH-EQ | 7229 |
| HDFCBANK-EQ | 1333 |
| HDFCLIFE-EQ | 467 |
| HEROMOTOCO-EQ | 1348 |
| HINDALCO-EQ | 1363 |
| HINDUNILVR-EQ | 1394 |
| ICICIBANK-EQ | 4963 |
| ITC-EQ | 1660 |
| INDUSINDBK-EQ | 5258 |
| INFY-EQ | 1594 |
| JSWSTEEL-EQ | 11723 |
| KOTAKBANK-EQ | 1922 |
| LT-EQ | 11483 |
| M&M-EQ | 2031 |
| MARUTI-EQ | 10999 |
| NTPC-EQ | 11630 |
| NESTLEIND-EQ | 17963 |
| ONGC-EQ | 2475 |
| POWERGRID-EQ | 14977 |
| RELIANCE-EQ | 2885 |
| SBILIFE-EQ | 21808 |
| SHRIRAMFIN-EQ | 4306 |
| SBIN-EQ | 3045 |
| SUNPHARMA-EQ | 3351 |
| TCS-EQ | 11536 |
| TATACONSUM-EQ | 3432 |
| TATAMOTORS-EQ | 3456 |
| TATASTEEL-EQ | 3499 |
| TECHM-EQ | 13538 |
| TITAN-EQ | 3506 |
| ULTRACEMCO-EQ | 11532 |
| WIPRO-EQ | 3787 |

## Notes

- This list reflects the current Nifty 50 constituents. The index is rebalanced semi-annually by NSE, so symbols may change.
- To get the latest mapping at runtime, call the `get_nifty50_symbols()` tool from the angel-one-mcp server.
- The token numbers are stable identifiers used by Angel One for API calls such as `get_live_quote` and `get_historical_candles`.
