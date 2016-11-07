from utils import Player, Rolls, Game, roll_dice, checkSimulatedQuantiles
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

###############################################################
# Let's run a simulation to make sure our statistics are good #
###############################################################

# simulate a bunch of rolls
ngames = 1000
nrolls = 50
agg = []
cdf_method = 'pb' # 'pb', 'gaussian', 'exact' or 'binomial'
for sim in range(ngames):
    simrolls = Rolls()
    gsim = Game({'simp1': Player(simrolls)})
    gsim.players['simp1'].add_settlements([2, 3, 6])
    gsim.players['simp1'].add_settlements([5, 3, 11])
    for roll in roll_dice(nrolls):
        gsim.add_roll(roll)

    resources_count = gsim.players['simp1'].resources_count()
    if cdf_method == 'pb':
        lowerbound = 0 if resources_count == 0 else gsim.players['simp1'].get_percentile_from_resources_poibin(resources_count - 1)
        agg.append(random.uniform(lowerbound, gsim.players['simp1'].get_percentile_from_resources_poibin(resources_count)))
    elif cdf_method == 'gaussian':
        lowerbound = 0 if resources_count == 0 else gsim.players['simp1'].get_percentile_from_resources_gaussian(resources_count - 1)
        agg.append(random.uniform(lowerbound, gsim.players['simp1'].get_percentile_from_resources_gaussian(resources_count)))
    elif cdf_method == 'binomial':
        try:
            pctile = gsim.players['simp1'].get_percentile_from_resources(resources_count)
            lowerbound = 0 if resources_count == 0 else pctile[0]
            agg.append(random.uniform(lowerbound, pctile[1]))
        except:
            print("game {} failed".format(sim))
            raise
    elif cdf_method == 'exact':
        lowerbound = 0 if resources_count == 0 else gsim.players['simp1'].get_percentile_from_resources_exact(resources_count - 1)
        agg.append(random.uniform(lowerbound, gsim.players['simp1'].get_percentile_from_resources_exact(resources_count)))
    print('simulated game: {}'.format(sim))

# percentiles should be uniform
plt.hist(agg, bins=15)

# should be 45 degree line
agg.sort()
plt.scatter(range(len(agg)), agg)

# checking a few quantiles
df = pd.DataFrame(agg)
df.quantile(np.arange(0, 1, 0.05))

# check accuracy numerically:
checkSimulatedQuantiles(agg)

# summaries
print(gsim.players['simp1'].resources_count())
print(gsim.players['simp1'].expected_resources_count())
print(gsim.players['simp1'].get_performance_summary())

# checking resources at percentile
print(gsim.players['simp1'].resources_at_percentile(0.9))
print(gsim.players['simp1'].resources_at_percentile_gaussian(0.9))

# TODO:
#print(gsim.players['simp1'].resources_at_percentile_poibin(0.9))


