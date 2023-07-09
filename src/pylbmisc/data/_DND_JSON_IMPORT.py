import json
import pprint


with open("dnd/adventuringgear.json") as f:
    agear = json.load(f)

with open("dnd/armor.json") as f:
    armor = json.load(f)

with open("dnd/classes.json") as f:
    classes = json.load(f)

with open("dnd/conditions.json") as f:
    conditions = json.load(f)

with open("dnd/races.json") as f:
    races = json.load(f)

with open("dnd/spells.json") as f:
    spells = json.load(f)

with open("dnd/weapons.json") as f:
    weapons = json.load(f)


dnd_data = agear + armor + classes + conditions + races + spells + weapons
with open("dnd_srd.py", "w") as f:
    print("srd = ", dnd_data, file=f)
