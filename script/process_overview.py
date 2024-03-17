import json

with open('resource/map/overview.json', 'r', encoding='utf-8') as file:
    overview_data = json.load(file)

code_to_filename = {value['code']: value['filename'] for value in overview_data.values()}

with open('resource/level_code_mapping.json', 'w', encoding='utf-8') as file:
    json.dump(code_to_filename, file, ensure_ascii=False, indent=4)

name_to_filename = {value['name']: value['filename'] for value in overview_data.values()}

with open('resource/level_name_mapping.json', 'w', encoding='utf-8') as file:
    json.dump(name_to_filename, file, ensure_ascii=False, indent=4)