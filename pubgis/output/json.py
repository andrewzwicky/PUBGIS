import json


def output_json(filename, name, positions, timestamps):
    with open(filename, 'w') as json_output_file:
        json.dump({'name': name, 'positions': list(zip(timestamps, positions))}, json_output_file)


def input_json(filename):
    with open(filename, 'r') as json_input_file:
        data = json.load(json_input_file)

    name = data['name']
    timestamps = []
    positions = []
    for timestamp, position in data['positions']:
        timestamps.append(timestamp)
        positions.append(tuple(position) if position is not None else position)

    return name, positions, timestamps
