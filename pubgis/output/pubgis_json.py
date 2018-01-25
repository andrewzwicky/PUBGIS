import json
from jsonschema import validate, ValidationError

SCHEMA = {
    "$schema": "http://json-schema.org/draft-06/schema#",
    "additionalProperties": False,
    "definitions": {},
    "properties": {
        "game": {
            "type": ["integer", "null"]
        },
        "name": {
            "type": ["string", "null"]
        },
        "positions": {
            "additionalItems": False,
            "items": {
                "items": [{"type": "number"},
                          {"anyOf": [
                              {"items": [{"type": "integer"}, {"type": "integer"}],
                               "type": "array"},
                              {"type": "null"}]}],
                "type": "array"
            },
            "type": "array"
        },
        "team": {
            "type": ["string", "null"]
        }
    },
    "type": "object",
    "required": ["positions"]
}


# TODO: clean up json validation


def valididate_pubgis_schema(data):
    try:
        validate(data, SCHEMA, types={'array': (list, tuple)})
        return True
    except ValidationError:
        return False


def create_json_data(positions, timestamps, name=None, game=None, team=None):
    return {'name': name,
            'game': game,
            'team': team,
            'positions': list(zip(timestamps, positions))}


def output_json(filename, data):
    if valididate_pubgis_schema(data):
        with open(filename, 'w') as json_output_file:
            json.dump(data, json_output_file)

            # TODO: error message for failed write


def read_json_file(filename):
    with open(filename, 'r') as json_input_file:
        data = json.load(json_input_file)

    return data


def parse_input_json_data(data):
    if valididate_pubgis_schema(data):
        try:
            name = data['name']
        except KeyError:
            name = None

        try:
            game = data['game']
        except KeyError:
            game = None

        try:
            team = data['team']
        except KeyError:
            team = None

        timestamps = []
        positions = []
        for timestamp, position in data['positions']:
            timestamps.append(timestamp)
            positions.append(tuple(position) if position is not None else position)

        return name, positions, timestamps, game, team
    return None, None, None, None, None


def input_json(filename):
    data = read_json_file(filename)
    return parse_input_json_data(data)
