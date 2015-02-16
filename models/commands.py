"""This file parses commands and dependency files.

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

    * SCV Command
    scv to gas - Send an scv to collect gas
    scv to minerals - Send an scv to collect minerals
    scv to scout - Send an scv to scout (effectively to do nothing)

    Any command can be prefixed with a number to indicate not to do this until supply has been reached.

"""

import re


class Command(object):

    def __init__(self, supply, item_name, raw_text):
        self.supply = supply
        self.item_name = item_name
        self.raw = raw_text

    def __repr__(self):
        return "<%s: %s>" % (
            self.__class__.__name__,
            self.item_name,
        )


class StandardCommand(Command):
    """Command to build a building, unit, attachment, or research."""
    item_name = None

    def run_name(self):
        """Return the item name, but remove spaces and other non-letter characters."""
        return re.sub("[^\w]", "", self.item_name)


class RefineryCommand(StandardCommand):
    """Scv will build a refinery, and when it's finished a certain
    number of workers will begin collecting from it.
    """
    def __init__(self, supply, item_name, raw_text, scv_transfer=3):
        super(RefineryCommand, self).__init__(supply, item_name, raw_text)
        self.scv_transfer = scv_transfer


class ScvCommand(Command):
    """Command for an scv to do something."""
    collect_minerals = False
    collect_gas = False
    scout = False
    



class ConstantCommand(Command):
    """Command to build this unit indefinitely (or to stop)."""

class SwapCommand(Command):
    """Command to lift off a building and switch it with another, in order
    to trade a reactor or tech lab.
    """
