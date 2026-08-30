"""Deribit API loader for live option data.

Fetches real option chains from Deribit's public API. Requires internet connection
but no authentication for public data.

**Note**: Deribit is a cryptocurrency (Bitcoin/Ethereum) options exchange. For
traditional equity options, use other data providers.
"""

import warnings
from typing import Any

import numpy as np

from qmath._typing import FloatArray
from qmath.options.chain import OptionChain

__all__ = ["load_deribit_chain"]


def load_deribit_chain(
    currency: str = "BTC",
    kind: str = "call",
    maturity_days: int = 7,
) -> OptionChain:
    r"""Fetch option chain from Deribit API.

    Parameters
    ----------
    currency : str, default='BTC'
        Cryptocurrency ('BTC' or 'ETH').
    kind : str, default='call'
        Option type ('call' or 'put').
    maturity_days : int, default=7
        Days to expiration (Deribit uses fixed maturities: 7, 30, 90, 180).

    Returns
    -------
    OptionChain
        Snapshot of live option chain from Deribit.

    Raises
    ------
    ImportError
        If requests library is not installed.
    RuntimeError
        If API request fails or no data available.

    Notes
    -----
    This requires an internet connection and makes a live API call. Deribit
    provides Bitcoin and Ethereum options with high liquidity and tight spreads,
    making it ideal for research into cryptocurrency volatility surfaces.

    **Warning**: Cryptocurrency markets are 24/7 and highly volatile. Use for
    research only; production systems should cache and validate.
    """
    try:
        import requests  # type: ignore[import-untyped]
    except ImportError as e:
        msg = "requests library required for Deribit API access. Install with: pip install requests"
        raise ImportError(msg) from e

    api_url = "https://www.deribit.com/api/v2"

    # Get current spot price
    try:
        resp = requests.get(f"{api_url}/public/ticker", params={"instrument_name": f"{currency}_USDT"}, timeout=5)
        resp.raise_for_status()
        spot: float = resp.json()["result"]["last_price"]
    except Exception as e:
        msg = f"Failed to fetch {currency} spot price: {e}"
        raise RuntimeError(msg) from e

    # Get option chain
    try:
        resp = requests.get(
            f"{api_url}/public/get_book_summary_by_currency",
            params={"currency": currency, "kind": kind},
            timeout=5,
        )
        resp.raise_for_status()
        options: list[dict[str, Any]] = resp.json()["result"]
    except Exception as e:
        msg = f"Failed to fetch {currency} {kind} options: {e}"
        raise RuntimeError(msg) from e

    # Filter by maturity
    options_by_maturity: dict[int, list[dict[str, Any]]] = {}
    for opt in options:
        exp_ts: int = opt["expiration_timestamp"]

        if exp_ts not in options_by_maturity:
            options_by_maturity[exp_ts] = []

        options_by_maturity[exp_ts].append(opt)

    if not options_by_maturity:
        msg = f"No {kind} options found for {currency}"
        raise RuntimeError(msg)

    # Pick maturity closest to target
    selected_maturity: int = min(
        options_by_maturity.keys(), key=lambda x: abs(x - (options[0]["creation_timestamp"] + maturity_days * 86400))
    )
    chain_data = options_by_maturity[selected_maturity]

    # Extract strikes and prices
    strikes_list: list[float] = []
    bids_list: list[float] = []
    asks_list: list[float] = []

    for opt in chain_data:
        strike: float = opt["strike"]
        bid: float | None = opt.get("bid_price", None)
        ask: float | None = opt.get("ask_price", None)

        if bid is not None and ask is not None and bid > 0 and ask > 0:
            strikes_list.append(strike)
            bids_list.append(bid)
            asks_list.append(ask)

    if not strikes_list:
        msg = f"No valid {kind} quotes found"
        raise RuntimeError(msg)

    # Sort by strike and create arrays
    sorted_indices = np.argsort(strikes_list)
    strikes: FloatArray = np.array([strikes_list[i] for i in sorted_indices], dtype=np.float64)
    bid_array: FloatArray = np.array([bids_list[i] for i in sorted_indices], dtype=np.float64)
    ask_array: FloatArray = np.array([asks_list[i] for i in sorted_indices], dtype=np.float64)

    # Time to maturity
    current_ts: int = options[0]["creation_timestamp"]
    T: float = (selected_maturity - current_ts) / 365.25 / 86400

    rate: float = 0.0

    warnings.warn(f"Fetched {len(strikes)} {kind} options from Deribit for {currency} expiring in {T:.2f} years")

    return OptionChain(
        strikes=strikes,
        bid=bid_array,
        ask=ask_array,
        T=T,
        spot=spot,
        rate=rate,
    )
