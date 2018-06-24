import collections
import itertools
import random
from bisect import bisect

import numpy as np
import pandas as pd
import scipy.stats

from catankarma.poibin.poibin import PoiBin


def convert_roll_to_prob(roll):
    """Calculate probability of each roll"""
    if 2 <= roll <= 7 :
        return (roll - 1) / 36
    elif 7 < roll <= 12:
        return (13 - roll) / 36
    else:
        print('impossible roll: not between 2 and 12')
        raise


def roll_dice(n_rolls, n_dice=2):
    """randomly roll dice n_dice times"""
    def roll_once(n_dice):
        return sum([random.randint(1, 6) for _ in range(n_dice)])
    return [roll_once(n_dice) for _ in range(n_rolls)]


def check_simulated_quantiles(quantiles, step=0.01):
    """ Check how uniform the sampled quantiles are"""
    df = pd.DataFrame(quantiles)
    qindex = np.arange(0, 1, step)
    dev = df.quantile(qindex).as_matrix().flatten() - qindex
    print('average error {}'.format(np.mean(dev)))
    print('median error {}'.format(np.median(dev)))
    print('median abs error {}'.format(np.mean(abs(dev))))
    return [np.mean(dev), np.median(dev), np.mean(abs(dev))]


class Rolls(object):

    @classmethod
    def __init__(self):
        self.rolls = []

    @classmethod
    def add_roll_to_list(self, roll):
        """add roll to list"""
        return self.rolls.append(roll)

    @classmethod
    def get_roll_history(self):
        """return history of rolls thus far"""
        return self.rolls

    @classmethod
    def print_get_roll_history(self):
        """print roll history in pretty format"""
        turn_roll = list(zip(range(len(self.rolls)), self.rolls))
        [print('turn #{0}: {1}'.format(turn[0], turn[1])) for turn in turn_roll]

    def delete_roll(self, turn=None):
        """delete a roll.  default to last roll"""
        if turn is None:
            turn = len(self.rolls)-1
        del self.rolls[turn]

    def replace_roll(self, turn, roll):
        """replace a roll for a specific turn with something else"""
        self.rolls[turn] = roll

    def get_turn_number(self):
        """what turn are we on?"""
        return len(self.rolls)

    def get_rolls_probability(self):
        """convert list of rolls to probabilties"""
        return list(map(lambda x: convert_roll_to_prob(x), self.rolls))


