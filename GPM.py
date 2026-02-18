import yfinance as yf
import pandas as pd 
import numpy as np 
 
# Load data 
def getMonthlyPrices(tickers):
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(months=14)
    data = yf.download(tickers, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), auto_adjust=True)['Close']
    data = data.resample('ME').last()
    return data[0:len(data)-1]

# Step 1 - Calculate ri, ci and zi for every last trading day of the month 
def riCalc(data): 
    ri = []
    for col in data.columns:
        prices = data[col].dropna()
        r1 = (prices.iloc[-1] / prices.iloc[-2]) - 1 
        r3 = (prices.iloc[-1] / prices.iloc[-4]) - 1
        r6 = (prices.iloc[-1] / prices.iloc[-7]) - 1
        r12 = (prices.iloc[-1] / prices.iloc[-13]) - 1
        average = (r1 + r3 + r6 + r12) / 4 
        ri.append(average)
    return ri

def ciCalc(data, tickers):
    ci = []
    eq_returns = data[tickers].pct_change().dropna().mean(axis=1)
    eqWindow = eq_returns[-12:]

    for asset in tickers:
        window = data[asset].pct_change().dropna()[-12:]
        corr = window.corr(eqWindow)
        ci.append(corr)

    return ci
            
def ziCalc(ri, ci):
    ri = np.array(ri)
    ci = np.array(ci)
    return ri * (1 - ci)

# Step 2 - Determine how much to allocate to the crash protection 
def crashProtectionPercentage(ziValue): 
    count = 0
    for i in range(0, 12): 
        if ziValue[i] > 0.0: 
            count += 1 
    if count <= 6: 
        CP = 1.0 
    else: 
        CP = (12 - count) / 6

    return CP


# Step 3 - Allocate a 3rd of the remaining portfolio to the 3 risk assets with the highest zi value 
def allocation(zi, tickers, CPP): 
    remainingAllocation = 1.0 - CPP
    combined = list(zip(tickers, zi))
    top3 = sorted(combined, key=lambda x: x[1], reverse=True)[:3]
    topTickers = [x[0] for x in top3]
    return topTickers, remainingAllocation

def getGPM(GPM): 
    return GPM


def safeAssetSelection(data, risky_tickers):
    safe_assets = ["IEF", "BIL"]
    safe_scores = {}

    # equal-weighted risky portfolio returns
    eq_returns = data[risky_tickers].pct_change().dropna().mean(axis=1)[-12:]

    for asset in safe_assets:
        if asset in data.columns:
            prices = data[asset].dropna()
            if len(prices) < 14:
                continue

            # ri (same as before)
            r1 = (prices.iloc[-1] / prices.iloc[-2]) - 1
            r3 = (prices.iloc[-1] / prices.iloc[-4]) - 1
            r6 = (prices.iloc[-1] / prices.iloc[-7]) - 1
            r12 = (prices.iloc[-1] / prices.iloc[-13]) - 1
            ri = (r1 + r3 + r6 + r12) / 4

            # correlation vs risky basket
            window = data[asset].pct_change().dropna()[-12:]
            ci = window.corr(eq_returns)

            safe_scores[asset] = ri * (1 - ci)

    if not safe_scores:
        return "BIL"

    return max(safe_scores, key=safe_scores.get)


# Main 
tickers = ["SPY", "QQQ", "IWM", "VGK", "EWJ", "EEM", "VNQ", "GSG", "GLD", "HYG", "LQD", "TLT"]
data = getMonthlyPrices(tickers)
ri = riCalc(data)
ci = ciCalc(data, tickers)
zi = ziCalc(ri, ci)
CPP = crashProtectionPercentage(zi)

topTickers, remainingAllocation = allocation(zi, tickers, CPP) 

GPM = []
for i in range(len(topTickers)):
    GPM.append([topTickers[i], remainingAllocation / 3])

best_safe = safeAssetSelection(data, tickers)  # tickers = risky assets list
GPM.append([best_safe, CPP])

