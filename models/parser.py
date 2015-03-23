import csv
import re

import commands


def parse_build_order_file(filename, facts):
    """Takes a filename, and creates a list of commands.
    """
    lines = open(filename).readlines()
    commands =  [parse_line(line, facts) for line in lines]
    # TODO: Some lines are not turned into commands (blank line, comments) so let's filter them out
    return [c for c in commands if c is not None]




def parse_line(text_line, facts):
    """Take a raw piece of text, and return a command.

    "10 - supply depot"
    "barracks"
    
    """
    raw_command = text_line.lower().strip()
    supply = None

    if raw_command.startswith("#"):
        # This line we are trying to parse is a comment
        return None # TODO: create a CommentCommand class?
    if raw_command.strip() == '':
        # Ignore any lines that are just whitespace
        return None

    # check for supply prefix
    found_supply = re.findall("^\d+", raw_command)
    if found_supply:
        ## Example: "10 - supply depot"
        supply = found_supply[0]
        # Remove the supply count, and whitespace
        raw_command.strip(supply).strip()
        # Remove an optional dash
        raw_command.strip("-").strip()


    # TODO: should this be in a data file?
    ATTACHMENT_LINES = [
        "tech lab on barracks",
        "tech lab on factory",
        "tech lab on starport",
        "reactor on barracks",
        "reactor on factory",
        "reactor on starport",
        "planetary fortress",
        "orbital command",
    ]
    if raw_command in ATTACHMENT_LINES:
        pieces = raw_command.split(" on ")
        if len(pieces) == 2:
            attachment, building = pieces
        elif len(pieces) == 1:
            attachment = pieces[0]
            building = "command center"
        else:
            raise Exception("Could not parse scv command `%s`" % raw_command)
        return commands.AttachmentCommand(
            supply,
            attachment,
            raw_command,
            attached_to=building,
        )
            

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
            raise Exception("Could not parse scv command `%s`" % text_line.strip())

        return command

    if raw_command in ("refinery", "refinery 1", "refinery 2", "refinery 3", "refinery 0"):
        # REFINERY COMMAND
        default_scv_transfer = 3
        scv_transfer = raw_command.strip('refinery ')
        scv_transfer = int(scv_transfer) if scv_transfer else default_scv_transfer
        command = commands.RefineryCommand(
            supply, 
            'refinery',
            raw_command,
            scv_transfer=scv_transfer,
        )
        return command

    if raw_command in facts.all_item_names():
        # THIS IS A STANDARD COMMAND
        item_name = raw_command
        command = commands.StandardCommand(
            supply,
            item_name,
            raw_command,
        )
        return command

    # TODO
    
    """
    Constant Commands are like:
        constant scvs
        stop constant scvs
    """

    if raw_command.startswith("constant"):
        unit_name = raw_command[8:].strip()
        all_names = facts.unit_names()
        print "unit name:", unit_name, all_names
        if unit_name in all_names:
            return commands.ConstantCommand(
                supply,
                unit_name,
                raw_command,
                begin=True,
            )
        
        # Try taking off an "s", may be plural
        unit_name = unit_name.rstrip("s")
        if unit_name in all_names:
            return commands.ConstantCommand(
                supply,
                unit_name,
                raw_command,
                begin=True,
            )


    # TODO: implement "stop constant scv" command
    #elif raw_command.startswith("stop constant"):
        

    """

    Swap Commands are like:
        remove barracks from tech lab
        move barracks onto tech lab

    """
    buildings = ['barracks', 'factory', 'starport']
    attachments = ['tech lab', 'reactor']
    swap_commands = \
        ["remove %s from %s" % (b, a) for b in buildings for a in attachments] + \
        ["move %s onto %s" % (b, a) for b in buildings for a in attachments]
    
    if raw_command in swap_commands:
        # Ugh, special case because 'tech lab' is two words
        if "tech lab" in raw_command:
            action, building = raw_command.split()[0:2]
            attachment = "tech lab"
        else:
            action, building, word, attachment = raw_command.split()
            
        return commands.SwapCommand(
            supply,
            building,
            raw_command,
            attachment_name=attachment,
            disconnect=bool(action == 'remove')
        )


    # TODO
    # pieces = raw_command.split()
    # swappable = ["barracks", "factory", "starport"]
    # if pieces[0] == 'swap' and \
    #         pieces[1] in swappable_buildings and \
    #         pieces[2] == 'and' and \
    #         pieces[3] in swappable_buildings:
    #     # SWAP COMMAND
    #     pass

    raise Exception("Could not parse command `%s`" % text_line.strip())


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


def parse_building_ability_file(filename):
    """Parse a data file containing building abilities (can build researhc, units, attachments)
    """

    with open(filename, 'rb') as csvfile:
        lines = csv.reader(csvfile, delimiter=',', quotechar='"')
        data = {}
        for line in lines:
            abilities = [a.lower().strip() for a in line[1:] if a]
            building = line[0].lower().strip()
            data[building] = abilities
        return data


