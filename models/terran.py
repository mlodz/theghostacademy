import commands

MINERALS = 'minerals'
GAS = 'gas'

class HotsGame(object):
    """The game engine."""

    time = 0

    minerals_available = 50 # FACT CHECK
    gas_available = 0
    supply_available = 11 # FACT CHECK
    supply_used = 0

    build_order = None
    facts = None

    units = []
    buildings = []

    def __init__(self, build_order, facts):
        self.build_order = build_order
        self.facts = facts

        self.buildings = [CommandCenter(self)]
        initial_scv_count = 5
        for i in range(initial_scv_count):
            self.units.append(Scv(self))
            self.spend(supply_used=1)


    def __repr__(self):
        return "\t\t\t<Hots Game: %s minerals, %s gas, %s/%s supply, %s units>" % (
            self.minerals_available,
            self.gas_available,
            self.supply_used,
            self.supply_available,
            len(self.units),
        )
    
    def can_afford(self, item_name):
        """Return True iff the game has the minerals, gas, supply, and prerequisites
        to build the given unit, building, or research.
        """
        costs = self.facts.cost(item_name)

        # check if has gas, minerals
        if self.minerals_available >= costs['minerals'] \
                and self.gas_available >= costs['gas']:
            # check if prefrequisite unit exists
            if all(self.has_item(prereq) for prereq in costs['dependencies']):
                # check if there's enough supply
                if ('supply' not in costs) \
                        or self.supply_used + costs['supply'] <= self.supply_available:
                    return True

        return False

    def has_item(self, item_name):
        """Return True iff the game has completed building the
        given name of a building, unit, or research.

        """
        return item_name in [b.name for b in self.buildings] or \
            item_name in [u.name for u in self.units] or \
            item_name in [r.name for r in self.research]

        

    def earn(self, minerals=0, gas=0, supply_used=0, supply_available=0):
        self.minerals_available += minerals
        self.gas_available += gas
        self.supply_available += supply_available
        self.supply_used += supply_used

    def spend(self, minerals=0, gas=0, supply_used=0, supply_available=0):
        self.minerals_available -= minerals
        self.gas_available -= gas
        self.supply_available += supply_available
        self.supply_used += supply_used


    def run(self):
        print "Running."
        breaker = 60
        while self.build_order:
            self.tick()
            breaker -= 1
            if breaker <= 0:
                print "breaking..."
                break
        print "Finished."
        return self

    def tick(self):
        # Every building, unit ticks one second
        [b.tick() for b in self.buildings]
        [u.tick() for u in self.units]
        if self.build_order:
            build_command = self.build_order[0]
            while self.build_order and any((b.attempt_build_command(build_command) for b in self.buildings)):
                self.build_order.pop(0)
                print "Ran command: %s" % build_command
            # Either there are no more build commands, or the buildings could not run a build_command

        print "[%s] (%s) - %s" % (self.time, self.minerals_available, self.build_order)
        print " "
        self.time += 1


class SupplyDepot(object):
    commands = []
    name = 'supply depot'

    

class CommandCenter(object):
    """
    A building has
    
    a list of units it can build
    a list of research it can perform
    a production in progress (or None)
    a time when an action will be complete (finished building a unit, finish building attachment, finish research)

    """
    valid_units = ['scv']
    valid_buildings = []
    valid_research = ['...', '...', '...']
    valid_attachments = ['orbital command', 'planetary fortress']

    name = "command center"
    command_in_progress = None

    def __init__(self, game):
        self.game = game
        self.valid_units_to_build = [Scv]

    def begin_scv(self):
        # TODO: use a dict, or object, not a tuple
        unit_name = 'scv'
        self.command_in_progress = (
            unit_name,
            self.game.time + self.game.facts.units[unit_name]['build time'],
        )
        print "BEGIN SCV", self.command_in_progress
        self.game.spend(
            minerals=self.game.facts.units[unit_name]['minerals'],
            gas=self.game.facts.units[unit_name]['gas'],
            supply_used=self.game.facts.units[unit_name]['supply'],
        )

        pass

    def complete_scv(self):
        print "COMPLETE SCV"
        self.command_in_progress = None
        self.units.append(Scv(self))


    def attempt_build_command(self, command):
        """Return True iff we have the resources, requirements, and ability to execute this command."""
        if not isinstance(command, commands.StandardCommand): # TODO: don't do this
            print "Cannot execute command %s, not a standard command" % command
            return False

        all_valid = self.valid_units + self.valid_buildings + self.valid_research + self.valid_attachments
        if command.item_name not in all_valid:
            print "Cannot execute command %s, Cannot be built by Command Center" % command
            return False

        if not self.game.can_afford(command.item_name):
            print "Cannot execute command %s, Cannot afford item" % command
            return False

        if self.command_in_progress is not None:
            print "Cannot execute command %s, command already in progress." % command
            return False

        self.run_command(command)
        return True

    def run_command(self, command):
        getattr(self, "begin_%s" % command.run_name())()

    def tick(self):
        """If something is building, then check if it's done?
        """
        if self.command_in_progress and self.command_in_progress[1] <= self.game.time:
            self.complete_scv()

                                 

class TerranBuilding(object):
    def tick(self):
        """Performs a command for this second."""

    def attempt_build_command(self, build_command):
        """Runs the build_command if it's able. Returns True iff it's able."""


class Scv(object):
    """A terran worker. Collects minerals or gas.
    
    HotS - 34 minerals per 60 seconds for 1 scv (0.56m/s)
        "From 0 to 2 SCVs/patch, each additional SCV adds ~39-45 minerals/game minute."
        42 minerals / 60s = 0.700 m/s

        "A base with 8 mineral patches will yield ~672 minerals/min with 16 SCVs, or ~816 minerals with 24 SCVs."
        0.700 m/s, or 0.566 m/s


    """
    name = "scv"

    mineral_cost = 50
    gas_cost = 0
    supply_cost = 1
    time_cost = 17

    mineral_collection_rate = 0.700 # minerals/second, valid until 16 active scvs

    minerals_per_trip = 5
    minerals_queued = 0

    collection_type = None # either Gas or Minerals

    def __init__(self, game):
        self.game = game
        self.collection_type = MINERALS

    def __str__(self):
        return "(SCV %(collection_type)s queued=%(minerals_queued)s)" % self.__dict__

    def tick(self):
        if self.collection_type == MINERALS:
            self.game.earn(minerals=self.collect_minerals())
        elif self.collection_type == GAS:
            self.game.earn(gas=self.collect_gas())
        return False

    def collect_minerals(self):
        """Return the number of minerals collected this second."""
        self.minerals_queued += self.mineral_collection_rate

        minerals_collected = 0
        if self.minerals_queued >= self.minerals_per_trip:
            minerals_collected = self.minerals_per_trip
            self.minerals_queued -= self.minerals_per_trip

        return minerals_collected

    def collect_gas(self):
        return 0
