import json


def output_json(filename, name, positions):
    with open(filename, 'w') as json_output_file:
        json.dump({'name': name, 'positions': positions}, json_output_file)


def input_json(filename):
    with open(filename, 'r') as json_input_file:
        data = json.load(json_input_file)

    name = data['name']
    positions = data['positions']

    return name, positions
