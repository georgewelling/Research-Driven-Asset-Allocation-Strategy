import yfinance as yf
import pandas as pd 

 
# Load data 
def getMonthlyPrices(tickers):
    end = pd.Timestamp.today()
    start = end - pd.DateOffset(months=14)
    data = yf.download(tickers, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), auto_adjust=True)['Close']
    data = data.resample('ME').last()
    return data[0:len(data)-1]

# Step 1 - Calculate the momentum score 
def momentumScore(data):
    momentumScores = []
    for col in data.columns: 
        prices = data[col].dropna()
        
        # Need at least 14 months (index 0..13) for 12-month momentum
        if len(prices) < 14:
            momentumScores.append(float("nan"))
            continue

        mom = (12 * (prices.iloc[-1]/prices.iloc[-2] - 1)) \
            + (4 * (prices.iloc[-1]/prices.iloc[-3] - 1)) \
            + (2 * (prices.iloc[-1]/prices.iloc[-5] - 1)) \
            + (prices.iloc[-1]/prices.iloc[-13] - 1)

        momentumScores.append(mom)
    return momentumScores

# Step 2 - Check to see what scores are positive and -ve
def check(momentumScore):
    count = 0
    for i in range(0,len(momentumScore)):
        if momentumScore[i] > 0: 
            count += 1 
    return count 


# Main 
offensiveAssets = ["AGG", "EEM", "EFA", "SPY"] 
defensiveAssets = ["LQD", "IEF", "BIL"] 

dataOffensive = getMonthlyPrices(offensiveAssets)
dataDefensive = getMonthlyPrices(defensiveAssets)

momentumScoresOffensive = momentumScore(dataOffensive)
momentumScoresDefensive = momentumScore(dataDefensive) 
positiveCheck = check(momentumScoresOffensive)

def selectAsset(positiveCount, offensiveAssets, momentumScoresOffensive,
                defensiveAssets, momentumScoresDefensive):
    if positiveCount == len(offensiveAssets):  
        combined = list(zip(offensiveAssets, momentumScoresOffensive))
        highestAsset = max(combined, key=lambda x: x[1])[0]
    else:  
        combined = list(zip(defensiveAssets, momentumScoresDefensive))
        highestAsset = max(combined, key=lambda x: x[1])[0]
    return highestAsset

highestAsset = selectAsset(positiveCheck, offensiveAssets, momentumScoresOffensive, defensiveAssets, momentumScoresDefensive)

def getVAA(highestAsset):
    return [(highestAsset, 1.0)]
    




