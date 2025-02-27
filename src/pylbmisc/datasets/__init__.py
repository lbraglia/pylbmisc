import pandas as _pd
from importlib import resources as _resources

_dataset_dir = _resources.files("pylbmisc") / "datasets"


def ls():
    """List available datasets.

    Examples
    --------
    >>> import pylbmisc as lb
    >>> lb.datasets.ls()
    """
    files = sorted(_dataset_dir.rglob("*.csv"))
    fnames = [str(f.name) for f in files]
    return fnames


def load(fname: str = "beetles1.csv", **kwargs):
    """Load an available dataset.

    Parameters
    ----------
    fname:
        string coming from lb.datasets.ls()
    kwargs:
        named paramers passed to pd.read_csv

    Examples
    --------
    >>> import pylbmisc as lb
    >>> lb.datasets.ls()
    >>> df = lb.datasets.load("laureati.csv")

    """
    return _pd.read_csv(_dataset_dir / fname, engine="python", **kwargs)
