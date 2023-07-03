import os as _os
import pandas as _pd
import tempfile as _tempfile
import zipfile as _zipfile

from pathlib import Path as _Path
from typing import Sequence as _Sequence

# ------------------------------------
# LaTeX stuff
# ------------------------------------

# Thanks PyLaTeX guys
_latex_special_chars = {
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\^{}',
    '\\': r'\textbackslash{}',
    '\n': '\\newline%\n',
    '-': r'{-}',
    '\xA0': '~',  # Non-breaking space
    '[': r'{[}',
    ']': r'{]}',
}

def latex_escape(s):
    """
    latex_escape from PyLaTeX

    s: a str or something coercible to it
    >>> print(latex_escape("asd_foo_bar"))
    """
    string = str(s)
    return ''.join(_latex_special_chars.get(c, c) for c in string)



def latex_table(tab,
                label: str = "",
                caption: str = "",
                digits = 3):
    """ Print a table (a pd.DataFrame or inheriting object with
    to_latex method) with sensible defaults.
    tab: a pd.DataFrame or other object with .to_latex method
    label (str): posta dopo "fig:" in LaTeX
    caption (str): posta dopo "fig:" in LaTeX
    """
    # todo:
    #- format float
    #- table (o altro) con label caption etc
    if (label == "") or (not isinstance(label, str)):
        raise ValueError("Please provide a label for the table.")
    caption = label.capitalize().replace("_", " ") \
        if caption == "" else caption
    latex_caption = latex_escape(caption)
    # latex_label = lb.io.latex_escape('fig:' + label)
    latex_label = 'tab:' + label
    # rimuovo eventuali nomi colonna perché non sono
    # escapati da pandas e mi ritrovo colonna_stratificazione
    # in analisi
    # https://github.com/pandas-dev/pandas/blob/v2.0.3/pandas/core/generic.py#L3174-L3466
    # non è detto che sia sempre ok (es su indici di
    # colonna piu stratificati) ma si vedràs strada facendo
    if isinstance(tab, _pd.DataFrame):
        tab.columns.name = None
    content = tab.to_latex(na_rep = "",
                           index = True,
                           index_names = False,
                           escape = True,
                           label = latex_label,
                           caption = latex_caption)
    print(content)


# ------------------------------------
# Figure and images stuff
# ------------------------------------

def fig_dump(
    fig,
    label: str = "",
    caption: str = "",
    fdir: str = "outputs",
    fname: str = "",
    scale: float = 1,
):
    """Dump a figure (save to file, include in LaTeX)

    Save to png, eps and pdf and include in Latex an image;
    intended to be used inside pythontex pycode.

    Args:
       fig (matplotlib.figure.Figure): the fig
       label (str): posta dopo "fig:" in LaTeX
       caption (str): caption LaTeX, se mancante viene riadattata label
       fdir (str): directory dove salvare, se mancante si usa /tmp
       fname (str): basename del file da salvare, se mancante si prova
          a riusare label oppure a creare un file temporaneo
       scale (float): scale di includegraphics di LaTeX

    Returns:
       None: nothing interesting here
    """
    # fdir not existing, using /tmp
    if not _os.path.isdir(fdir):
        fdir = '/tmp'

    # default filename to be set as label, if available or a temporary one
    if fname == "":
        if label != "":
            fname = label
        else:
            tmp = _tempfile.mkstemp(dir=fdir)
            fname = _os.path.basename(tmp[1])

    # produce the file paths
    base_path = _os.path.join(fdir, fname)
    eps_path = base_path + ".eps"
    png_path = base_path + ".png"
    pdf_path = base_path + ".pdf"

    # save figures to hard drive
    fig.savefig(eps_path)
    fig.savefig(png_path)  # , dpi = 600)
    fig.savefig(pdf_path)

    # latex stuff
    latex_label = 'fig:' + label
    caption = label.capitalize().replace("_", " ") if caption == "" else caption
    latex = (
        "\\begin{figure} \\centering "
        + "\\includegraphics[scale=%(scale).2f]{%(base_path)s}"
        + " \\caption{%(caption)s} \\label{%(label)s} \\end{figure}"
    )
    subs = {
        "scale": scale,
        "base_path": base_path,
        "caption": caption,
        "label": latex_label,
    }
    print(latex % subs)



# ------------------------------------
# Data Import/export (from/to csv/xls)
# ------------------------------------

def data_import(fpaths: str | _Path | _Sequence[str | _Path],
                csv_kwargs: dict = {},
                excel_kwargs: dict = {}) -> dict[str, _pd.DataFrame]:
    '''import data from one or several filepaths (supported formats: .csv
    .xls .xlsx .zip) and return a dict of DataFrame
    '''
    # import ipdb
    # ipdb.set_trace()

    # uniform 1 to many and clean input
    if isinstance(fpaths, str) or isinstance(fpaths, _Path):
        fpaths = [fpaths]
    accepted_fpaths = [str(f) for f in fpaths if _os.path.splitext(f)[1].lower() in {".csv", ".xls", ".xlsx", ".zip"}]

    rval: dict[str, _pd.DataFrame] = {}

    for fpath in accepted_fpaths:
        fname = _os.path.splitext(_os.path.basename(fpath))[0]
        fext = _os.path.splitext(fpath)[1].lower()
        if fext == '.csv':
            dfname = fname
            data = _pd.read_csv(fpath, **csv_kwargs)
            if dfname not in rval.keys():  # check for duplicates
                rval[dfname] = data
            else:
                msg = "{0} is duplicated, skipping to avoid overwriting"
                raise Warning(msg.format(dfname))
        elif fext in {'.xls', '.xlsx'}:
            sheets = _pd.read_excel(fpath, None, **excel_kwargs)  # import all the sheets as a dict of DataFrame
            sheets = {"{0}_{1}".format(fname, k): v for k, v in sheets.items()}  # add xlsx to sheet names
            rval.update(sheets)
        elif fext == '.zip':  # unzip in temporary directory and go by recursion
            with _tempfile.TemporaryDirectory() as tempdir:
                with _zipfile.ZipFile(fpath) as myzip:
                    myzip.extractall(tempdir)
                    zipped_fpaths = [_os.path.join(tempdir, f) for f in _os.listdir(tempdir)]
                    zipped_data = data_import(zipped_fpaths)
            # prepend zip name to fname (as keys) and update results
            zipped_data = {"{0}_{1}".format(fname, k): v for k, v in zipped_data.items()}
            rval.update(zipped_data)
        else:
            msg = "File format not supported for {0}. Ignoring it.".format(fext)
            raise Warning(msg)

    if len(rval):
        return rval
    else:
        raise ValueError("No data to be imported.")


