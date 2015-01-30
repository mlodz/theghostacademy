"""This file contains notes and code that I don't really want to put anywhere yet.
"""


import csv

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


data = parse_building_ability_file('data/HotS/terran_building_abilities.csv')
for b, a in data.items():
    print b, a
