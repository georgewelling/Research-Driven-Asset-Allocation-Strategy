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
    data = data.resample('ME').last() # gets month end data. 
    return data[0:len(data)-1]

# Momentum score
def momentumScore(data):
    momentumScores = []
    for col in data.columns: 
        prices = data[col].dropna()
        if len(prices) < 14:  # not enough history
            momentumScores.append(float("nan")) # could interfere with calculations
            continue
        mom = (12 * (prices.iloc[-1]/prices.iloc[-2] - 1)) \
            + (4 * (prices.iloc[-1]/prices.iloc[-3] - 1)) \
            + (2 * (prices.iloc[-1]/prices.iloc[-5] - 1)) \
            + (prices.iloc[-1]/prices.iloc[-13] - 1)
        momentumScores.append(mom)
    return momentumScores

# Defensive Asset Allocation (DAA)
def getDAA(risky, protective, canary):
    # Canary
    canaryData = getMonthlyPrices(canary)
    canaryMomentum = momentumScore(canaryData) 
    canaryCombined = list(zip(canary, canaryMomentum))

    # Risky
    riskyData = getMonthlyPrices(risky) 
    riskyMomentum = momentumScore(riskyData) 
    riskyCombined = list(zip(risky, riskyMomentum))
    top6Risky = sorted(riskyCombined, key=lambda x: x[1], reverse=True)[:6]
    topTickers = [x[0] for x in top6Risky]

    # Protective
    protectiveData = getMonthlyPrices(protective) 
    protectiveMomentum = momentumScore(protectiveData)
    protectiveCombined = list(zip(protective, protectiveMomentum))
    topProtective = sorted(protectiveCombined, key=lambda x: x[1], reverse=True)[0]

    # Canary check
    canaryNeg = sum(1 for m in canaryMomentum if m < 0)
    allocation = []
    remainingAllocation = 1.0

    if canaryNeg == 0: 
        # 100% risky (equally split across top 6)
        for t in topTickers:
            allocation.append([t, remainingAllocation/6])
    elif canaryNeg == 1: 
        # 50% risky (top 6 equally), 50% top protective
        for t in topTickers:
            allocation.append([t, remainingAllocation/12])
        allocation.append([topProtective[0], remainingAllocation/2])
    else: 
        # 100% top protective
        allocation.append([topProtective[0], remainingAllocation])

    return allocation


risky = ["EEM", "SPY", "IWM", "QQQ", "VGK", "EWJ", "VNQ", "DBC", "GLD", "TLT", "HYG", "LQD"]
protective = ["SHY", "IEF", "LQD"]
canary = ["EEM", "AGG"]

allocation = getDAA(risky, protective, canary)
