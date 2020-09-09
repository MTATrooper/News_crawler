import json

def load_json(path):
    with open(path, 'r') as f:
        dic = json.loads(f.read())
    return dic