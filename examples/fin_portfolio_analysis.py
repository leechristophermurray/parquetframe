"""
Portfolio Analysis Example using ParquetFrame FIN Module

This example demonstrates:
- Multi-asset portfolio tracking
- Portfolio returns calculation
- Risk metrics (volatility, Sharpe ratio, Sortino ratio)
- Value at Risk (VaR) and Conditional VaR
- Correlation analysis
"""

import numpy as np
import pandas as pd

from parquetframe._rustic import (
    fin_cvar,
    fin_sharpe_ratio,
    fin_sortino_ratio,
    fin_value_at_risk,
)

# Convert to Arrow for FIN operations (using internal _rustic module)

# Sample portfolio data
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")

# Create portfolio with 3 assets
portfolio = pd.DataFrame(
    {
        "date": dates,
        "AAPL_price": 150 + np.cumsum(np.random.randn(len(dates)) * 2),
        "MSFT_price": 350 + np.cumsum(np.random.randn(len(dates)) * 3),
        "GOOGL_price": 140 + np.cumsum(np.random.randn(len(dates)) * 2.5),
    }
)

# Portfolio weights
weights = {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}

print("=" * 80)
print("PORTFOLIO ANALYSIS WITH PARQUETFRAME FIN")
print("=" * 80)
print(f"\nAnalyzing {len(dates)} days of data for 3-asset portfolio")
print(
    f"Portfolio Weights: AAPL={weights['AAPL']:.0%}, MSFT={weights['MSFT']:.0%}, GOOGL={weights['GOOGL']:.0%}"
)
print()

# Calculate returns for each asset

for asset in ["AAPL", "MSFT", "GOOGL"]:
    col = f"{asset}_price"
    portfolio[f"{asset}_return"] = portfolio[col].pct_change()

# Calculate portfolio return (weighted average)
portfolio["portfolio_return"] = (
    portfolio["AAPL_return"] * weights["AAPL"]
    + portfolio["MSFT_return"] * weights["MSFT"]
    + portfolio["GOOGL_return"] * weights["GOOGL"]
)

# Remove NaN from first row
portfolio = portfolio.dropna()


# Calculate portfolio metrics
returns_array = portfolio["portfolio_return"].values

print("📊 PORTFOLIO PERFORMANCE METRICS")
print("-" * 80)

# Total return
total_return = (1 + portfolio["portfolio_return"]).prod() - 1
print(f"Total Return:              {total_return:>12.2%}")

# Annualized return
trading_days = len(portfolio)
annualized_return = (1 + total_return) ** (252 / trading_days) - 1
print(f"Annualized Return:         {annualized_return:>12.2%}")

# Volatility (annualized)
volatility = portfolio["portfolio_return"].std() * np.sqrt(252)
print(f"Annualized Volatility:     {volatility:>12.2%}")

# Sharpe Ratio (assuming 3% risk-free rate)
sharpe = fin_sharpe_ratio(returns_array, 0.03, 252)
print(f"Sharpe Ratio:              {sharpe:>12.2f}")

# Sortino Ratio
sortino = fin_sortino_ratio(returns_array, 0.03, 252)
print(f"Sortino Ratio:             {sortino:>12.2f}")

print()
print("⚠️  RISK METRICS")
print("-" * 80)

# Value at Risk (95% confidence)
var_95 = fin_value_at_risk(returns_array, 0.95)
print(f"VaR (95%):                 {var_95:>12.2%}")

# Value at Risk (99% confidence)
var_99 = fin_value_at_risk(returns_array, 0.99)
print(f"VaR (99%):                 {var_99:>12.2%}")

# Conditional VaR (Expected Shortfall)
cvar_95 = fin_cvar(returns_array, 0.95)
print(f"CVaR (95%):                {cvar_95:>12.2%}")

cvar_99 = fin_cvar(returns_array, 0.99)
print(f"CVaR (99%):                {cvar_99:>12.2%}")

# Maximum Drawdown
cumulative_returns = (1 + portfolio["portfolio_return"]).cumprod()
running_max = cumulative_returns.expanding().max()
drawdown = (cumulative_returns - running_max) / running_max
max_drawdown = drawdown.min()
print(f"Maximum Drawdown:          {max_drawdown:>12.2%}")

print()
print("🔗 CORRELATION ANALYSIS")
print("-" * 80)

# Calculate correlation matrix
returns_df = portfolio[["AAPL_return", "MSFT_return", "GOOGL_return"]]
correlation = returns_df.corr()

print("\nAsset Correlation Matrix:")
print(correlation.to_string(float_format=lambda x: f"{x:>7.3f}"))

print()
print("📈 INDIVIDUAL ASSET PERFORMANCE")
print("-" * 80)

for asset in ["AAPL", "MSFT", "GOOGL"]:
    asset_returns = portfolio[f"{asset}_return"].values
    asset_sharpe = fin_sharpe_ratio(asset_returns, 0.03, 252)
    asset_vol = portfolio[f"{asset}_return"].std() * np.sqrt(252)

    print(f"\n{asset}:")
    print(f"  Sharpe Ratio:    {asset_sharpe:>8.2f}")
    print(f"  Volatility:      {asset_vol:>8.2%}")

print()
print("=" * 80)
print("✅ Analysis complete!")
print("=" * 80)
print("\nKey Insights:")
print(f"• Portfolio generated {annualized_return:.2%} annualized return")
print(f"• Risk-adjusted performance (Sharpe): {sharpe:.2f}")
print(f"• Worst expected daily loss (VaR 95%): {var_95:.2%}")
print(f"• Maximum observed drawdown: {max_drawdown:.2%}")
