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
    fnames = [str(f.name).replace(".csv", "") for f in files]
    return fnames


def load(dname: str = "beetles1", **kwargs) -> _pd.DataFrame:
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
    data_file = _dataset_dir / (dname + ".csv") 
    doc_file = _dataset_dir / (dname + ".txt") 
    data = _pd.read_csv(data_file,
                        engine="python",
                        dtype_backend=_default_dtype_backend,
                        **kwargs)
    with open(doc_file, "r") as f:
        doc = f.read()
    data.__doc__ = doc
    return data
