"""This file contains notes and code that I don't really want to put anywhere yet.
"""




class Game(object):

    def can_afford(self, item_name):
        """Return True iff the game has the minerals, gas, supply, and prerequisites
        to build the given unit, building, or research.
        """
        costs = self.costs[item_name]
        game = self.game

        # check if has gas, minerals
        if game.minerals >= costs['minerals'] and game.gas >= costs['gas']:
            # check if prefrequisite unit exists
            if all(game.has_item(prereq) for prereq in costs['dependencies']):
                # check if there's enough supply
                if ('supply' not in costs) or game.used_supply + costs['supply'] <= game.total_supply:
                    return True

        return False


    def has_item(self, item_name):
        """Return True iff the game has completed building the
        given name of a building, unit, or research.

        """
        return item_name in [b.name for b in self.buildings] or \
            item_name in [u.name for u in self.units] or \
            item_name in [r.name for r in self.research]


