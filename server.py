"""Minimal MCP server for the Buy-or-Wait Decision app.

This implementation uses Python's standard library only.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from decision_logic import make_buy_or_wait_decision

TOOL_NAME = "buy_or_wait_decision"
TOOL_TITLE = "Buy or Wait Decision"
TOOL_DESCRIPTION = (
    "Use this when the user wants help deciding whether to buy a product now "
    "or wait for a better time to get a better price or value."
)


def build_tool_definition() -> dict[str, Any]:
    return {
        "name": TOOL_NAME,
        "title": TOOL_TITLE,
        "description": TOOL_DESCRIPTION,
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "current_price": {"type": "number"},
                "urgency_level": {"type": "string"},
                "expected_wait_window": {"type": "string"},
            },
            "required": [
                "product_name",
                "current_price",
                "urgency_level",
                "expected_wait_window",
            ],
            "additionalProperties": False,
        },
    }


class MCPHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _jsonrpc_success(self, request_id: Any, result: dict[str, Any]) -> None:
        self._send_json(200, {"jsonrpc": "2.0", "id": request_id, "result": result})

    def _jsonrpc_error(self, request_id: Any, code: int, message: str) -> None:
        self._send_json(
            200,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": code,
                    "message": message,
                },
            },
        )

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        if self.path != "/mcp":
            self._send_json(404, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            request = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if request.get("jsonrpc") != "2.0":
            self._jsonrpc_error(request_id, -32600, "Invalid Request: jsonrpc must be '2.0'")
            return

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "buy-or-wait-decision", "version": "0.1.0"},
            }
            self._jsonrpc_success(request_id, result)
            return

        if method == "tools/list":
            self._jsonrpc_success(request_id, {"tools": [build_tool_definition()]})
            return

        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name != TOOL_NAME:
                self._jsonrpc_error(request_id, -32602, f"Unknown tool: {tool_name}")
                return

            required_keys = {
                "product_name",
                "current_price",
                "urgency_level",
                "expected_wait_window",
            }
            if not isinstance(arguments, dict) or not required_keys.issubset(arguments.keys()):
                self._jsonrpc_error(
                    request_id,
                    -32602,
                    "Invalid arguments: product_name, current_price, urgency_level, expected_wait_window are required.",
                )
                return

            decision = make_buy_or_wait_decision(
                product_name=arguments["product_name"],
                current_price=arguments["current_price"],
                urgency_level=arguments["urgency_level"],
                expected_wait_window=arguments["expected_wait_window"],
            )
            self._jsonrpc_success(request_id, {"structuredContent": decision})
            return

        self._jsonrpc_error(request_id, -32601, f"Method not found: {method}")


def run() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    server = HTTPServer((host, port), MCPHandler)
    print(f"MCP server running on http://{host}:{port}")
    print("MCP endpoint: POST /mcp")
    print("Health endpoint: GET /health")
    server.serve_forever()


if __name__ == "__main__":
    run()
