import os
import json


def parse_config_csv(file, path=''):
    """Parses an LTBNet config.csv file and return the contents in a list of dictionaries"""
    keys = list()
    out = list()
    flag = False
    with open(os.path.join(path, file)) as f:
        for num, line in enumerate(f):
            if not line.strip():
                continue

            if line.startswith('#'):
                continue
            data = line.strip().split(',')

            # Use the first valid line as the keys
            if not flag:
                keys = data
                flag = True
                continue

            out.append({k: v for k, v in zip(keys, data)})

    return out


def parse_config_json(file, path=''):
    """
    Parse an LTBNet config.json file and return the data in a list of dictionaries
    """
    with open(os.path.join(path, file)) as f:
        out = json.load(f)

    return out


def parse_config(file, path='', fmt=None):
    if fmt is None:
        name, fmt = os.path.splitext(file)

    if fmt[1:] == 'json':
        out = parse_config_json(file, path)
    elif fmt[1:] == 'csv':
        out = parse_config_csv(file, path)
    else:
        raise NotImplementedError('File format {} not supported'.format(fmt))

    return out