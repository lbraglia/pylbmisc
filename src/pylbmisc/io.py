import os
import pandas as pd
import tempfile
import zipfile

from pathlib import Path
from typing import Sequence


def data_import(fpaths: Sequence[str | Path]) -> dict[str, pd.DataFrame]:
    '''
    import data from several filepaths (supported formats: .csv .xls .xlsx .zip) and return a dict of DataFrame
    '''
    # import ipdb
    # ipdb.set_trace()
    accepted_fpaths = [str(f) for f in fpaths if os.path.splitext(f)[1].lower() in {".csv", ".xls", ".xlsx", ".zip"}]

    rval: dict[str, pd.DataFrame] = {}

    for fpath in accepted_fpaths:
        fname = os.path.splitext(os.path.basename(fpath))[0]
        fext = os.path.splitext(fpath)[1].lower()
        if fext == '.csv':
            dfname = fname
            data = pd.read_csv(fpath)
            if dfname not in rval.keys():  # check for duplicates
                rval[dfname] = data
            else:
                raise Warning("{0} is probably duplicated, skipping to avoid overwriting ".format(dfname))
        elif fext in {'.xls', '.xlsx'}:
            sheets = pd.read_excel(fpath, None)  # import all the sheets as a dict of DataFrame
            sheets = {"{0}_{1}".format(fname, k): v for k, v in sheets.items()}  # add xlsx to sheet names
            rval.update(sheets)
        elif fext == '.zip':  # unzip in temporary directory and go by recursion
            with tempfile.TemporaryDirectory() as tempdir:
                with zipfile.ZipFile(fpath) as myzip:
                    myzip.extractall(tempdir)
                    zipped_fpaths = [os.path.join(tempdir, f) for f in os.listdir(tempdir)]
                    zipped_data = data_import(zipped_fpaths)
            # prepend zip name to fname (as keys) and update results
            zipped_data = {"{0}_{1}".format(fname, k): v for k, v in zipped_data.items()}
            rval.update(zipped_data)
        else:
            raise Warning(
                "Format not supported for {0}. It must be a .csv, .xls, .xlsx, .zip. Ignoring it.".format(fext)
            )
    if len(rval):
        return rval
    else:
        raise ValueError("No data to be imported.")


def data_export(dfs: dict[str, pd.DataFrame], fpath: str | Path, fmt: str = "csv") -> None:
    '''
    export a dict of DataFrame as a list of csv or a single excel file

    dfs: dict of pandas.DataFrame
    fpath: fpath file path
    fmt: str, file format as "csv" (default) or "xlsx"
    '''
    fpath = Path(fpath)
    if fmt == "csv":
        for k, v in dfs.items():
            csvpath = fpath.parent / (str(fpath.stem) + "_{0}.csv".format(k))
            print(k, csvpath)
            v.to_csv(csvpath, index=False)
    elif fmt == "excel":
        with pd.ExcelWriter(str(fpath)) as writer:
            for k, v in dfs.items():
                v.to_excel(writer, sheet_name=k)
    else:
        raise ValueError("Formato non disponibile: disponibili csv ed xlsx.")


# def import_logical(x):
#     """
#     Function to import logical values saved in csv
#     """
#     if ((x == "TRUE") or (x == "True") or (x == True)):
#         return True
#     elif (x == "NA") or (x == None) or (x == ""):
#         return None
#     else:
#         return False


# def import_character(x):
#     """
#     Function to import characters values saved in csv
#     """
#     if (x == "" or x == "NA"):
#         return None
#     else:
#         return str(x)
