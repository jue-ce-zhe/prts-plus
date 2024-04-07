import json

with open('resource/battle_data.json', 'r', encoding='utf-8') as file:
    battle_data = json.load(file)

name_to_filename = {}

def add_mapping(name, filename):
    if name_to_filename.get(name):
        if filename not in name_to_filename[name]:
            name_to_filename[name].append(filename)
    else:
        name_to_filename[name] = [filename]

for key, value in battle_data["chars"].items():
    add_mapping(value['name'], key)
    # Save another version without curly quotes
    quoteless_name = value['name'].replace('“', '').replace('”', '')
    add_mapping(quoteless_name, key)

with open('resource/operator_mapping.json', 'w', encoding='utf-8') as file:
    json.dump(name_to_filename, file, ensure_ascii=False, indent=4)
