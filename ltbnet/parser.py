# TODO: Hardware Interface Binding
# TODO: Router support

import os


def parse_config_csv(file, path=''):
    """Parses an LTBNet config.csv file and return the contents in a dictionary"""
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
