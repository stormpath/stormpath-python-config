"""Helper functions that this package relies upon."""


from codecs import open as copen
from os.path import isfile


def _load_properties(fname):
    """
    Load a .properties file, and return the contents as a dictionary.

    :param str fname: The file name to open.
    :rtype: dict
    :returns: A dictionary of key / values, loaded from the file.
    """
    props = {}

    if not fname or not isfile(fname):
        return props

    with copen(fname, 'r', encoding='utf-8') as fd:
        for line in fd:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue

            k, v = line.split('=', 1)
            props[k.strip()] = v.strip()

    return props


def _extend_dict(original, extend_with):
    """
    Extend a dictionary with another.

    :param dict original: The original dictionary to extend.
    :param dict extend_with: The dictionary with which to extend.
    :rtype: dict
    :returns: The extended dictionary.
    """
    for key, value in extend_with.items():
        if key in original and isinstance(value, dict):
            _extend_dict(original[key], value)
        else:
            original[key] = value

    return original


def to_camel_case(s):
    """
    Convert a string to camelCase.

    :param str s: The string to convert.
    :rtype: str
    :returns: The camelCased string.
    """
    if '_' not in s:
        return s

    head, tail = s.split('_', 1)
    tail = tail.title().replace('_', '')

    return head + tail
