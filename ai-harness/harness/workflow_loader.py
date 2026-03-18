import json


def load_workflow(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)