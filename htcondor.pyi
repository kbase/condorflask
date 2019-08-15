# stubs for htcondor
# TODO These should be moved to the Python bindings for HTCondor itself

import classad

from typing import Any, List, Optional, Union

class AdTypes:
    Generic: Any
    Accounting: Any
    Any: Any
    Collector: Any
    Credd: Any
    Defrag: Any
    Generic: Any
    Grid: Any
    HAD: Any
    License: Any
    Master: Any
    Negotiator: Any
    Schedd: Any
    Startd: Any
    Submitter: Any


class Collector:
    def __init__(self, pool:Union[str, List[str], None]=...): ...
    def locate(self, daemon_type:DaemonTypes, name:str): ...
    def query(self, ad_type:AdTypes=..., constraint:str=..., projection:List[str]=..., statistics:str=...) -> List[classad.ClassAd]:...


class DaemonTypes:
    Any: Any
    Master: Any
    Schedd: Any
    Startd: Any
    Collector: Any
    Negotiator: Any
    HAD: Any
    Generic: Any
    Credd: Any


class Schedd:
    def __init__(self, location_ad:Optional[classad.ClassAd]=...): ...
