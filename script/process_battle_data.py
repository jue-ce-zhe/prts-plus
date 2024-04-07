import json

with open('resource/battle_data.json', 'r', encoding='utf-8') as file:
    battle_data = json.load(file)

name_to_filename = {}

# Sort the keys
sorted_keys = sorted(battle_data["chars"].keys())

for key in sorted_keys:
    value = battle_data["chars"][key]
    if value['name'] not in name_to_filename.keys():
        name_to_filename[value['name']] = key
        # Save another version without curly quotes
        quoteless_name = value['name'].replace('“', '').replace('”', '')
        name_to_filename[quoteless_name] = key

with open('resource/operator_mapping.json', 'w', encoding='utf-8') as file:
    json.dump(name_to_filename, file, ensure_ascii=False, indent=4)