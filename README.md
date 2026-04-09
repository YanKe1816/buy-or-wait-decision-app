# Buy-or-Wait Decision (MCP Server)

A minimal Python MCP server that provides one tool:

- **Tool name:** `buy_or_wait_decision`
- **Tool title:** Buy or Wait Decision
- **Tool description:** Use this when the user wants help deciding whether to buy a product now or wait for a better time to get a better price or value.

## What is implemented

- One MCP endpoint: `POST /mcp`
- One MCP tool: `buy_or_wait_decision`
- One health endpoint: `GET /health`
- Deterministic, explicit decision rules
- No UI, no auth, no database, no external APIs

## Project structure

```text
.
├── decision_logic.py
├── server.py
├── requirements.txt
└── README.md
```

## Local run instructions

1. (Optional) create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. (Optional) install requirements (none required):

```bash
pip install -r requirements.txt
```

3. Run the MCP server:

```bash
python server.py
```

Server defaults:
- Host: `0.0.0.0`
- Port: `8000`

Override with environment variables:

```bash
HOST=127.0.0.1 PORT=9000 python server.py
```

## Tool contract

### Input fields

- `product_name` (string)
- `current_price` (number)
- `urgency_level` (string)
- `expected_wait_window` (string)

### Output fields

- `decision` (string)
- `reason` (string)
- `wait_window` (string)
- `estimated_savings` (string)
- `special_condition` (string)

## Prototype decision rules used

1. If `urgency_level` is exactly `"high"` (case-insensitive), recommend **buy**.
2. If `expected_wait_window` implies a meaningful wait (>= 14 days, or recognized sale/event keywords), recommend **wait**.
3. If `current_price` is missing/invalid/non-positive, return a safe fallback recommendation.
4. Otherwise recommend **buy**.

## Test steps

### 1) Health check

```bash
curl -s http://127.0.0.1:8000/health
```

Expected output:

```json
{"status": "ok"}
```

### 2) List tools (MCP)

```bash
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### 3) Call tool (example input + output)

Example input:

```json
{
  "name": "buy_or_wait_decision",
  "arguments": {
    "product_name": "Wireless Headphones",
    "current_price": 199.99,
    "urgency_level": "low",
    "expected_wait_window": "3 weeks"
  }
}
```

Example call:

```bash
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "buy_or_wait_decision",
      "arguments": {
        "product_name": "Wireless Headphones",
        "current_price": 199.99,
        "urgency_level": "low",
        "expected_wait_window": "3 weeks"
      }
    }
  }'
```

Example output:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "structuredContent": {
      "decision": "wait",
      "reason": "The expected wait window (3 weeks) is meaningful and may unlock better deals.",
      "wait_window": "3 weeks",
      "estimated_savings": "~$20.00 (rule-of-thumb estimate)",
      "special_condition": "Set a price alert and buy only if the price drops or urgency increases."
    }
  }
}
```
