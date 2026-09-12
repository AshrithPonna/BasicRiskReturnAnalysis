"""Compare the risk and return of one or more stocks."""

from __future__ import annotations

import argparse # Making sure that stock tickers can be read.
from dataclasses import dataclass # Data classification for stock metrics.
from datetime import datetime, timedelta # Year history of data. 
from pathlib import Path # Chart saving locality. 

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import tstd


TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.02
OUTPUT_FILE = Path("risk_return_scatter.png")


@dataclass
class StockMetrics:
    """The metrics calculated for one ticker."""

    ticker: str
    annual_return: float
    daily_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    maximum_drawdown: float
    is_efficient: bool = False


def download_prices(ticker: str) -> pd.Series:
    """Download one year of adjusted closing prices for a ticker."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
    )
    if data.empty:
        raise ValueError(f"No price data was returned for {ticker}.")

    # yfinance can return a MultiIndex even for one requested ticker.
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"].iloc[:, 0]
    else:
        prices = data["Close"]
    prices = prices.dropna()
    if len(prices) < 2:
        raise ValueError(f"Not enough price data was returned for {ticker}.")
    return prices


def calculate_metrics(ticker: str, prices: pd.Series) -> StockMetrics:
    """Calculate return, risk-adjusted ratios, and drawdown."""
    daily_returns = prices.pct_change().dropna()
    annual_return = daily_returns.mean() * TRADING_DAYS_PER_YEAR
    daily_volatility = daily_returns.std()

    # Annualize volatility so the Sharpe numerator and denominator share a time
    # scale, even though the summary table reports daily volatility.
    annualized_volatility = daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR)
    sharpe_ratio = (annual_return - RISK_FREE_RATE) / annualized_volatility

    # Sortino penalizes returns below the daily risk-free hurdle only.
    daily_risk_free_rate = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR
    downside_returns = daily_returns[daily_returns < daily_risk_free_rate] - daily_risk_free_rate
    downside_deviation = tstd(downside_returns, ddof=1) if len(downside_returns) > 1 else 0.0
    annualized_downside_deviation = downside_deviation * np.sqrt(TRADING_DAYS_PER_YEAR)
    sortino_ratio = (
        (annual_return - RISK_FREE_RATE) / annualized_downside_deviation
        if annualized_downside_deviation > 0
        else np.nan
    )

    # Compare each price with the highest price seen before it.
    running_peak = prices.cummax()
    maximum_drawdown = (prices / running_peak - 1).min()

    return StockMetrics(
        ticker=ticker,
        annual_return=annual_return,
        daily_volatility=daily_volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        maximum_drawdown=maximum_drawdown,
    )


def mark_efficient_stocks(metrics: list[StockMetrics]) -> None:
    """Mark stocks not dominated by another stock's return and volatility."""
    for candidate in metrics:
        candidate.is_efficient = not any(
            other is not candidate
            and other.annual_return >= candidate.annual_return
            and other.daily_volatility <= candidate.daily_volatility
            and (
                other.annual_return > candidate.annual_return
                or other.daily_volatility < candidate.daily_volatility
            )
            for other in metrics
        )


def print_summary(metrics: list[StockMetrics]) -> None:
    """Print a table ranked by Sharpe ratio."""
    ranked = sorted(metrics, key=lambda item: item.sharpe_ratio, reverse=True)
    rows = [
        {
            "Rank": rank,
            "Ticker": item.ticker,
            "Annual Return": f"{item.annual_return:.2%}",
            "Daily Risk": f"{item.daily_volatility:.2%}",
            "Sharpe": f"{item.sharpe_ratio:.2f}",
            "Sortino": f"{item.sortino_ratio:.2f}",
            "Max Drawdown": f"{item.maximum_drawdown:.2%}",
            "Efficient": "Yes" if item.is_efficient else "No",
        }
        for rank, item in enumerate(ranked, start=1)
    ]
    print(pd.DataFrame(rows).to_string(index=False))


def create_plot(metrics: list[StockMetrics], output_file: Path) -> None:
    """Save the risk-return scatter plot."""
    efficient = [item for item in metrics if item.is_efficient]
    other = [item for item in metrics if not item.is_efficient]
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.scatter(
        [item.daily_volatility for item in other],
        [item.annual_return for item in other],
        color="steelblue",
        s=100,
        label="Other stocks",
    )
    axis.scatter(
        [item.daily_volatility for item in efficient],
        [item.annual_return for item in efficient],
        color="darkorange",
        edgecolor="black",
        s=140,
        label="Efficient stocks",
        zorder=3,
    )
    for item in metrics:
        axis.annotate(item.ticker, (item.daily_volatility, item.annual_return), xytext=(6, 6), textcoords="offset points")

    # The risk-free asset would sit at zero volatility and a 2% annual return.
    axis.axhline(RISK_FREE_RATE, color="firebrick", linestyle="--", label="2% risk-free return")
    axis.set_title("Risk vs. Return")
    axis.set_xlabel("Daily volatility (standard deviation)")
    axis.set_ylabel("Expected annual return")
    axis.xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.1%}"))
    axis.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.1%}"))
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_file, dpi=150)
    plt.close(figure)


def parse_arguments() -> argparse.Namespace:
    """Read ticker symbols from the command line."""
    parser = argparse.ArgumentParser(description="Analyze stock risk and return.")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols, such as AAPL MSFT")
    return parser.parse_args()


def main() -> None:
    """Download data, calculate metrics, print results, and save the chart."""
    arguments = parse_arguments()
    metrics: list[StockMetrics] = []
    for raw_ticker in arguments.tickers:
        ticker = raw_ticker.upper()
        try:
            metrics.append(calculate_metrics(ticker, download_prices(ticker)))
        except (ValueError, KeyError) as error:
            print(f"Skipping {ticker}: {error}")
    if not metrics:
        raise SystemExit("No valid ticker data was found.")
    mark_efficient_stocks(metrics)
    print_summary(metrics)
    create_plot(metrics, OUTPUT_FILE)
    print(f"\nSaved visualization to {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()