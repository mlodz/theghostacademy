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



class Command(object):
    """
    * Standard Command
    <item_name> - This is simply the name of a unit, building, or research

    * Constant Command
    constant <unit_name> - Command to constantly produce this unit.
    stop constant <unit_name> - Command to stop producing these units

    * Refinery Command
    refinery 1 - Build a refinery, and set one scv on it when complete
    refinery 2 - Build a refinery, and set two scvs on it when complete
    refinery 3 - Build a refinery, and set three scvs on it when complete

    * Swap Command
    swap <building> and <building> - Lift off each building, and swap them. To change the attachment.
    # let's hold of on these next three
    # <attachment> on <building> - Build the attachment on a building (tech lab on factory)
    # remove <attachment> from <building> - Lift off the building and land it without the attachment.
    # add <attachment> to <building> - Lift off the building and land it on the attachment.

    * SCV Comman
    scv to gas - Send an scv to collect gas
    scv to minerals - Send an scv to collect minerals
    scv to scout - Send an scv to scout (effectively to do nothing)

    Any command can be prefixed with a number to indicate not to do this until supply has been reached.

    """

    wait_until_supply = None
    item = None

    def __init__(self, original_command):
        import re

        raw_command = original_command.lower().strip()

        # check for supply prefix
        found_supply = re.findall("^\d+", raw_command)
        if found_supply:
            ## Example: "10 - supply depot"
            self.supply = found_supply[0]
            # Remove the supply count, and whitespace
            raw_command.strip(self.supply).strip()
            # Remove an optional dash
            raw_command.strip("-").strip()
        else:
            self.supply = None

        if raw_command in ("scv to minerals", "scv to gas", "scv to scout"):
            # SCV COMMAND
            pass
        if raw_command in ("refinery 1", "refinery 2", "refinery 3"):
            # REFINERY COMMAND
            pass
        if raw_command in (self.all_units + self.all_buildings + self.all_research):
            # THIS IS A STANDARD COMMAND
            pass
        if raw_command.startswith(("constant", "stop constant")):
            # CONSTANT COMMAND
            pass

        pieces = raw_command.split()
        swappable = ["barracks", "factory", "starport"]
        if pieces[0] == 'swap' and \
                pieces[1] in swappable_buildings and \
                pieces[2] == 'and' and \
                pieces[3] in swappable_buildings:
            # SWAP COMMAND
            pass

        raise Exception("Could not parse command `%s`" % original_command)



import csv

def parse_dependency_file(filename):
    """Parse a data file containing dependencies.

    The input file is the following csv format:

        name,minerals,gas,build time,dependencies
        command center,400,0,100,
        orbital command,150,0,35,command center|barracks

    Notice that the "dependencies" column is a list, deliminated with |

    # TODO: We should lowercase everthing in this file
    # TODO: We should validate all names and dependencies are valid units/buildings/research
    # TODO: Should we store this stuff in memory rather than reading a file? Or memcache it?

    """

    reader = csv.DictReader(open(filename, 'rb'), delimiter=',', quotechar='"')
    data = list(reader) # Force to a list

    # Ensure values for these keys are integers
    int_keys = ['minerals', 'gas', 'supply', 'build time', 'research time']

    result = {}
    for line in data:
        # Change "thing1 |thing2 | thing3 " into ["thing1", "thing2", "thing3"]
        line['dependencies'] = [s.strip() for s in line['dependencies'].split("|") if s]

        for key in int_keys:
            if key in line:
                line[key] = int(line[key])

        result[line['name']] = line

    return result

