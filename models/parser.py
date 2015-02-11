import csv
import re

import commands

def parse_build_order_file(filename, dependencies):
    """Takes a filename, and creates a list of commands.
    """
    lines = open(filename).readlines()
    return [parse_line(line, dependencies) for line in lines]


def parse_line(text_line, dependencies):
    """Take a raw piece of text, and return a command.

    "10 - supply depot"
    "barracks"
    
    """
    raw_command = text_line.lower().strip()
    supply = None

    # check for supply prefix
    found_supply = re.findall("^\d+", raw_command)
    if found_supply:
        ## Example: "10 - supply depot"
        supply = found_supply[0]
        # Remove the supply count, and whitespace
        raw_command.strip(supply).strip()
        # Remove an optional dash
        raw_command.strip("-").strip()


    if raw_command in ("scv to minerals", "scv to gas", "scv to scout"):
        # SCV COMMAND
        command = commands.ScvCommand(supply, raw_command, raw_command)
        if raw_command.endswith('minerals'):
            command.collect_minerals = True
        elif raw_command.endswith('gas'):
            command.collect_minerals = True
        elif raw_command.endswith('scout'):
            command.scout = True
        else:
            raise Exception("Could not parse scv command `%s`" % text_line)

        return command

    if raw_command in ("refinery", "refinery 1", "refinery 2", "refinery 3"):
        # REFINERY COMMAND
        command = commands.RefineryCommand(supply, text_line)
        command.scv_for_gas = 1 # TODO
        return command

    if raw_command in dependencies.all_item_names():
        # THIS IS A STANDARD COMMAND
        command = commands.StandardCommand(supply, raw_command)
        command.item_name = raw_command
        return command

    # TODO
    # if raw_command.startswith(("constant", "stop constant")):
    #     # CONSTANT COMMAND
    #     pass

    # TODO
    # pieces = raw_command.split()
    # swappable = ["barracks", "factory", "starport"]
    # if pieces[0] == 'swap' and \
    #         pieces[1] in swappable_buildings and \
    #         pieces[2] == 'and' and \
    #         pieces[3] in swappable_buildings:
    #     # SWAP COMMAND
    #     pass

    raise Exception("Could not parse command `%s`" % text_line)


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



