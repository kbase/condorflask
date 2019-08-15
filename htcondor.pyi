# stubs for htcondor
# TODO These should be moved to the Python bindings for HTCondor itself

import classad

from typing import Any, List

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
    def query(self, ad_type:AdTypes=..., constraint:str=..., projection:List[str]=..., statistics:str=...) -> List[classad.ClassAd]:...
