"""Compare the risk and return of one or more stocks."""

from __future__ import annotations # Annotation syntax counter point. 

import argparse # Making sure that stock tickers can be read.
from dataclasses import dataclass # Data classification for stock metrics.
from datetime import datetime, timedelta # Year history of data. 
from pathlib import Path # Chart saving locality. 

import matplotlib.pyplot as plt # Plotting library.
import numpy as np # Numerical operations.
import pandas as pd # Data manipulation and analysis.
import yfinance as yf # Financial API.
from scipy.stats import tstd # Statistic evaluations. 

# I'm learning about Sortino ratio (investment returns/downside risk). ALL POSITIVES growths/metrics are IGNORED for this corrolary. 
# (Asset returns - target return) / downside deviation (deviation below target). 
# Negative volatility determination.

# I'm also learning about Sharpe ratio! - (Portfolio's risk-adjusted return).
# (Actual return - arbitrary beta (risk free rate))/ standard deviation (distance from general return).
# Excess return/standard deviation of standard deviation of all returns. 

TRADING_DAYS_PER_YEAR = 252 # NYSE standard trading max. 
RISK_FREE_RATE = 0.02 # Investment return (0% loss) - (NOT RELATED TO CURRENT MARKET //TODO)
OUTPUT_FILE = Path("risk_return_scatter.png") # File path for the scatter plot. 

# Class holding target values for Stock analysis. 

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

# Pulling adjusted historical prices from yfinance (mainly disregarding splits, dividends, etc.)

def download_prices(ticker: str) -> pd.Series:

    # End/start date built with delta integration to get a year of data.
   
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    #yfinance API information pulled, based on initial parameters. 

    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
    )

    # Checking for empty n/a null anomalies and providing solutions. 

    if data.empty:
        raise ValueError(f"No price data was returned for {ticker}.")

    # Analyzing data columns (similar to data frames in R and then views closing prices of columns).

    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"].iloc[:, 0]
    else:
        prices = data["Close"]

    # Eradicating any invalidated arguments. 

    prices = prices.dropna()
    if len(prices) < 2: # final parameter closing checks for 2 days (prior relations)
        raise ValueError(f"Not enough price data was returned for {ticker}.")
    return prices

# Converting values in a metrics object (new data frame), this is something I learned, metrics object is basically a data frame conversion based on an array of input. 

def calculate_metrics(ticker: str, prices: pd.Series) -> StockMetrics:
    """Calculate return, risk-adjusted ratios, and drawdown."""
    daily_returns = prices.pct_change().dropna() # Daily returns. 
    annual_return = daily_returns.mean() * TRADING_DAYS_PER_YEAR # Mean of daily returns * trading days yields annual return.
    daily_volatility = daily_returns.std() # Standard deviation of daily returns yields volatility. 

    # Sharpe ratio calculation (annual return - risk free rate) / annualized volatility.

    annualized_volatility = daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR)
    sharpe_ratio = (annual_return - RISK_FREE_RATE) / annualized_volatility



    daily_risk_free_rate = RISK_FREE_RATE / TRADING_DAYS_PER_YEAR # Daily risk free risk rate derived from total trading day count. 
    downside_returns = daily_returns[daily_returns < daily_risk_free_rate] - daily_risk_free_rate # Looking for filtered returns that are < than daily risk free rate; aforementioned value is then substracted with the daily risk free rate for a positive to negative conversion.
    downside_deviation = tstd(downside_returns, ddof=1) if len(downside_returns) > 1 else 0.0 # Ensures that there are more than 1 days for comparison. Swing of standard deviation (extent) is determined. 
    # I'm learning about the delta degrees of freedom parameter that, when set to one, actually takes into context historical data (sample standard deviation)! - Risk determination
    annualized_downside_deviation = downside_deviation * np.sqrt(TRADING_DAYS_PER_YEAR) # Deviation is scaled up to an annual extent. An exponential relation is learned here. 
    sortino_ratio = (
        (annual_return - RISK_FREE_RATE) / annualized_downside_deviation # Accounts for an error output, and finally decides to calculate a viable sortino ratio. 
        if annualized_downside_deviation > 0
        else np.nan
    )

    # Compare each price with the highest price seen before it.
    running_peak = prices.cummax() # Calculates highest price recorded (cumulative max).
    maximum_drawdown = (prices / running_peak - 1).min() # Calculates drop of price with comparison from aforementioned variable. 

    #

    return StockMetrics( # Data container uses information storage techniques for optimized outputs.
        ticker=ticker,
        annual_return=annual_return,
        daily_volatility=daily_volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        maximum_drawdown=maximum_drawdown,
    )

# I'm learning about the Pareto Efficient Frontier, where stocks are compared against each other on the basis of efficient returns and decreased risk.
# Apparently, if a candidate is compared against another candidate, and that other candidate has lower/equal return AND higher or equal risk, the initially compared candidate is NOT efficient. 

def mark_efficient_stocks(metrics: list[StockMetrics]) -> None: # Compares market candidates with each other on the basis of volatility and returns. (Marked as efficient if more optimal).
    for candidate in metrics: # Looping through candidates.
        candidate.is_efficient = not any(
            other is not candidate # Beginning of comparisons. 
            and other.annual_return >= candidate.annual_return
            and other.daily_volatility <= candidate.daily_volatility
            and ( # Accounts for ties (one cateogiry MUST be better to some extent).
                other.annual_return > candidate.annual_return
                or other.daily_volatility < candidate.daily_volatility
            )
            for other in metrics # Looking through competitors. 
        )

# Formatted table printed of all calculated stock market risk metrics from yfinance API. 

def print_summary(metrics: list[StockMetrics]) -> None:
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

# Scatter plot, with the output file is constructed. 

def create_plot(metrics: list[StockMetrics], output_file: Path) -> None:
    efficient = [item for item in metrics if item.is_efficient] # Efficient organized in variable.
    other = [item for item in metrics if not item.is_efficient] # Not efficient organized in variable. 
    figure, axis = plt.subplots(figsize=(10, 6)) # 10x6 plot consutrtued. 
    axis.scatter(
        [item.daily_volatility for item in other], # x-axis
        [item.annual_return for item in other], # y-axis
        color="steelblue", # Plotting non-efficient stocks.
        s=100,
        label="Other stocks",
    )
    axis.scatter(
        [item.daily_volatility for item in efficient], # x-axis
        [item.annual_return for item in efficient], # y-axis
        color="darkorange", # Plotting efficient stocks. 
        edgecolor="black",
        s=140,
        label="Efficient stocks",
        zorder=3,
    )
    for item in metrics:
        axis.annotate(item.ticker, (item.daily_volatility, item.annual_return), xytext=(6, 6), textcoords="offset points")

    # Risk free rate, graph titles, and layout are all constructed here. 

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

# Parametered interpreted from terminal command line. Multiple parameters can be accepted. 

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze stock risk and return.")
    parser.add_argument("tickers", nargs="+", help="Ticker symbols, such as AAPL MSFT")
    return parser.parse_args() # Grouping input into a different object (argparse.Namespace).

# Arguments read and then interpreted accordingly. 

def main() -> None:
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

# main() method called. 

if __name__ == "__main__":
    main()