"""
Quick test to verify MCP server imports and tool registration.
Run: python test_servers.py
"""

import sys
import os

# Set project root
os.environ["TRADING_PROJECT_ROOT"] = os.path.dirname(os.path.abspath(__file__))

# Add mcp-servers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp-servers"))

def test_shared_config():
    """Test shared configuration loads correctly."""
    from shared import (
        STARTING_CAPITAL, MAX_POSITION_PCT, MAX_OPEN_POSITIONS,
        DAILY_LOSS_LIMIT_PCT, DEFAULT_STOP_LOSS_PCT, is_market_active, now_ist,
    )
    print("[OK] Shared config loaded")
    print(f"  Capital: Rs.{STARTING_CAPITAL:,.0f}")
    print(f"  Max position: {MAX_POSITION_PCT:.0%}")
    print(f"  Max positions: {MAX_OPEN_POSITIONS}")
    print(f"  Daily loss limit: {DAILY_LOSS_LIMIT_PCT:.0%}")
    print(f"  Default SL: {DEFAULT_STOP_LOSS_PCT:.0%}")
    print(f"  Current IST: {now_ist().isoformat()}")
    print(f"  Market active: {is_market_active()}")
    print()


def test_server_imports():
    """Test each server can import and list its tools."""
    servers = [
        ("angel-one-mcp", "mcp-servers/angel-one-mcp/server.py"),
        ("portfolio-db-mcp", "mcp-servers/portfolio-db-mcp/server.py"),
        ("news-sentiment-mcp", "mcp-servers/news-sentiment-mcp/server.py"),
    ]

    for name, path in servers:
        try:
            # Import the module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                name.replace("-", "_"),
                os.path.join(os.path.dirname(__file__), path),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the FastMCP instance
            mcp_instance = module.mcp

            # List registered tools
            # FastMCP stores tools internally
            print(f"[OK] {name} loaded successfully")
            print(f"  Server name: {mcp_instance.name}")

            # Try to get tool list
            if hasattr(mcp_instance, '_tool_manager'):
                tools = mcp_instance._tool_manager._tools
                for tool_name in tools:
                    print(f"    • {tool_name}")
            elif hasattr(mcp_instance, '_tools'):
                for tool_name in mcp_instance._tools:
                    print(f"    • {tool_name}")
            else:
                print("  (tools registered but cannot enumerate outside server context)")
            print()

        except ImportError as e:
            print(f"[FAIL] {name} - import error: {e}")
            print(f"  Install missing package: pip install {str(e).split("'")[1] if "'" in str(e) else '???'}")
            print()
        except Exception as e:
            print(f"[FAIL] {name} - error: {e}")
            print()


def test_db_init():
    """Test portfolio database initialization."""
    from shared import DB_PATH
    print(f"Database path: {DB_PATH}")

    # Don't actually create it in test - just verify path is valid
    db_dir = os.path.dirname(DB_PATH)
    if os.path.exists(db_dir):
        print(f"[OK] Data directory exists: {db_dir}")
    else:
        print(f"  Data directory will be created on first run: {db_dir}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Trading Agent v1 - Server Verification")
    print("=" * 50)
    print()

    test_shared_config()
    test_db_init()
    test_server_imports()

    print("=" * 50)
    print("Done. If all checks pass, run: claude")
    print("Then: initialize_portfolio, login_session")
    print("=" * 50)
