"""
Datasets related utilities (list, load).
"""

import pandas as _pd
from importlib import resources as _resources
from pylbmisc.dm import _default_dtype_backend

_dataset_dir = _resources.files("pylbmisc") / "datasets"


def ls() -> list[str]:
    """List available datasets.

    Examples
    --------
    >>> import pylbmisc as lb
    >>> lb.datasets.ls()
    """
    files = sorted(_dataset_dir.rglob("*.csv"))
    fnames = [str(f.name) for f in files]
    return fnames


def load(fname: str = "beetles1.csv", **kwargs) -> _pd.DataFrame:
    """Load an available dataset.

    Parameters
    ----------
    fname: str
        string coming from lb.datasets.ls()
    kwargs: Any
        named paramers passed to pd.read_csv

    Examples
    --------
    >>> import pylbmisc as lb
    >>> lb.datasets.ls()
    >>> df = lb.datasets.load("laureati.csv")
    """
    return _pd.read_csv(_dataset_dir / fname, engine="python",
                        dtype_backend=_default_dtype_backend,
                        **kwargs)
