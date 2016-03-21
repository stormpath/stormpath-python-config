"""Helper functions that this package relies upon."""


from codecs import open as copen
from os.path import isfile


def _load_properties(fname):
    props = {}
    if not fname or not isfile(fname):
        return props

    try:
        with copen(fname, 'r', encoding='utf-8') as fd:
            for line in fd:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue

                k, v = line.split('=', 1)
                props[k.strip()] = v.strip()

        return props
    except UnicodeDecodeError:
        return {}


def _extend_dict(original, extend_with):
    for key, value in extend_with.items():
        if key in original and isinstance(value, dict):
            _extend_dict(original[key], value)
        else:
            original[key] = value
    return original


def to_camel_case(name):
    if '_' not in name:
        return name

    head, tail = name.split('_', 1)
    tail = tail.title().replace('_', '')

    return head + tail
