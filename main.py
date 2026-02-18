from collections import defaultdict

import KDAA
import VAA
import HAA
import GPM
import DAA


# KDAA
risky = ["EEM", "IEF", "SPY", "VGK", "EWJ", "VNQ", "RWX", "TLT", "DBC", "GLD"]
canary = ["EEM", "AGG"]
KDAAAllocation = KDAA.getKDAA(risky, canary)
# VAA
VAAAllocation = VAA.getVAA(VAA.highestAsset)  
# HAA
HAAAllocation = HAA.getHAA(HAA.canaryAsset, HAA.offensiveAssets) 
# GPM
GPMAllocation = GPM.getGPM(GPM.GPM) 
# DAA
DAAAllocation = DAA.getDAA(DAA.risky, DAA.protective, DAA.canary)
Raccoon = KDAAAllocation + VAAAllocation + HAAAllocation + GPMAllocation + DAAAllocation
agg = defaultdict(float)
for t, w in Raccoon:
    agg[t] += w

grouped_allocations = [(t, w / 5) for t, w in agg.items()]
print(grouped_allocations)
