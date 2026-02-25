# Indian Financial News — Data Sources

Document the free data sources used by the news-sentiment-mcp server.

**RSS Feeds (Primary)**
- Google News RSS: `https://news.google.com/rss/search?q={query}+stock+NSE&hl=en-IN&gl=IN`
- Economic Times Markets RSS: `https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms`
- Economic Times Companies RSS: various category feeds

**NSE Public APIs (No auth required)**
- FII/DII Activity: `https://www.nseindia.com/api/fiidiiActivity`
- Corporate Actions: `https://www.nseindia.com/api/corporates-corporateActions`
- All Indices (VIX, Sectors): `https://www.nseindia.com/api/allIndices`
- Note: NSE APIs require proper User-Agent header and may need cookies

**Data Limitations**
- Google News: Rate-limited, may return cached results
- NSE APIs: Sometimes return partial data, need fallback handling
- No paid API keys needed — all sources are free
- RSS feeds don't include sentiment scores — agent must interpret headlines

**Source Reliability**
- NSE/BSE official data: Highest reliability
- Major dailies (ET, Mint, BS): High reliability
- Google News aggregation: Medium (includes noise)
- Social media: Low reliability, not used by default
