from __future__ import annotations

from enum import Enum, EnumDict

class WBMr:
    def __init__(self):
        pass

class Model(EnumDict):
    wbmr6c = {"name": "WB-MR6C v.2","class": WBMr}
    wbmio = {"name": "WB-MGE v.3", "class": None}


a=Model.wbmr6c.values()
t=Model.wbmr6c["name"]
tc=Model.wbmr6c["class"]
print(a)