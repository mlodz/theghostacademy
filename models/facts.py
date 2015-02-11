
class Facts(object):
    """This class represents all the facts we know about units, buildings, and research, 
    including costs, supply, dependencies, etc.
    """

    def __init__(self, units, buildings, research):
        self.units = units
        self.buildings = buildings
        self.research = research
    
    def unit_names(self):
        return self.units.keys()

    def building_names(self):
        return self.buildings.keys()

    def research_names(self):
        return self.research.keys()

    def all_item_names(self):
        return self.research_names() + self.building_names() + self.unit_names()


    def cost(self, item_name):
        if item_name in self.units:
            return self.units[item_name]
        if item_name in self.buildings:
            return self.buildings[item_name]
        if item_name in self.research:
            return self.research[item_name]

        raise Exception("Invalid item name: `%s`" % item_name)

    def __str__(self):
        everything = {}
        everything.update(self.units)
        everything.update(self.buildings)
        everything.update(self.research)
        return str(sorted(everything.keys()))
