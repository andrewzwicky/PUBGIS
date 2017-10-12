import json


def output_json(filename, name, positions):
    with open(filename, 'w') as json_output:
        json.dump({'name': name, 'positions': positions}, json_output)
