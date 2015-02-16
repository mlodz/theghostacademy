import commands

class StarcraftException(Exception):
    """An exception specific to this codebase."""

class SupplyBlocked(StarcraftException):
    """This build has become supply blocked."""

class DependencyError(StarcraftException):
    """This build is attempting to build an item without first building its dependency"""

class HotsGame(object):
    """The game engine."""

    time = 0

    minerals_available = 50 # TODO: FACT CHECK
    gas_available = 0
    supply_available = 11 # TODO: FACT CHECK
    supply_used = 0

    build_order = None
    facts = None

    units = []
    buildings = []
    research = []

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
        breaker = 60*15 # Prevent an infinite loop by breaking at this time
        self.print_progress_line()
        while self.build_order or self.anything_in_progress():
            self.tick()
            breaker -= 1
            if breaker <= 0:
                print "breaking...", self.time
                break

        self.print_report()

        return self

    def is_supply_blocked(self):
        no_supply_available = self.supply_available - self.supply_used <= 0
        # are any scv building supply depots?
        running_commands = [u.command_in_progress['command'] 
                            for u in self.units if u.command_in_progress and u.name == 'scv']
        supply_in_progress = any([c.item_name == 'supply depot' for c in running_commands])

        no_more_commands = not self.build_order
        # Can't be supply blocked if there are no more commands
        if no_more_commands:
            return False

        # Is supply depot the next command?
        next_command_is_supply = self.build_order[0].item_name == 'supply depot'

        if no_supply_available and not supply_in_progress and not next_command_is_supply:
            raise SupplyBlocked()

        return False

    def impossible_build_sequence(self):
        """Your build order is out of order. For example, if you are building
        a barracks, but you haven't built a supply depot yet.

        * can't build a barrack before a supply depot
        * can't build a marine without a barrack
        * can't research stimpack without a barracks tech lab
        TODO: can't build a tech lab without a barrack/factory/starport

        """
        no_more_commands = not self.build_order
        # Can't be supply blocked if there are no more commands
        if no_more_commands:
            return False
        
        item_name = self.build_order[0].item_name
        dependencies = self.facts.dependencies(item_name)
        completed_items = [i.name for i in self.units + self.buildings + self.research]
        pending_items = self.in_progress()

        for dependency in dependencies:
            if dependency not in completed_items and \
                    dependency not in pending_items:
                
                raise DependencyError("Cannot build %s without first building a %s." % (item_name, dependency))
                                      

    def in_progress(self):
        items = [i for i in self.buildings + self.units if i.command_in_progress]
        return [i.command_in_progress['command'].item_name for i in items]

    def tick(self):
        # Every building, unit ticks one second
        previous_supply = self.supply_used
        [b.tick() for b in self.buildings]
        [u.tick() for u in self.units]
        if self.build_order:
            build_command = self.build_order[0]

            # See if any buildings can run the command
            while self.build_order and any((b.attempt_build_command(build_command) for b in self.buildings)):
                self.build_order.pop(0)
                if self.build_order:
                    build_command = self.build_order[0]

            # See if any units (scv) can run the command
            while self.build_order and any((u.attempt_build_command(build_command) for u in self.units)):
                self.build_order.pop(0)
                if self.build_order:
                    build_command = self.build_order[0]

            # Either there are no more build commands, or the buildings could not run a build_command

        self.is_supply_blocked()
        self.impossible_build_sequence()

        # if self.time % 10 == 0:
        #     #print "pending commands:", [o.item_name for o in self.build_order]
        #     print "[%s] (M: %s, G: %s, S:% s/%s)" % (
        #         self.time,
        #         self.minerals_available,
        #         self.gas_available,
        #         self.supply_used,
        #         self.supply_available,
        #     )

        if self.supply_used != previous_supply:
            self.print_progress_line()

        self.time += 1

    def print_progress_line(self):
        print "[%s/%s] (T: %s, M: %s, G: %s)" % (
            self.supply_used,
            self.supply_available,
            self.format_time(),
            self.minerals_available,
            self.gas_available,
        )

    def format_time(self):
        minutes = self.time / 60
        seconds = self.time % 60
        return "%s:%02d" % (minutes, seconds)

    def anything_in_progress(self):
        return any([b.command_in_progress for b in self.buildings]) \
            or any([u.command_in_progress for u in self.units])


    def print_report(self):
        
        report =  """
================================================================
Time: %(time)s    Minerals: %(minerals_available)s    Gas: %(gas_available)s    Supply: %(supply_used)s / %(supply_available)s
Buildings:
  %(building_list)s
Units:
  %(unit_list)s
Research:
  %(research_list)s
================================================================
"""
        from collections import Counter

        def format_item_list(items):
            item_counts = Counter([b.name for b in items]).items()
            item_counts = sorted(item_counts, key=lambda t: t[1], reverse=True)
            item_list = "\n  ".join(["%s %s" % (c, b.capitalize()) for b, c in item_counts])
            if item_counts:
                return item_list
            else:
                return "None"


        params = {}
        params.update(self.__dict__)
        params.update({
                'building_list': format_item_list(self.buildings),
                'unit_list': format_item_list(self.units),
                'research_list': format_item_list(self.research),
                'time': self.format_time(),
        })

        report = report % params

        print "REPORT"
        print report


