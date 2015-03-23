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
    attachments = []

    def __init__(self, build_order, facts):
        self.build_order = build_order
        self.facts = facts

        self.constant_commands = []

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
        if self.minerals_available < costs['minerals']:
            return False
        if self.gas_available < costs['gas']:
            return False

        # check if any prerequisites do not exist
        if any(not self.has_item(prereq) for prereq in costs['dependencies']):
            return False
        # check if there's enough supply
        if ('supply' in costs) \
                and self.supply_available < self.supply_used + costs['supply']:
            return False

        return True

    def has_item(self, item_name):
        """Return True iff the game has completed building the
        given name of a building, unit, or research.

        """
        return item_name in [b.name for b in self.buildings] or \
            item_name in [u.name for u in self.units] or \
            item_name in [r.name for r in self.research] or \
            item_name in [r.proper_name() for r in self.attachments]
            

        

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
            if not self.build_order:
                self.constant_commands = []
            self.tick()
            breaker -= 1
            if breaker <= 0:
                print "breaking...", self.time
                # TODO: if just waiting to complete last command, then this will raise exception
                self.print_report()
                raise Exception("Could not complete command: `%s`" % self.build_order[0].raw)
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

    # def impossible_build_sequence(self):
    #     """Your build order is out of order. For example, if you are building
    #     a barracks, but you haven't built a supply depot yet.

    #     * can't build a barrack before a supply depot
    #     * can't build a marine without a barrack
    #     * can't research stimpack without a barracks tech lab
    #     TODO: can't build a tech lab without a barrack/factory/starport

    #     """
    #     no_more_commands = not self.build_order
    #     # Can't be supply blocked if there are no more commands
    #     if no_more_commands:
    #         return False
        
    #     item_name = self.build_order[0].item_name
    #     dependencies = self.facts.dependencies(item_name)
    #     completed_items = [i.name for i in self.units + self.buildings + self.research]
    #     pending_items = self.in_progress()

    #     for dependency in dependencies:
    #         if dependency not in completed_items and \
    #                 dependency not in pending_items:
                
    #             print "completed items:", completed_items
    #             print "pending items:", pending_items
    #             print "dependency:", dependency
    #             raise DependencyError("Cannot build %s without first building a %s." % (item_name, dependency))
                                      

    def in_progress(self):
        items = [i for i in self.buildings + self.units if i.command_in_progress]
        return [i.command_in_progress['command'].item_name for i in items]

    def free_attachments(self):
        """Return a list of attachments that are not attached to anything"""
        return [a for a in self.attachments if a.attached_to is None]        

    def execute_build_command(self, build_command, skip_constants=False):
        # Save any ConstantCommands
        if build_command.is_constant():
            if build_command.begin:
                self.constant_commands.append(build_command.standard_command)
                return True
            else:
                # Find it's "begin" command and remove it
                print "TODO"
                return True


        # TODO: rotate, is this the best place to do it?
        # self.constant_commands.append(self.constant_commands.pop(0))
        # TODO: I want "constant scvs" to take priority over anything, but
        #       "constant marines" should not take priority over building other things
        # No, scv can't be highest priority, or else I can't build supply depot and get supply blocked

        ran_command = False

        # See if any buildings can execute this command
        if not ran_command and any((b.attempt_build_command(build_command) for b in self.buildings)):
            ran_command = True
            #return True

        # See if any unit can execute this command
        if not ran_command and any((u.attempt_build_command(build_command) for u in self.units)):
            ran_command = True
            #return True

        # See if any attachments can execute this command
        if not ran_command and any((a.attempt_build_command(build_command) for a in self.attachments)):
            ran_command = True
            #return True

        if skip_constants is False:
            import copy
            constant_commands = copy.deepcopy(self.constant_commands)
            while constant_commands and \
                    self.execute_build_command(constant_commands[0], skip_constants=True):
                constant_commands.pop(0)

        return ran_command

    def tick(self):
        # Every building, unit ticks one second
        previous_supply = self.supply_used
        [b.tick() for b in self.buildings]
        [u.tick() for u in self.units]
        [a.tick() for a in self.attachments]

        # Execute the build order as long as we are able
        while self.build_order and self.execute_build_command(self.build_order[0]):
            self.build_order.pop(0)


        self.is_supply_blocked()
        #self.impossible_build_sequence()

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
            or any([u.command_in_progress for u in self.units]) \
            or any([a.command_in_progress for a in self.attachments])


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
Freestanding Attachments:
  %(attachment_list)s
