import json
import os
from os.path import join, dirname

import pytest

from pubgis.output.pubgis_json import output_json, input_json, valididate_pubgis_schema, \
    parse_input_json_data, create_json_data

JSON_TEST_DIR = join(dirname(__file__), "json")

COORDS = [(3079, 4034), (3095, 4061), None, (3123, 4108), (3140, 4138), (3160, 4170),
          (3178, 4201), (3194, 4228), (3208, 4251), (3228, 4285), (3247, 4318), (3265, 4348),
          (3281, 4374), (3298, 4402), (3314, 4429), (3330, 4459), (3350, 4491), (3371, 4525),
          (3387, 4551), (3400, 4574), (3413, 4598)]

TIMESTAMPS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

GAME = None
TEAM = "best_team"
USER = "username"

VALID_JSON_FOLDER = join(dirname(__file__), "json", "valid")
INVALID_JSON_FOLDER = join(dirname(__file__), "json", "invalid")


def test_json_write():
    actual_file = join(JSON_TEST_DIR, 'actual_out.json')
    expected_file = join(JSON_TEST_DIR, 'expected_out.json')

    output_json(actual_file, create_json_data(COORDS, TIMESTAMPS, name=USER, game=GAME, team=TEAM))

    expected_read = open(expected_file, 'r').read()
    actual_read = open(actual_file, 'r').read()

    assert actual_read == expected_read


def test_json_read():
    expected_file = join(JSON_TEST_DIR, 'expected_out.json')
    assert input_json(expected_file) == (USER, COORDS, TIMESTAMPS, GAME, TEAM)


def test_json_same():
    actual_file = join(JSON_TEST_DIR, 'actual_out.json')
    output_json(actual_file, create_json_data(COORDS, TIMESTAMPS, name=USER, game=GAME, team=TEAM))
    assert input_json(actual_file) == (USER, COORDS, TIMESTAMPS, GAME, TEAM)


@pytest.mark.parametrize("valid_json_file", os.scandir(VALID_JSON_FOLDER))
def test_json_schema_valid(valid_json_file):
    with open(valid_json_file.path, 'r') as in_file:
        data = json.load(in_file)

    assert valididate_pubgis_schema(data)


@pytest.mark.parametrize("invalid_json_file", os.scandir(INVALID_JSON_FOLDER))
def test_json_schema_invalid(invalid_json_file):
    with open(invalid_json_file.path, 'r') as in_file:
        data = json.load(in_file)

    assert not valididate_pubgis_schema(data)


def test_missing_json():
    assert parse_input_json_data({"positions": []}) == (None, [], [], None, None)