class Player(Rolls):

    def __init__(self, rolls):
        self.rolls = rolls.rolls
        self.settlements = []
        self.settlements_resources = []

    def add_settlements(self, die):
        """adds the new numbers gained from a new settlement for a player"""
        for d in die:
            self.settlements.append((0, d))
            self.settlements_resources.append((0, d))

    def settlements_prob(self):
        return list(map(lambda x: (x[0], convert_roll_to_prob(x[1])), self.settlements))

    def expected_resources_count(self):
        """calculate the expected number of resources"""
        return sum([p * c for p, c in self.settlements_prob()])

    def resources_count(self):
        """actual number of resources"""
        return sum(list(zip(*self.settlements_resources))[0])

    def resources_at_percentile(self, percentile):
        """Does not take into consideration clumpiness of cities that return 2 or 0 resources, not just 1"""
        return sum(scipy.stats.binom.ppf(percentile,
                                         n=list(list(zip(*self.settlements_prob()))[0]),
                                         p=list(list(zip(*self.settlements_prob()))[1])
                                         )
                   )

    def resources_at_percentile_gaussian(self, percentile, k=1):
        expected = self.expected_resources_count()
        return scipy.stats.norm.ppf(percentile,
                                    loc=expected,
                                    scale=k*(expected**0.5)
                                    )

    def make_cdf(self, step=0.01):
        """
        creates mapping for percentile => # of resources expected at that percentile
        """
        nrolls = list(list(zip(*self.settlements_prob()))[0])
        hexes_prob = list(list(zip(*self.settlements_prob()))[1])
        cdf = []
        for i in np.arange(step, 1, step):
            cdf.append([round(float(i), 5), sum(scipy.stats.binom.ppf(i, n=nrolls, p=hexes_prob))])
        return cdf

    def get_percentile_from_resources(self, resources=None, step=0.01):
        """
        given the pre-calculated CDF, what is the probability of receiving X resources
        """
        resources = self.resources_count() if resources is None else resources
        cdf = self.make_cdf(step)

        try:
            # if resources exists in CDF, return the range of probs
            pctiles = [cdf[i][0] for i, j in enumerate([i[1] for i in cdf]) if j == resources]
            return(min(pctiles), max(pctiles))
        except ValueError:
            # if resources doesnt exist in CDF, check
            if resources < max([i[1] for i in cdf]):
                pctiles = cdf[bisect([i[1] for i in cdf], resources)][0]
                return (pctiles, pctiles)
            else:
                raise Exception("impossible, you can't have these many resources!")

    def get_percentile_from_resources_poibin(self, resources=None):
        """
        Use Poisson Binomial distribution CDF (PoiBin) to calculate percentile given resources
        """
        resources = self.resources_count() if resources is None else resources
        rolls_p = [val for sublist in [x[0] * [x[1]] for x in self.settlements_prob()] for val in sublist]
        pb = PoiBin(rolls_p)
        return pb.cdf(resources)

    def get_percentile_from_resources_gaussian(self, resources=None, k=1):
        """
        Use Gaussian approximation to calculate percentile given resources
        """
        resources = self.resources_count() if resources is None else resources
        expected = self.expected_resources_count()
        return scipy.stats.norm.cdf(resources, loc=expected, scale=k*(expected**0.5))

    def get_percentile_from_resources_exact(self, resources=None):
        """
        Use exact CDF creation to calculate percentile given resources
        """

        def get_length_of_cdf():
            """Calculate how many elements to make CDF (depends on number of rolls and which settlements occupied"""
            settlements_agg = collections.defaultdict(int)
            for r, s in self.settlements: settlements_agg[s] += r
            max_resources = settlements_agg[max(settlements_agg, key=settlements_agg.get)]
            len_cdf = max(1, max_resources) * len(Rolls.get_roll_history())
            return len_cdf

        resources = self.resources_count() if resources is None else resources
        len_cdf = get_length_of_cdf()
        pmf = np.zeros(len_cdf*4) # temporary hack... needs to update length when new settlements get added
        pmf[0] = 1
        turns = len(self.get_roll_history())

        # list[2tuple].  First tuple element is range with settlement.  Second tuple element is number on settlement
        settprob = [(range(turns-i[0], turns), i[1]) for i in self.settlements]
        settprob.sort(key=lambda tup: tup[1])

        # list[2tuple]. First tuple element is dice roll.  Second tuple element is list w ranges of turns w settlement
        aggsett_range = [(key, list(v for v, k in group)) for key, group in itertools.groupby(settprob, key=lambda x: x[1])]

        # list[2tuple]. First tuple element is dice roll.  Second tuple element is Counter w key for turn # and value
        # for num of settlements at that turn
        aggsett = list(map(lambda x: (x[0], collections.Counter(list(itertools.chain(*x[1])))), aggsett_range))

        for i in range(turns):
            print(pmf[0:10])
            # print(np.cumsum(pmf)[0:10])
            print('')

            # list[2tuple].  First element is prob of roll number.  Second is # of settlements on number at turn i
            isett = list(map(lambda x: (convert_roll_to_prob(x[0]), x[1][i]), aggsett))
            isett.sort(key=lambda tup: tup[1])

            # list[2tuple].  First element is # of resources for turn i.  Second element is combined probability
            isettagg = [(key, sum(v for v, k in group)) for key, group in itertools.groupby(isett, key=lambda x: x[1])]

            # Adding 0 with leftover probability
            isettagg.append((0, 1 - sum([x[1] for x in isettagg])))

            pmf = sum([np.roll(pmf, j[0])*j[1] for j in isettagg])
        return np.cumsum(pmf)[resources]


    def get_rolls_probability_test(self):
        return self.get_rolls_probability()

    def get_performance_summary(self):
        print(self.resources_at_percentile(0.1))
        print(self.resources_at_percentile(0.5))
        print(self.resources_at_percentile(0.9))
        print(self.make_cdf())
        print(self.get_percentile_from_resources())


class Game(Player, Rolls):

    """
    TODO: need to connect the functions in Rolls to actually modify player.settlements
    """

    def __init__(self, players={}):
        """
        players: dict of named players
        """
        self.players = players
        self.rolls = []
        self.settlements = []
        self.settlements_resources = []

    def add_players(self, players):
        for k, v in players.items():
            self.players[k] = v

    def add_roll(self, roll):
        """
        adds dice rolls to list and increments up resources gained in settlements
        """
        self.add_roll_to_list(roll)
        for p in self.players.keys():
            self.players[p].settlements = list(map(lambda x: (x[0] + 1, x[1]), self.players[p].settlements))
            self.players[p].settlements_resources = list(map(lambda x: (x[0] + 1 if x[1] == roll else x[0], x[1]), self.players[p].settlements_resources))


















