# Trading Agent v1

Multi-agent AI trading system for Indian stocks (Nifty 50) using Claude Code Agent Teams.

## Architecture

```
Claude Code (Team Lead - Opus)
├── Screener Agent (Sonnet) → Technical analysis on Nifty 50
├── Analyst Agent (Sonnet)  → News sentiment + red flag detection
└── Executor Agent (Sonnet) → Risk validation + order execution
```

**Three MCP Servers:**
- `angel-one-mcp` — Angel One SmartAPI (market data + orders)
- `portfolio-db-mcp` — SQLite portfolio + trade journal + risk enforcement
- `news-sentiment-mcp` — RSS news feeds + NSE data (FII/DII, VIX, sectors)

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure credentials
```bash
cp .mcp.json.example .mcp.json
# Edit .mcp.json and fill in your Angel One credentials:
# - ANGEL_API_KEY
# - ANGEL_CLIENT_ID
# - ANGEL_PIN
# - ANGEL_TOTP_SECRET
```

### 3. Verify servers
```bash
python test_servers.py
```

### 4. Start Claude Code
```bash
claude
```

### 5. Initialize
```
> Initialize the portfolio database, then log in to Angel One.
```

### 6. Begin trading
```
> Run a trading cycle: scan Nifty 50, analyze flagged stocks, execute if approved.
```

## Safety (Defense in Depth)

Risk rules are enforced in **Python code** inside the MCP servers, not in prompts:

| Rule | Limit | Enforced In |
|------|-------|-------------|
| Market hours | 9:30-15:15 IST | angel-one-mcp |
| Max per stock | 10% of capital | angel-one-mcp + portfolio-db-mcp |
| Max positions | 5 open | portfolio-db-mcp |
| Stop-loss required | 3-5% from entry | angel-one-mcp |
| Daily loss limit | 2% of capital | portfolio-db-mcp |
| No duplicates | 1 position per stock | portfolio-db-mcp |

The LLM cannot bypass these regardless of prompt injection or hallucination.

## Paper Trading

This system uses ₹1,00,000 simulated capital. No real money is at risk. The `place_order` tool calls Angel One's real API — use paper trading mode or test with minimal quantities.

## Files

```
trading-agent/
├── .claude/settings.json     # Agent teams enabled
├── .mcp.json                 # MCP config (gitignored - has credentials)
├── .mcp.json.example         # Template (safe to commit)
├── CLAUDE.md                 # Claude Code instructions
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── test_servers.py           # Server verification
├── mcp-servers/
│   ├── shared/__init__.py    # Config, constants, risk limits
│   ├── angel-one-mcp/server.py
│   ├── portfolio-db-mcp/server.py
│   └── news-sentiment-mcp/server.py
└── data/                     # SQLite databases (auto-created)
```
