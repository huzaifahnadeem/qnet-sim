import os
import json


check_for_params = {
    'seed': 82
}
dir = "/home/hun13/qnet-sim/src/experiments-results/varying-lengths-0.5-1"

filenames = os.listdir(dir)
filenames[:] = [x for x in filenames if x[-5:] == '.json'] # only select .json files


files_data = {}
for fn in filenames:
    with open(f'{dir}/{fn}', 'r') as jsonfile:
        files_data[fn] = json.load(jsonfile)


found = []
for filename in files_data:
    data = files_data[filename]
    for param in check_for_params:
        if data['params_used'][param] == check_for_params[param]:
            found.append(filename)


print(dir)
print()
for filename in found:
    print(filename)

