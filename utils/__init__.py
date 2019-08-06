import htcondor
try:
    from typing import Dict, Any
except ImportError: pass


def get_schedd(pool=None, schedd_name=None):
    if schedd_name:
        collector = htcondor.Collector(pool)
        return htcondor.Schedd(collector.locate(
            htcondor.DaemonTypes.Schedd,
            schedd_name
        ))
    else:
        return htcondor.Schedd()


def deep_lcasekeys(dictish):
    # type: (Dict[str, Any]) -> Dict
    """Return a copy of a dictionary with all the keys lowercased, recursively."""
    transformed_dict = dict()
    for k, v in dictish.items():
        k = k.lower()
        if isinstance(v, dict):
            v = deep_lcasekeys(v)
        transformed_dict[k] = v
    return transformed_dict
