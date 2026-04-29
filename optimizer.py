import numpy as np
import pandas as pd
import yfinance as yf
from pypfopt import EfficientFrontier, risk_models, expected_returns

def fetch_prices(tickers, period="2y"):
    data = yf.download(tickers, period=period, auto_adjust=True)["Close"]
    data = data.dropna()
    return data

def get_optimizer(prices):
    mu = expected_returns.mean_historical_return(prices)
    S  = risk_models.sample_cov(prices)
    ef = EfficientFrontier(mu, S)
    return ef, mu, S

def optimize_portfolio(tickers, period="2y", objective="max_sharpe"):
    prices = fetch_prices(tickers, period)
    ef, mu, S = get_optimizer(prices)

    if objective == "max_sharpe":
        ef.max_sharpe(risk_free_rate=0.05)
    elif objective == "min_volatility":
        ef.min_volatility()

    weights = ef.clean_weights()
    performance = ef.portfolio_performance(verbose=False)

    return {
        "weights": weights,
        "return": round(performance[0] * 100, 2),
        "volatility": round(performance[1] * 100, 2),
        "sharpe": round(performance[2], 2),
        "prices": prices
    }

def get_frontier_data(tickers, period="2y", points=50):
    prices = fetch_prices(tickers, period)
    mu = expected_returns.mean_historical_return(prices)
    S  = risk_models.sample_cov(prices)

    frontier_vols = []
    frontier_rets = []

    ef_temp = EfficientFrontier(mu, S)
    min_ret = float(min(mu))
    max_ret = float(max(mu))
    target_returns = np.linspace(min_ret + 0.01, max_ret - 0.01, points)

    for target in target_returns:
        try:
            ef_temp = EfficientFrontier(mu, S)
            ef_temp.efficient_return(target)
            p = ef_temp.portfolio_performance(verbose=False)
            frontier_vols.append(round(p[1] * 100, 2))
            frontier_rets.append(round(p[0] * 100, 2))
        except:
            continue

    return frontier_vols, frontier_rets
def backtest(tickers):
    import yfinance as yf
    from datetime import datetime, timedelta
    from pypfopt import EfficientFrontier, risk_models, expected_returns

    end   = datetime.today()
    split = end - timedelta(days=365)
    start = split - timedelta(days=365 * 2)

    all_data = yf.download(tickers, start=start, end=end, auto_adjust=True)["Close"]
    all_data = all_data.dropna()

    train_data = all_data[all_data.index < split]
    test_data  = all_data[all_data.index >= split]

    mu = expected_returns.mean_historical_return(train_data)
    S  = risk_models.sample_cov(train_data)
    ef = EfficientFrontier(mu, S)
    ef.max_sharpe(risk_free_rate=0.05)
    weights = ef.clean_weights()

    weight_arr    = [weights[t] for t in tickers]
    daily_returns = test_data.pct_change().dropna()

    portfolio_returns = daily_returns @ weight_arr
    equal_returns     = daily_returns.mean(axis=1)

    cumulative_portfolio = (1 + portfolio_returns).cumprod()
    cumulative_equal     = (1 + equal_returns).cumprod()

    return {
        "portfolio_final":    round((cumulative_portfolio.iloc[-1] - 1) * 100, 2),
        "equal_weight_final": round((cumulative_equal.iloc[-1] - 1) * 100, 2),
        "portfolio_returns":  portfolio_returns,
        "equal_returns":      equal_returns,
        "cumulative_portfolio": cumulative_portfolio,
        "cumulative_equal":     cumulative_equal,
        "weights": weights
    }


def evaluate_performance(daily_returns):
    import numpy as np

    total_return  = (1 + daily_returns).cumprod().iloc[-1] - 1
    annual_return = (1 + total_return) ** (252 / len(daily_returns)) - 1
    volatility    = daily_returns.std() * (252 ** 0.5)
    sharpe        = (annual_return - 0.05) / volatility

    rolling_max  = (1 + daily_returns).cumprod().cummax()
    drawdown     = ((1 + daily_returns).cumprod() - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    return {
        "Total Return":  f"{round(total_return * 100, 2)}%",
        "Annual Return": f"{round(annual_return * 100, 2)}%",
        "Volatility":    f"{round(volatility * 100, 2)}%",
        "Sharpe Ratio":  round(sharpe, 2),
        "Max Drawdown":  f"{round(max_drawdown * 100, 2)}%"
    }