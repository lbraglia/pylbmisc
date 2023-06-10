"""
Modulo con funzioni di utilità per Telegram
"""

import json
import pandas as pd

from pathlib import Path


def chat2df(fpath):
    '''Trasforma una chat json esportata dal clienti desktop in un
    DataFrame Pandas.

    fpath: str|Path to a json export of a telegram chat

    '''
    fpath = Path(fpath)
    with fpath.open() as f:
        js = json.load(f)
        msg = js["messages"]
        return pd.DataFrame(msg)
