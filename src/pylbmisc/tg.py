import json
import pandas as pd

from pathlib import Path


def chat2df(fpath: str | Path) -> pd.DataFrame:
    """Telegram chat json to pandas DataFrame

    Trasforma una chat json esportata dal clienti desktop in un
    DataFrame Pandas.

    Args:
       fpath (str|Path): path ad un file json esportato da Telegram

    Returns:
       pandas.DataFrame: the chat

    """
    fpath = Path(fpath)
    with fpath.open() as f:
        js = json.load(f)
        msg = js["messages"]
        return pd.DataFrame(msg)



def bot_token(b):
    """
    Get Bot API token from environment variables.
    """
    return os.environ["TG_BOT_%s" % b]


def user_id(u):
    """
    Get user id from environment variables.
    """
    return os.environ["TG_USER_%s" % u]


def group_id(g):
    """
    Get group id from environment variables.
    """
    return os.environ["TG_GROUP_%s" % g]
    
