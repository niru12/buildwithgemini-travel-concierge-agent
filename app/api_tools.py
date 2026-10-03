# Copyright 2026 Google LLC
# External Public API tools for Travel Concierge Agent

import os
import httpx


def get_currency_exchange_rates(base_currency: str = "USD", target_currencies: str = "EUR,JPY,GBP,CAD,AUD") -> dict:
    """Fetches real-time foreign currency exchange rates from the Frankfurter Public API.

    Args:
        base_currency: Three-letter ISO currency code to convert from (e.g., 'USD', 'EUR', 'GBP').
        target_currencies: Optional comma-separated list of target currency codes (e.g., 'EUR,JPY,GBP').

    Returns:
        A dictionary containing exchange rates, base currency, and date of rates.
    """
    base = base_currency.upper().strip()
    api_host = os.getenv("FRANKFURTER_API_URL", "https://api.frankfurter.app")
    url = f"{api_host}/latest?from={base}"

    if target_currencies:
        symbols = ",".join([s.strip().upper() for s in target_currencies.split(",") if s.strip()])
        if symbols:
            url += f"&to={symbols}"

    try:
        response = httpx.get(url, follow_redirects=True, timeout=10.0)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API request failed with status code {response.status_code}"}
    except Exception as e:
        return {"error": f"Failed to fetch real-time exchange rates: {e}"}
