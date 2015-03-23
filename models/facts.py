
class Facts(object):
    """This class represents all the facts we know about units, buildings, and research, 
    including costs, supply, dependencies, etc.
    """

    def __init__(self, units, buildings, research, abilities):
        self.units = units
        self.buildings = buildings
        self.research = research
        self.abilities = abilities
    
    def unit_names(self):
        return self.units.keys()

    def is_building(self, item_name):
        return item_name in self.buildings.keys()

    def is_unit(self, item_name):
        return item_name in self.units.keys()

    def is_research(self, item_name):
        return item_name in self.research.keys()

    def building_names(self):
        return self.buildings.keys()

    def research_names(self):
        return self.research.keys()

    def all_item_names(self):
        return self.all().keys()

    def all(self):
        everything = {}
        everything.update(self.buildings)
        everything.update(self.units)
        everything.update(self.research)
        return everything

    def dependencies(self, item_name):
        everything = self.all()
        if item_name in everything:
            return everything[item_name]['dependencies']
        

    def cost(self, item_name):
        everything = self.all()
        if item_name in everything:
            return everything[item_name]

        raise Exception("Invalid item name: `%s`" % item_name)

    

    def __str__(self):
        return str(sorted(self.all().keys()))
