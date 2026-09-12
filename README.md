# Basic Risk Return Analysis

Stock Risk Analyses 

## Installation
```bash
pip install -r requirements.txt # All libraries are noted on the .txt file. 
```
## Usage
```bash 
python risk_return_analyzer.py QMCO (single parameter) # Analyze QMCO
python risk_return_analyzer.py QMCO SPCX COF (multiple parameters) # Analyze QMCO, SPCX, AND COF (with efficiency comparisons)
```
## Overview
This application takes real-time financial metrics from the yfinance API and then uses them to calculate risk & return comparisons between companies through several variables:
- [x] Stock Annual Return (mean of daily returns and total trading days)
- [x] Daily Risk (risk free rate and total trading days)
- [x] Sharpe Ratio (actual return, arbitrary beta risk free rate, and return standard deviation)
- [x] Sortino Ratio (actual returns, target return, and downside deviation).
- [x] Max Drawdown (change in price based on cumulative maximum value).
- [x] Efficiency Determination (company versus company on basis of risk & return; Pareto Efficient Frontier).

These are all correlative to stocks; plots (scatter) for historical distributions and comparisons, with asymptotic risk levels are created. 

## Learning Technicalities
- [x] Formulas and rationales for a multitude of different financial concepts (Sharpe's Ratio, Sortino's Ratio, the. Pareto Efficient Frontier, etc.).
- [x] Utilizing matplot.lib to construct a scatter plot consistent of multiple plot, in conjunction with pathlib (localizing graph's file path).
- [x] Utilizing datetime to pull daily information and utilize it to calculate historical-based stock data metrics.
- [x] Developing skills in relation to pulling financial information from the yfinance API and even manipulating said information.
- [x] Utilizing filter conditions to filter out specific standard deviations from a data frame (in this case, downside deviations).
- [x] Through comparison statements and conditionals, comparing different elements (candidates) with others based on attributes (in this case, risk and return).
- [x] Using a new library known as scipy.stats for tstd() function, which trims excess values during a standard deviation calculation from a data source (frame or otherwise).
- [x] Parsing multiple input parameters from the terminal and calculating various different values for each, with comparison statements (referencing point 6).

## Skills
- [x] Python 3
- [x] yfinance (stock data)
- [x] pandas (data manipulation)
- [x] numpy (calculations)
- [x] matplotlib (visualization)
- [x] scipy.stats (statistics)

## Developer Logs

Tested and reviewed codebase.

//TODO

- [ ] RiskFreeRate --> Constantly Changing (Dynamic)
