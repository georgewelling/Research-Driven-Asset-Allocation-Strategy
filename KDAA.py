import yfinance as yf
import pandas as pd
import numpy as np

# Data
def getMonthlyPrices(tickers):
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(months=14)
    data = yf.download(tickers, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), auto_adjust=True)['Close']
    data = data.resample('ME').last()
    return data[0:len(data)-1]

def momentumScore(data):
    momentumScores = []
    for col in data.columns:
        prices = data[col].dropna()
        if len(prices) < 14:
            momentumScores.append(float("nan"))
            continue
        mom = (12 * (prices.iloc[-1]/prices.iloc[-2] - 1)) \
            + (4 * (prices.iloc[-1]/prices.iloc[-4] - 1)) \
            + (2 * (prices.iloc[-1]/prices.iloc[-7] - 1)) \
            + (prices.iloc[-1]/prices.iloc[-13] - 1)
        momentumScores.append(mom)
    return momentumScores

# Crash protection
def crashProtectionCheck():
    crashData = getMonthlyPrices(["IEF"])
    crashMomentum = momentumScore(crashData)
    if crashMomentum[0] > 0:
        return "IEF"
    else:
        return "BIL"

# Canary rule
def allocationAmount(canaryMomentum):
    positive = sum(1 for m in canaryMomentum if m > 0)
    if positive == 0:
        return 1.0, 0.0
    elif positive == 1:
        return 0.5, 0.5
    else:
        return 0.0, 1.0

# Risky allocation with min-var portfolio
def riskyUniverseAllocation(risky):
    riskyData = getMonthlyPrices(risky)
    riskyMomentum = momentumScore(riskyData)
    riskyCombined = list(zip(risky, riskyMomentum))

    # Top 5 risky by momentum
    top5Risky = sorted(riskyCombined, key=lambda x: x[1], reverse=True)[:5]
    top5Risky = [item for item in top5Risky if item[1] >= 0]

    if len(top5Risky) == 0:
        return []

    tickers = [t[0] for t in top5Risky]

    if len(tickers) == 1:
        return [(tickers[0], 1.0)]

    data = riskyData[tickers].dropna()
    returns = data.pct_change().dropna()

    corr_1m = returns.iloc[-1:].corr()
    corr_3m = returns.iloc[-3:].corr()
    corr_6m = returns.iloc[-6:].corr()
    corr_12m = returns.iloc[-12:].corr()

    corr_combined = (12*corr_1m + 4*corr_3m + 2*corr_6m + corr_12m) / 19

    vols = returns.std()
    cov_combined = corr_combined.values * np.outer(vols, vols)
    cov_combined = np.nan_to_num(cov_combined, nan=0.0, posinf=0.0, neginf=0.0)

    if not np.any(cov_combined):
        equal_weight = 1.0 / len(tickers)
        return [(t, equal_weight) for t in tickers]

    try:
        inv_cov = np.linalg.pinv(cov_combined)
    except np.linalg.LinAlgError:
        equal_weight = 1.0 / len(tickers)
        return [(t, equal_weight) for t in tickers]

    ones = np.ones(len(tickers))
    raw_weights = inv_cov @ ones

    if raw_weights.sum() == 0 or np.any(np.isnan(raw_weights)):
        equal_weight = 1.0 / len(tickers)
        weights = np.array([equal_weight] * len(tickers))
    else:
        weights = raw_weights / raw_weights.sum()

    return list(zip(tickers, weights.round(4).tolist()))

# Master KDAA
def getKDAA(risky, canary):
    canaryData = getMonthlyPrices(canary)
    canaryMomentum = momentumScore(canaryData)
    crashAsset = crashProtectionCheck()
    crashAlloc, riskyAlloc = allocationAmount(canaryMomentum)
    riskyPortfolio = riskyUniverseAllocation(risky)

    allocation = []

    if crashAlloc > 0:
        allocation.append((crashAsset, crashAlloc))

    for ticker, weight in riskyPortfolio:
        allocation.append((ticker, weight * riskyAlloc))

    return allocation

risky = ["EEM", "IEF", "SPY", "VGK", "EWJ", "VNQ", "RWX", "TLT", "DBC", "GLD"]
canary = ["EEM", "AGG"]

allocation = getKDAA(risky, canary)
