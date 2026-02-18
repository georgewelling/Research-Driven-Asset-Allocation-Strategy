import yfinance as yf
import pandas as pd

# Load data 
def getMonthlyPrices(tickers):
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(months=14)
    data = yf.download(
        tickers, 
        start=start.strftime('%Y-%m-%d'), 
        end=end.strftime('%Y-%m-%d'), 
        auto_adjust=True
    )['Close']
    data = data.resample('ME').last()
    return data[0:len(data)-1]

# Momentum calculation
def momentumScore(data): 
    momentumScores = []
    for col in data.columns:
        prices = data[col].dropna()
        if len(prices) < 14:
            momentumScores.append(float("nan"))
            continue 
        r1 = (prices.iloc[-1] / prices.iloc[-2]) - 1
        r3 = (prices.iloc[-1] / prices.iloc[-4]) - 1
        r6 = (prices.iloc[-1] / prices.iloc[-7]) - 1
        r12 = (prices.iloc[-1] / prices.iloc[-13]) - 1
        average = (r1 + r3 + r6 + r12) / 4
        momentumScores.append(average)
    return momentumScores

# Hedge Asset Allocation
def getHAA(canaryAsset, offensiveAssets):
    allocation = []

    # Canary (TIP)
    canaryMomentum = momentumScore(getMonthlyPrices(canaryAsset))[0]

    if canaryMomentum > 0:
        # Risk-on: pick 4 best offensive assets
        offensiveData = getMonthlyPrices(offensiveAssets)
        offensiveMomentum = momentumScore(offensiveData)
        offensiveCombined = list(zip(offensiveAssets, offensiveMomentum))
        top4 = sorted(offensiveCombined, key=lambda x: x[1], reverse=True)[:4]

        # Allocate 25% to each top 4, or BIL if its momentum is negative
        for ticker, mom in top4:
            if mom > 0:
                allocation.append([ticker, 0.25])
            else:
                allocation.append(["BIL", 0.25])

    else:
        # Risk-off: TIP < 0
        IEFmomentum = momentumScore(getMonthlyPrices(["IEF"]))[0]
        if IEFmomentum > 0:
            allocation.append(["IEF", 1.0])
        else:
            allocation.append(["BIL", 1.0])

    return allocation

canaryAsset = ["TIP"]
offensiveAssets = ["IEF", "SPY", "IWM", "EFA", "EEM", "VNQ", "DBC", "TLT"]

allocation = getHAA(canaryAsset, offensiveAssets)
