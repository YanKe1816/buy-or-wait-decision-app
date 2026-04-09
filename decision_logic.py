"""Core decision logic for the Buy-or-Wait Decision MCP tool."""

from __future__ import annotations

import re
from typing import Any


MEANINGFUL_WAIT_KEYWORDS = {
    "black friday",
    "cyber monday",
    "prime day",
    "holiday",
    "clearance",
    "end of season",
    "next model",
}



def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())



def _parse_wait_days(expected_wait_window: str) -> int:
    """Convert wait text to an estimated number of days.

    Simple deterministic parser that supports common units.
    """
    text = _normalize_text(expected_wait_window)

    number_match = re.search(r"(\d+(?:\.\d+)?)", text)
    amount = float(number_match.group(1)) if number_match else 0.0

    if "day" in text:
        return int(amount)
    if "week" in text:
        return int(amount * 7)
    if "month" in text:
        return int(amount * 30)
    if "year" in text:
        return int(amount * 365)

    if any(keyword in text for keyword in MEANINGFUL_WAIT_KEYWORDS):
        return 30

    return 0



def make_buy_or_wait_decision(
    product_name: str,
    current_price: Any,
    urgency_level: str,
    expected_wait_window: str,
) -> dict[str, str]:
    """Return a deterministic buy-or-wait recommendation."""
    normalized_urgency = _normalize_text(urgency_level)

    try:
        price = float(current_price)
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
    except (TypeError, ValueError):
        return {
            "decision": "wait",
            "reason": "The current price is missing or invalid, so a safe fallback is to wait and verify the price first.",
            "wait_window": "Recheck within 7 days",
            "estimated_savings": "Unknown until a valid price is provided",
            "special_condition": "Provide a valid positive current_price for a stronger recommendation.",
        }

    wait_days = _parse_wait_days(expected_wait_window)

    if normalized_urgency == "high":
        return {
            "decision": "buy",
            "reason": "Urgency is high, so immediate utility outweighs potential future savings.",
            "wait_window": "No wait recommended",
            "estimated_savings": "$0 to minimal",
            "special_condition": f"Buy now if {product_name} is needed immediately.",
        }

    if wait_days >= 14:
        estimated_savings_value = max(price * 0.10, 5.0)
        return {
            "decision": "wait",
            "reason": f"The expected wait window ({expected_wait_window}) is meaningful and may unlock better deals.",
            "wait_window": expected_wait_window,
            "estimated_savings": f"~${estimated_savings_value:.2f} (rule-of-thumb estimate)",
            "special_condition": "Set a price alert and buy only if the price drops or urgency increases.",
        }

    return {
        "decision": "buy",
        "reason": "Urgency is not high, but the wait window is short and unlikely to produce strong value improvement.",
        "wait_window": "Optional short wait: up to 7 days",
        "estimated_savings": "Likely low (<5%)",
        "special_condition": "If a known sale event is near, reassess then.",
    }
