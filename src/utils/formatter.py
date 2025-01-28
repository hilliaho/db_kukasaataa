import json


def print_pretty_json(data):
    """Tulostaa JSON-datan helposti luettavassa muodossa."""
    formatted_json = json.dumps(data, indent=4, ensure_ascii=False)
    print(formatted_json)