class TerranBuilding(object):

    name = "TERRAN BUILDING"
    command_in_progress = None

    def __init__(self, game, command=None):
        self.game = game

    def tick(self):
        pass

    def attempt_build_command(self, command):
        """If we have the resources, requirements, and ability to execute this command,
        then do so and return True. Otherwise return False.

        """
        if not isinstance(command, commands.StandardCommand): # TODO: don't do this
            #print "Cannot execute command %s, not a standard command" % command
            return False

        all_valid = self.game.facts.abilities[self.name]
        if command.item_name not in all_valid:
            #print "Cannot execute command, %s cannot be built by %s" % (command.item_name, self.__class__.__name__)
            return False

        if not self.game.can_afford(command.item_name):
            #print "Cannot execute command %s, Cannot afford item" % command
            return False

        if self.command_in_progress is not None:
            #print "Cannot execute command %s, command already in progress." % command
            return False

        self.begin_command(command)
        return True

    def begin_command(self, command):
        #getattr(self, "begin_%s" % command.run_name())(command)
        item_name = command.item_name
        self.command_in_progress = dict(
            command=command,
            time=self.game.time + self.game.facts.units[item_name]['build time'],
        )
        print "     BEGIN", item_name.upper()
        cost = self.game.facts.cost(item_name)
        self.game.spend(
            minerals=cost['minerals'],
            gas=cost['gas'],
            supply_used=cost['supply'],
        )


    def complete_command(self, command_in_progress):
        command = command_in_progress['command']
        # getattr(self, "complete_%s" % command.run_name())(command)

        item_name = command.item_name
        print "     COMPLETE", item_name.upper()
        self.command_in_progress = None

        self.game.units.append(create_unit_from_name(item_name, self.game, command=command))

    def tick(self):
        """If something is building, then check if it's done?
        """
        if self.command_in_progress and self.command_in_progress['time'] <= self.game.time:
            #self.complete_scv(self.command_in_progress['command']) # TODO generalize this
            self.complete_command(self.command_in_progress)


class SupplyDepot(TerranBuilding):
    name = 'supply depot'
    
    def __init__(self, game, command=None):
        super(SupplyDepot, self).__init__(game)
        self.game.earn(supply_available=10)


class Refinery(TerranBuilding):
    name = 'refinery'

    def __init__(self, game, command=None):
        super(Refinery, self).__init__(game)

        if command.scv_transfer > 0:
            # Move scv to collect gas
            available_scv = [u for u in self.game.units if isinstance(u, Scv) and u.is_free_to_collect_gas()]
            # Grab workers at the end of the list; last to pull to build something
            transfer_scv = available_scv[command.scv_transfer*-1:]
            [scv.collect_gas() for scv in transfer_scv]


class CommandCenter(TerranBuilding):
    """
    A building has
    
    a list of units it can build
    a list of research it can perform
    a production in progress (or None)
    a time when an action will be complete (finished building a unit, finish building attachment, finish research)

    """

    name = "command center"
    command_in_progress = None

    def __init__(self, game, command=None):
        self.game = game


class TerranUnit(object):
    name = "TERRAN UNIT"
    command_in_progress = None

    def __init__(self, game, command=None):
        self.game = game

    def tick(self):
        pass

    def attempt_build_command(self, command):
        """Return True iff we have the resources, requirements, and ability to execute this command.

        Really, only workers can execute build commands, so we'll return False.
        """
        return False


