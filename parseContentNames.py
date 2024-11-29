# this isn't really an xsoar automation but useful for grabbing all of the names for content in a content pack 
# e.g. you use demisto-sdk to create a custom content pack and you just want to dump the names for documentation or whatever ;)

import os
import json
import yaml

# subfolders
subfolders = [
    'Classifiers', 'Dashboards', 'IncidentFields', 'IncidentTypes',
    'IndicatorFields', 'IndicatorTypes', 'Jobs', 'Layouts', 'Playbooks',
    'Reports', 'Scripts', 'Widgets'
]

# dict to store names under each subfolder
names_per_subfolder = {}

# base directory 
base_dir = os.getcwd()

for subfolder in subfolders:
    subfolder_path = os.path.join(base_dir, subfolder)
    names = []

    if not os.path.exists(subfolder_path):
        # skip subfolder if it doesn't exist
        continue

    # iterate through the subfolder and its nested dirs
    for root, dirs, files in os.walk(subfolder_path):
        for file in files:
            if file.endswith(('.json', '.yml', '.yaml')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        if file.endswith('.json'):
                            data = json.load(f)
                        else:
                            data = yaml.safe_load(f)

                    # extract 'name' at the highest level
                    if isinstance(data, dict) and 'name' in data:
                        name = data['name']
                        names.append(name)
                except Exception as e:
                    print(f"error processing file {file_path}: {e}")

    if names:
        names_per_subfolder[subfolder] = names

# write the collected names to 'content-names.txt'
with open('content-names.txt', 'w', encoding='utf-8') as f:
    for subfolder in subfolders:
        names = names_per_subfolder.get(subfolder, [])
        if names:
            f.write(f"{subfolder}:\n")
            for name in names:
                f.write(f"{name}\n")
            f.write('\n')
