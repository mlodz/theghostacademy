import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)


from models import parser
from models import facts
from models import terran

def main():

    # Setup Facts
    units = parser.parse_dependency_file('data/HotS/terran_units.csv')
    buildings = parser.parse_dependency_file('data/HotS/terran_buildings.csv')
    research = parser.parse_dependency_file('data/HotS/terran_research.csv')
    abilities = parser.parse_building_ability_file('data/HotS/terran_abilities.csv')

    item_facts = facts.Facts(units, buildings, research, abilities)

    #build_order = parser.parse_build_order_file('input_examples/dev_test.txt', item_facts)
    #build_order = parser.parse_build_order_file('input_examples/HotS_banshee_opener.txt', item_facts)
    build_order = parser.parse_build_order_file('input_examples/standard_opener.txt', item_facts)   

    game = terran.HotsGame(build_order, item_facts).run()



main()