class Scv(TerranUnit):
    """A terran worker. Collects minerals or gas.
    
    HotS - 34 minerals per 60 seconds for 1 scv (0.56m/s)
        "From 0 to 2 SCVs/patch, each additional SCV adds ~39-45 minerals/game minute."
        42 minerals / 60s = 0.700 m/s

        "A base with 8 mineral patches will yield ~672 minerals/min with 16 SCVs, or ~816 minerals with 24 SCVs."
        0.700 m/s, or 0.566 m/s


    """
    name = "scv"

    MINERALS = 'minerals'
    GAS = 'gas'

    # TODO: FACT CHECK
    mineral_collection_rate = 0.700 # minerals/second, valid until 16 active scvs
    minerals_per_trip = 5
    minerals_queued = 0

    #Each of the three workers on a single geyser will collect approximately 38 gas per minute, with saturation at approximately 114 gas/min.
    # TODO: FACT CHECK
    gas_collection_rate = 38.0/60.0 # gas/second, valid until 3 workers per refinery
    gas_per_trip = 4
    gas_queued = 0

    collection_type = None # either Gas or Minerals
    command_in_progress = None

    def __init__(self, game, command=None):
        super(Scv, self).__init__(game)
        self.collection_type = self.MINERALS

    def collect_minerals(self):
        if self.command_in_progress:
            raise Exception("SCV has command in progress, cannot collect minerals.")
        self.collection_type = self.MINERALS

    def collect_gas(self):
        if self.command_in_progress:
            raise Exception("SCV has command in progress, cannot collect gas.")
        self.collection_type = self.GAS

    def __repr__(self):
        return "<SCV %s>" % (self.collection_type or ("CONSTRUCTION" if self.command_in_progress else "None"))
        print "DICT:", self.__dict__
        return "(SCV %(collection_type)s queued=%(minerals_queued)s)" % self.__dict__

    def tick(self):
        super(Scv, self).tick()
        if self.collection_type == self.MINERALS:
            self.game.earn(minerals=self._collect_minerals())
        elif self.collection_type == self.GAS:
            self.game.earn(gas=self._collect_gas())

        if self.command_in_progress and self.command_in_progress['time'] <= self.game.time:
            self.complete_command(self.command_in_progress)

    def _collect_minerals(self):
        """Return the number of minerals collected this second.

        TODO: add some kind of random delay to make more realistic?
        TODO: FACT CHECK, make sure this approximation is accurate enough
        """
        self.minerals_queued += self.mineral_collection_rate

        minerals_collected = 0
        if self.minerals_queued >= self.minerals_per_trip:
            minerals_collected = self.minerals_per_trip
            self.minerals_queued -= self.minerals_per_trip

        return minerals_collected

    def _collect_gas(self):
        """Return the amount of gas collected this second.

        TODO: add some kind of random delay to make more realistic?
        TODO: FACT CHECK, make sure this approximation is accurate enough
        """
        self.gas_queued += self.gas_collection_rate

        gas_collected = 0
        if self.gas_queued >= self.gas_per_trip:
            gas_collected = self.gas_per_trip
            self.gas_queued -= self.gas_per_trip

        return gas_collected

    def is_free_to_collect_gas(self):
        return bool(self.collection_type == self.MINERALS)

    def is_free_to_collect_minerals(self):
        return bool(self.collection_type == self.GAS)

    def attempt_build_command(self, command):
        """Return True iff we have the resources, requirements, and ability to execute this command."""
        if not isinstance(command, commands.StandardCommand): # TODO: don't do this
            #print "Cannot execute command %s, not a standard command" % command
            return False

        # and scv can only build buildings
        if not self.game.facts.is_building(command.item_name):
            #print "Cannot execute command %s, scv can only build buildings." % command
            return False

        if not self.game.can_afford(command.item_name):
            #print "Cannot execute command %s, Cannot afford item" % command
            return False

        if self.command_in_progress is not None:
            #print "Cannot execute command %s, command already in progress." % command
            return False

        self.begin_command(command)
        return True

    def begin_command(self, command):
        """Stop collecting resources and begin constructing a building.
        """
        self.collection_type = None # Pause resource collection
        building_name = command.item_name
        self.command_in_progress = dict(
            command=command,
            time=self.game.time + self.game.facts.buildings[building_name]['build time'],
        )
        print "     BEGIn", building_name.upper(), command
        self.game.spend(
            minerals=self.game.facts.buildings[building_name]['minerals'],
            gas=self.game.facts.buildings[building_name]['gas'],
        )

    def complete_command(self, command_in_progress):
        """Complete the construction of a building and add it to the game.
        """
        command = command_in_progress['command']
        building_name = command.item_name
        print "     COMPLETe", building_name.upper()
        self.collection_type = self.MINERALS # TODO: minerals or gas?
        self.command_in_progress = None

        new_building = create_building_from_name(building_name, self.game, command=command)
        self.game.buildings.append(new_building)

NAME_TO_CLASS_MAP = {}
import sys
import inspect
def build_name_map():
    """We need to map item_names to their classes.
    For example, from string 'scv' we need to get class Scv. And
    from 'supply depot' we need to get class SupplyDepot.
    """
    current_module = sys.modules[__name__]
    for something, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj):
            if hasattr(obj, 'name'):
                name = getattr(obj, 'name')
                NAME_TO_CLASS_MAP[name] = obj

def create_unit_from_name(name, *args, **kwargs):
    class_name = NAME_TO_CLASS_MAP.get(name, None)
    if class_name is None:
        instance = TerranUnit(*args, **kwargs)
        instance.name = name
    else:
        instance = class_name(*args, **kwargs)

    return instance

def create_building_from_name(name, *args, **kwargs):
    class_name = NAME_TO_CLASS_MAP.get(name, None)
    if class_name is None:
        instance = TerranBuilding(*args, **kwargs)
        instance.name = name
    else:
        instance = class_name(*args, **kwargs)

    return instance

build_name_map()

