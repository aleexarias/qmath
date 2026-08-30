"""Filtering and data quality checks for option chains."""

from qmath.options.chain import OptionChain

__all__ = ["filter_chain"]


def filter_chain(
    chain: OptionChain,
    min_spread: float = 0.01,
    max_bid_ask_ratio: float = 1.1,
    min_bid: float = 0.0,
) -> OptionChain:
    r"""Filter an option chain to remove low-liquidity and stale quotes.

    Parameters
    ----------
    chain : OptionChain
        Raw option chain.
    min_spread : float, default=0.01
        Minimum spread (in dollars) to keep a quote.
    max_bid_ask_ratio : float, default=1.1
        Maximum ask/bid ratio; filters wide spreads.
    min_bid : float, default=0.0
        Minimum bid to keep a quote.

    Returns
    -------
    OptionChain
        Filtered chain with a subset of strikes.

    Notes
    -----
    Removes strikes where:
    - bid < min_bid (zero or stale bids)
    - ask/bid > max_bid_ask_ratio (too wide)
    - ask - bid < min_spread (too tight, possibly arb)
    """
    mask = (
        (chain.bid >= min_bid)
        & (chain.ask / chain.bid <= max_bid_ask_ratio)
        & (chain.spread >= min_spread)
    )

    return OptionChain(
        strikes=chain.strikes[mask],
        bid=chain.bid[mask],
        ask=chain.ask[mask],
        T=chain.T,
        spot=chain.spot,
        rate=chain.rate,
        dividend_yield=chain.dividend_yield,
        true_density=chain.true_density[mask] if chain.true_density is not None else None,
    )
