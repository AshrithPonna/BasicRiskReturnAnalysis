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
This application takes real-time financial metrics from yfinance API and then uses them to calculate risk & return comparisons between companies. 
- [x] Stock Annual Return (mean of daily returns and total trading days)
- [x] Daily Risk (risk free rate and total trading days)
- [x] Sharpe Ratio (actual return, arbitrary beta risk free rate, and return standard deviation)
- [x] Sortino Ratio (actual returns, target return, and downside deviation).
- [x] Max Drawdown (change in price based on cumulative maximum value).
- [x] Efficiency Determination (company versus company on basis of risk & return).

## Learning Technicalities
getting back to this