================================================================
"""
        from collections import Counter

        def format_item_list(items):
            item_counts = Counter([b.proper_name() for b in items]).items()
            item_counts = sorted(item_counts, key=lambda t: t[1], reverse=True)
            item_list = "\n  ".join(["%s %s" % (c, b) for b, c in item_counts])
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
                'attachment_list': format_item_list(self.free_attachments()),
                'time': self.format_time(),
        })

        report = report % params

        print "REPORT"
        print report


class TerranBuilding(object):

    name = "TERRAN BUILDING"
    command_in_progress = None
    attached_to = None

    def __init__(self, game, command=None):
        self.game = game

    def tick(self):
        pass


    def proper_name(self):
        if self.attached_to:
            name = "%s with %s" % (self.name, self.attached_to.name)
        else:
            name = self.name
        return name

    def attempt_build_command(self, command):
        """If we have the resources, requirements, and ability to execute this command,
        then do so and return True. Otherwise return False.

        """

        if self.attempt_swap_command(command):
            return True

        all_valid = self.game.facts.abilities[self.proper_name()]
        if command.item_name not in all_valid:
            #print "Cannot execute command, %s cannot be built by %s" % (command.item_name, self.__class__.__name__)
            return False

        # Cannot build an attachment if already has an attachment
        if command.is_attachment() and self.attached_to is not None:
            #print "Cannot execute command, %s cannot build attachment %s, already has attachment %s" % (self.name, command.item_name, self.attached_to.name)
            return False

        # Cannot build an attachment that's meant for a different building
        if command.is_attachment() and command.attached_to != self.name:
            # print "Cannot execute command, %s cannot build attachment meant for %s" % (self.name, command.attached_to)
            return False

        if not self.game.can_afford(command.item_name):
            # print "Cannot execute command %s, Cannot afford item" % command
            return False

        if self.command_in_progress is not None:
            # print "Cannot execute command %s, command already in progress." % command
            return False

        self.begin_command(command)
        return True

    def attempt_swap_command(self, command):
        """
        Can remove a building from an attachment iff
              1) building has attachment that is specified
              2) building does not have command_in_progress
              3) attachment does not have command_in_progress

         Can attach a building to an attachment iff
              1) building has no attachment
              2) building does not have command_in_progress
              3) the game has a free attachment that is specified
        """
        if not command.is_swap():
            return False

        if command.item_name != self.name:
            return False
        
        if self.command_in_progress is not None:
            return False

        if command.disconnect:
            # Remove <building> from <attachment>
            if self.attached_to is not None and self.attached_to.name == command.attachment_name :
                if self.attached_to.command_in_progress is None:
                    attachment = self.attached_to
                    self.attached_to = None
                    attachment.attached_to = None
                    return True
        else:
            # Move <building> onto <attachment>
            if self.attached_to is None:
                free_attachments = [a for a in self.game.free_attachments() 
                                    if a.name == command.attachment_name and \
                                        a.command_in_progress is None]
                for a in self.game.attachments:
                    print a.name, a.attached_to
                if free_attachments:
                    free = free_attachments[0]
                    free.attached_to = self
                    self.attached_to = free
                    return True

        return False

    def begin_command(self, command):
        """Buildings can construct units and attachments.
        """
        item_name = command.item_name
        cost = self.game.facts.cost(item_name)
        self.command_in_progress = dict(
            command=command,
            time=self.game.time + cost['build time'],
        )
        print "     %s BEGIN %s (%s)" % (self.name, item_name.upper(), self.game.time)
        self.game.spend(
            minerals=cost['minerals'],
            gas=cost['gas'],
            supply_used=cost.get('supply', 0),
        )

    def complete_command(self, command_in_progress):
        command = command_in_progress['command']

        item_name = command.item_name
        print "     %s COMPLETE %s (%s)" % (self.name, item_name.upper(), self.game.time)
        self.command_in_progress = None

        # When a building builds a building, it's an attachment
        is_attachment = self.game.facts.is_building(item_name)

        new_item = create_item_from_name(item_name, self.game, command=command, is_attachment=is_attachment)

        if is_attachment:

            #..... should be creating an instance of TerranBuildingAttachment...

            self.attached_to = new_item
            new_item.attached_to = self
            self.game.attachments.append(new_item)
        else:
            print "appending %s to units" % new_item
            
            # TODO THIS IS WHERE ITS BROKEN, adding research STIMPACK to units
            # should `create_item_from_name` return an item_type as well?
            # or should we use is_building()/is_attachment()/is_research() methods?
            # is an attachment a building as well? 

            self.game.units.append(new_item)

    def tick(self):
        """If something is building, then check if it's done?
        """
        if self.command_in_progress and self.command_in_progress['time'] <= self.game.time:
            #self.complete_scv(self.command_in_progress['command']) # TODO generalize this
            self.complete_command(self.command_in_progress)

    def is_attachment(self):
        return False


class TerranBuildingAttachment(TerranBuilding):

    name = "TERRAN ATTACHMENT"

    def proper_name(self):
        name = self.name
        if self.attached_to:
            name = "%s on %s" % (self.name, self.attached_to.name)
        return name

# class TechLab(TerranBuilding):

#     attached_to = None

#     def is_attachment(self):
#         return True


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
    name = "command center"
    # command_in_progress = None

    # def __init__(self, game, command=None):
    #     self.game = game


class TerranResearch(object):
    name = "TERRAN RESEARCH"
    def __init__(self, game, command=None):
        self.game = game

class TerranUnit(object):
    name = "TERRAN UNIT"
    command_in_progress = None

    def __init__(self, game, command=None):
        self.game = game

    def proper_name(self):
        return self.name

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

        all_valid = self.game.facts.abilities[self.proper_name()]
        if command.item_name not in all_valid:
            #print "Cannot execute command, %s cannot be built by %s" % (command.item_name, self.__class__.__name__)
            return False

        if not isinstance(command, commands.StandardCommand): # TODO: don't do this
            #print "Cannot execute command %s, not a standard command" % command
            return False

        # # and scv can only build buildings
        # # REPLACE THIS condition with ability check
        # if not self.game.facts.is_building(command.item_name):
        #     #print "Cannot execute command %s, scv can only build buildings." % command
        #     return False

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
        print "     scv BEGIN %s (%s)" % (building_name.upper(), self.game.format_time())
        self.game.spend(
            minerals=self.game.facts.buildings[building_name]['minerals'],
            gas=self.game.facts.buildings[building_name]['gas'],
        )

    def complete_command(self, command_in_progress):
        """Complete the construction of a building and add it to the game.
        """
        command = command_in_progress['command']
        building_name = command.item_name
        print "     scv COMPLET", building_name.upper()
        self.collection_type = self.MINERALS # TODO: minerals or gas?
        self.command_in_progress = None

        new_building = create_item_from_name(building_name, self.game, command=command)
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

def create_item_from_name(name, *args, **kwargs):
    game =  args[0]

    is_attachment = kwargs.get('is_attachment', False)
    if 'is_attachment' in kwargs:
        del kwargs['is_attachment']

    if is_attachment:
        attachment = TerranBuildingAttachment(game)
        attachment.name = name
        return attachment
    elif game.facts.is_building(name):
        return create_building_from_name(name, *args, **kwargs)
    elif game.facts.is_unit(name):
        return create_unit_from_name(name, *args, **kwargs)
    elif game.facts.is_research(name):
        return create_research_from_name(name, *args, **kwargs)
    else:
        raise Exception("Cannot determine item type:", name)

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

def create_research_from_name(name, *args, **kwargs):
    research = TerranResearch(*args, **kwargs)
    research.name =  name
    return research

build_name_map()

