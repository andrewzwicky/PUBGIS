from os.path import join, dirname

from pubgis.output.json import output_json, input_json

JSON_TEST_DIR = join(dirname(__file__), "json")

COORDS = [(3079, 4034), (3095, 4061), None, (3123, 4108), (3140, 4138), (3160, 4170),
          (3178, 4201), (3194, 4228), (3208, 4251), (3228, 4285), (3247, 4318), (3265, 4348),
          (3281, 4374), (3298, 4402), (3314, 4429), (3330, 4459), (3350, 4491), (3371, 4525),
          (3387, 4551), (3400, 4574), (3413, 4598)]

TIMESTAMPS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]


def test_json_write():
    actual_file = join(JSON_TEST_DIR, 'actual_out.json')
    expected_file = join(JSON_TEST_DIR, 'expected_out.json')

    output_json(actual_file, "username", COORDS, TIMESTAMPS)

    expected_read = open(expected_file, 'r').read()
    actual_read = open(actual_file, 'r').read()

    assert actual_read == expected_read


def test_json_read():
    expected_file = join(JSON_TEST_DIR, 'expected_out.json')

    assert input_json(expected_file) == ("username", COORDS, TIMESTAMPS)


def test_json_same():
    actual_file = join(JSON_TEST_DIR, 'actual_out.json')

    output_json(actual_file, "username", COORDS, TIMESTAMPS)

    assert input_json(actual_file) == ("username", COORDS, TIMESTAMPS)
