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
    item_facts = facts.Facts(units, buildings, research)


    build_order = parser.parse_build_order_file('input_examples/scv_test.txt', item_facts)
    # build_order = ['scv', 'scv', 'supply depot']
    print "Build Order:", build_order

    print "****************************************************************"
    print "RUN GAME"
    game = terran.HotsGame(build_order, item_facts).run()

    print "done"


main()