def data_export(x: dict[str, _pd.DataFrame], path: str | _Path) -> None:
    """export a dict of DataFrame as a list of csv or a single excel file

    in case of a dict is used and a csv path is given, the path is
    suffixed with dict names

    x: dict of pandas.DataFrame
    fpath: fpath file path

    """
    path = _Path(path)
    fmt = path.suffix
    if fmt == ".csv":
        if isinstance(x, _pd.DataFrame):
            x.to_csv(path, index=False)
        elif isinstance(x, dict):
            for k, v in x.items():
                csvpath = path.parent / (str(path.stem) + "_{0}.csv".format(k))
                print(k, csvpath)
                v.to_csv(csvpath, index=False)
        else:
            raise ValueError("x deve essere un pd.DataFrame o un dict di pd.DataFrame")
    elif fmt == ".xlsx":
        if isinstance(x, _pd.DataFrame):
            x.to_excel(writer, sheet_name="Foglio 1")
        elif isinstance(x, dict):
            with _pd.ExcelWriter(str(path)) as writer:
                for k, v in x.items():
                    v.to_excel(writer, sheet_name=k)
        else:
            raise ValueError("x deve essere un pd.DataFrame o un dict di pd.DataFrame")
    else:
        raise ValueError("Formato non disponibile: disponibili csv ed xlsx.")


# --------------------------------------------------
# rdf: pd.DataFrame to R data.frame converter (a-la dput)
# --------------------------------------------------


def _rdf_integer(x: _pd.Series, xn: str):
    data_str = x.to_string(
        na_rep="NA",
        index=False,
        header=False,
    ).replace("\n", ", ")
    rval = "{} = c({})".format(xn, data_str)
    return rval


# placeholder
_rdf_numeric = _rdf_integer


def _rdf_factor(x: _pd.Series, xn: str):
    # to be safe it's seems to be better rather than
    # pd.Categorical
    x = _pd.Series(x, dtype='category')
    # raw data (integers)
    data = x.cat.codes
    data_str = "c({})".format(
        data.to_string(
            na_rep="NA",
            index=False,
            header=False,
        ).replace("\n", ", ")
    )
    # unique categories and labels
    categs = x.cat.categories
    levels = []
    labels = []
    for lev, lab in enumerate(categs):
        levels.append(str(lev))
        labels.append("'{}'".format(lab))

    levs = ", ".join(levels)
    labs = ", ".join(labels)
    levels_str = "levels = c({})".format(levs)
    labels_str = "labels = c({})".format(labs)
    # return
    rval = "{} = factor({}, {}, {})".format(xn, data_str, levels_str, labels_str)
    return rval


def _rdf_object(x: _pd.Series, xn: str):
    data_l = x.to_list()
    data_l2 = []
    for s in data_l:
        if isinstance(s, str) and s != "":
            data_l2.append('"{}"'.format(s))
        else:
            data_l2.append('NA')
    data_str = ', '.join(data_l2)
    rval = "{} = c({})".format(xn, data_str)
    return rval


def _rdf_bool(x: _pd.Series, xn: str):
    ft = {True : "TRUE", False : "FALSE"}
    data_str = x.map(ft).to_string(
        na_rep="NA",
        index=False,
        header=False,
    ).replace("\n", ", ")
    rval = "{} = c({})".format(xn, data_str)
    return rval


# Thigs yet TODO
def _rdf_NA(x: _pd.Series, xn: str):
    rval = "{} = NA".format(xn)
    return rval

_rdf_datetime = _rdf_NA




def rdf(df: _pd.DataFrame, path: str | _Path, dfname: str = "df"):
    """
    pd.DataFrame to R data.frame 'converter'
    """
    path = _Path(path)

    r_code = []
    r_code.append("{} <- data.frame(".format(dfname))
    for var in df.columns:
        x = df[var]
        if _pd.api.types.is_integer_dtype(x):
            r_code.append(_rdf_integer(x, var))
        elif _pd.api.types.is_numeric_dtype(x):
            r_code.append(_rdf_numeric(x, var))
        elif _pd.api.types.is_categorical_dtype(x):
            r_code.append(_rdf_factor(x, var))
        elif _pd.api.types.is_bool_dtype(x):
            r_code.append(_rdf_bool(x, var))
        elif _pd.api.types.is_datetime64_any_dtype(x):
            r_code.append(_rdf_datetime(x, var))
        elif _pd.api.types.is_object_dtype(x):
            r_code.append(_rdf_object(x, var))
        else:
            msg = "{}: il tipo {} non è ancora gestito.".format(var, str(x.dtype))
            raise ValueError(msg)
        is_last = var == df.columns[-1]
        if not is_last:
            r_code.append(",\n")
        else:
            r_code.append(")\n")

    with path.open(mode="w") as f:
        f.writelines(r_code)
