from utils import Player, Rolls, Game


# instantiate Players and Game
rolls = Rolls()
players = {'p1': Player(rolls), 'p2': Player(rolls)}
g1 = Game(players)

# add starting settlements
g1.players['p1'].add_settlements([3,8,11])
g1.players['p1'].add_settlements([6,4,12])
g1.players['p2'].add_settlements([3,4,9])
g1.players['p2'].add_settlements([9,5,10])

# roll some dice
g1.add_roll(6)
g1.add_roll(5)
g1.add_roll(11)
g1.add_roll(6)

# add another settlement
g1.players['p1'].add_settlements([8,9,10])

# roll some more dice
g1.add_roll(8)
g1.add_roll(10)

# check that percentile functions work
g1.players['p1'].get_percentile_from_resources_exact(2)
g1.players['p1'].get_percentile_from_resources_poibin(2)

# check that each players rolls are incremented up
print(g1.players['p1'].settlements)
print(g1.players['p2'].settlements)

# adding another settlement for player 1
g1.players['p1'].add_settlements([6,10])

# adding more rolls
g1.add_roll(6)
g1.add_roll(2)
g1.add_roll(3)
g1.add_roll(9)

# check again that each players settlements are incremented up for each roll they held a number
print(g1.players['p1'].settlements)
print(g1.players['p2'].settlements)

# check that player actually received resources
print(g1.players['p1'].settlements_resources)
print(g1.players['p2'].settlements_resources)

# check that this method calculating dice roll probabilities works
print(g1.players['p1'].settlements_prob())

# what turn are we on?
g1.get_turn_number()

# what's happened?
g1.print_get_roll_history()

#############################
# Let's get some statistics #
#############################

# estimated # of resources
print(g1.players['p1'].expected_resources_count())
print(g1.players['p2'].expected_resources_count())

# actual # of resources received
print(g1.players['p1'].resources_count())
print(g1.players['p2'].resources_count())

# how many resources expected at 90th percentile
print(g1.players['p1'].resources_at_percentile(0.1))
print(g1.players['p1'].resources_at_percentile(0.5))
print(g1.players['p1'].resources_at_percentile(0.9))

# make CDF for player 1
g1.players['p1'].make_cdf(step=.05)

# given current resources, what percentile am i in?
g1.players['p2'].get_percentile_from_resources()

# given current resources, what percentile am i in ... using the poisson binomial?
g1.players['p1'].get_percentile_from_resources_poibin()



