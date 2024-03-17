import json

with open('resource/map/overview.json', 'r', encoding='utf-8') as file:
    overview_data = json.load(file)

code_to_filename = {value['code']: value['filename'] for value in overview_data.values()}

with open('resource/level_mapping.json', 'w', encoding='utf-8') as file:
    json.dump(code_to_filename, file, ensure_ascii=False, indent=4)
