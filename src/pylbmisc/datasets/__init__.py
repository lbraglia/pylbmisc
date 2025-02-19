import pandas as _pd
from importlib import resources as _resources
from pprint import pp as _pp
# idea stolen from lifelines

_dataset_dir = _resources.files("pylbmisc") / "datasets"


def list():
    """List available datasets."""
    files = sorted(_dataset_dir.rglob("*.csv"))
    fnames = [str(f.name) for f in files]
    return fnames


def load(fname, **kwargs):
    """Load a dataset from pylbmisc.

    Parameters
    fname : string (eg "frei.csv")
    kwargs: named paramers passed to pd.read_csv
    """
    return _pd.read_csv(_dataset_dir / fname, engine="python", **kwargs)
