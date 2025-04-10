"""
Data, figures/tables IO handy utilities.
"""

import os as _os
import pandas as _pd
import tempfile as _tempfile
import zipfile as _zipfile

from pylbmisc.dm import fix_varnames as _fix_varnames

from pathlib import Path as _Path
from typing import Sequence as _Sequence

from pylbmisc.dm import _default_dtype_backend
from pylbmisc.dm import _is_string

# ------------------------------------
# Figure and images stuff
# ------------------------------------
def export_figure(fig,
                  label: str = "",
                  caption: str = "",
                  fdir: str = "outputs",
                  fname: str = "",
                  scale: float = 1
                  ) -> None:
    """Dump a figure (save to file, include in LaTeX)

    Save to png, eps and pdf and include in Latex an image;
    intended to be used inside pythontex pycode.

    Parameters
    ----------
    fig: matplotlib.figure.Figure
        the fig
    label: str
        posta dopo "fig:" in LaTeX
    caption: str
        caption LaTeX, se mancante viene riadattata label
    fdir: str
        directory dove salvare, se mancante si usa /tmp
    fname: str
        basename del file da salvare, se mancante si prova a riusare
        label oppure a creare un file temporaneo
    scale: float
        scale di includegraphics di LaTeX
    """
    # fdir not existing, using /tmp
    if not _os.path.isdir(fdir):
        fdir = "/tmp"

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
    latex_label = "fig:" + label
    caption = (
        label.capitalize().replace("_", " ") if caption == "" else caption
    )
    latex = (
        "\\begin{figure} \\centering "
        "\\includegraphics[scale=%(scale).2f]{%(base_path)s}"
        " \\caption{%(caption)s} \\label{%(label)s} \\end{figure}"
    )
    subs = {
        "scale": scale,
        "base_path": base_path,
        "caption": caption,
        "label": latex_label,
    }
    print(latex % subs)


# ------------------------------------
# Dataset Import/export routines
# ------------------------------------
def import_data(fpaths: str | _Path | _Sequence[str | _Path],
                csv_kwargs: dict = {"dtype_backend": _default_dtype_backend},
                excel_kwargs: dict = {"dtype_backend": _default_dtype_backend},
                rm_common_prefix: bool = True
                ) -> _pd.DataFrame | dict[str, _pd.DataFrame]:
    '''Import data

    Can be used to import data from one or several filepaths

    Parameters
    ----------
    fpaths: string, Path, or sequence of
        file paths (supported formats: .csv .xls .xlsx .zip)
    csv_kwargs: dict
        parameter passed to read_csv
    excel_kwargs: dict
        parameter passed to read_excel
    rm_common_prefix: bool
        if dataset share the same common prefix, remove it

    Returns
    -------
    A dict of DataFrame

    '''
    # import ipdb
    # ipdb.set_trace()

    # uniform 1 to many and clean input
    if isinstance(fpaths, str) or isinstance(fpaths, _Path):
        fpaths = [fpaths]
    accepted_fpaths = [
        str(f)
        for f in fpaths
        if _os.path.splitext(f)[1].lower() in {".csv", ".xls", ".xlsx", ".zip"}
    ]

    rval: dict[str, _pd.DataFrame] = {}

    for fpath in accepted_fpaths:
        fname = _os.path.splitext(_os.path.basename(fpath))[0]
        fext = _os.path.splitext(fpath)[1].lower()
        if fext == ".csv":
            dfname = fname
            data = _pd.read_csv(fpath, **csv_kwargs)
            if dfname not in rval.keys():  # check for duplicates
                rval[dfname] = data
            else:
                msg = f"{dfname} is duplicated, skipping to avoid overwriting"
                raise Warning(msg)
        elif fext in {".xls", ".xlsx"}:
            sheets = _pd.read_excel(
                fpath, None, **excel_kwargs
            )  # import all the sheets as a dict of DataFrame
            sheets = {
                f"{fname}_{k}": v for k, v in sheets.items()
            }  # add xlsx to sheet names
            rval.update(sheets)
        elif (
            fext == ".zip"
        ):  # unzip in temporary directory and go by recursion
            with _tempfile.TemporaryDirectory() as tempdir:
                with _zipfile.ZipFile(fpath) as myzip:
                    myzip.extractall(tempdir)
                    zipped_fpaths = [
                        _os.path.join(tempdir, f) for f in _os.listdir(tempdir)
                    ]
                    zipped_data = import_data(zipped_fpaths)
            # prepend zip name to fname (as keys) and update results
            zipped_data = {
                f"{fname}_{k}": v for k, v in zipped_data.items()
            }
            rval.update(zipped_data)
        else:
            msg = f"File format not supported for {fext}. Ignoring it."
            raise Warning(msg)

    if len(rval) == 1:
        # a single dataset: return the data directly
        for v in rval.values():
            return v
    elif len(rval) > 1:
        # multiple dataset return the dict and remove common name prefix
        if rm_common_prefix:
            keys = list(rval.keys())
            common_prefix = _os.path.commonprefix(keys)
            rval = {k.removeprefix(common_prefix) : rval[k] for k in rval.keys()}
        return rval
    else:
        msg = "No data to be imported."
        raise ValueError(msg)


# _rdf: pd.DataFrame to R data.frame converter (a-la dput)
# --------------------------------------------------------
def _rdf_integer(x: _pd.Series, xn: str):
    data_str = x.to_string(
        na_rep="NA",
        index=False,
        header=False,
    ).replace("\n", ", ")
    rval = f"{xn} = c({data_str})"
    return rval


# placeholder
_rdf_numeric = _rdf_integer


def _rdf_factor(x: _pd.Series, xn: str):
    # to be safe it's seems to be better rather than
    # pd.Categorical
    x = _pd.Series(x, dtype="category")
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
        labels.append(f"'{lab}'")

    levs = ", ".join(levels)
    labs = ", ".join(labels)
    levels_str = f"levels = c({levs})"
    labels_str = f"labels = c({labs})"
    rval = f"{xn} = factor({data_str}, {levels_str}, {labels_str})"
    return rval


def _rdf_object(x: _pd.Series, xn: str):
    data_l = x.to_list()
    data_l2 = []
    for s in data_l:
        if isinstance(s, str) and s != "":
            data_l2.append(f'"{s}"')
        else:
            data_l2.append("NA")
    data_str = ", ".join(data_l2)
    rval = f"{xn} = c({data_str})"
    return rval


def _rdf_bool(x: _pd.Series, xn: str):
    ft = {True: "TRUE", False: "FALSE"}
    data_str = (
        x.map(ft).to_string(
            na_rep="NA",
            index=False,
            header=False,
        ).replace("\n", ", ")
    )
    rval = f"{xn} = c({data_str})"
    return rval


def _rdf_datetime(x: _pd.Series, xn: str):
    val = ", ".join(x.dt.strftime("'%Y-%m-%d %H:%M:%S'"))
    rval = f"{xn} = c({val})"
    return rval


def _rdf(df: _pd.DataFrame, path: str | _Path, dfname: str = "df"):
    """
    pd.DataFrame to R data.frame 'converter'
    """
    path = _Path(path)

    r_code = []
    r_code.append(f"{dfname} <- data.frame(")
    for var in df.columns:
        x = df[var]
        if _pd.api.types.is_bool_dtype(x):
            r_code.append(_rdf_bool(x, var))
        elif _pd.api.types.is_integer_dtype(x):
            r_code.append(_rdf_integer(x, var))
        elif _pd.api.types.is_numeric_dtype(x):
            r_code.append(_rdf_numeric(x, var))
        elif _pd.api.types.is_categorical_dtype(x):
            r_code.append(_rdf_factor(x, var))
        elif _pd.api.types.is_datetime64_any_dtype(x):
            r_code.append(_rdf_datetime(x, var))
        elif _is_string(x):
            r_code.append(_rdf_object(x, var))
        else:
            msg = f"{var}: il tipo {x.dtype!r} non è ancora gestito."
            raise ValueError(msg)
        is_last = var == df.columns[-1]
        if not is_last:
            r_code.append(",\n")
        else:
            r_code.append(")\n")

    # fix some NA
    r_code = [line.replace("<NA>", "NA") for line in r_code]
    with path.open(mode="w") as f:
        f.writelines(r_code)


def export_data(x: _pd.DataFrame | dict[str, _pd.DataFrame],
                path: str | _Path,
                ext: str | list[str] = ["xlsx", "csv", "pkl", "R"],
                index=False,
                dfname="df"
                ) -> None:
    """Export a DataFrame or a dict of DataFrames as csv/xlsx

    In case of a dict is used and a csv path is given, the path is
    suffixed with dict names

    Parameters
    ----------
    x:
        dict of pandas.DataFrame
    fpath:
        file path, if extension is provided it will overwrite formats otherwise formats is considered
    ext:
        str or list of string with file extensions
    index:
        bool add index in exporting (typically True for results, False for data)
    """

    if not (isinstance(x, _pd.DataFrame) or isinstance(x, dict)):
        msg = "x deve essere un pd.DataFrame o un dict di pd.DataFrame"
        raise ValueError(msg)

    if isinstance(ext, str): #uniforma
        ext = [ext]

    path = _Path(path)
    path_has_suffix = path.suffix != ""
    if path_has_suffix:
        used_formats = [path.suffix.replace(".", "")]
    else:
        used_formats = ext

    if "xlsx" in used_formats:
        xlsx_path = path if path_has_suffix else path.with_suffix(".xlsx")
        with _pd.ExcelWriter(xlsx_path) as writer:
            if isinstance(x, _pd.DataFrame):
                x.to_excel(writer, sheet_name="Foglio 1", index=index)
            elif isinstance(x, dict):
                for k, v in x.items():
                    # preprocess the key of the dict, it must be an accepted excel
                    # sheetname. Trim it to the first x characters
                    k = _fix_varnames(k)[:31]
                    v.to_excel(writer, sheet_name=k, index=index)

    if "csv" in used_formats:
        if isinstance(x, _pd.DataFrame):
            x.to_csv(path if path_has_suffix else path.with_suffix(".csv"), index=index)
        elif isinstance(x, dict):
            # use dict key as postfix
            for k, v in x.items():
                csv_path = path.parent / (str(path.stem) + f"_{k}.csv")
                v.to_csv(csv_path, index=index)

    if "pkl" in used_formats:
        if isinstance(x, _pd.DataFrame):
            x.to_pickle(path if path_has_suffix else path.with_suffix(".pkl"))
        elif isinstance(x, dict):
            # use dict key as postfix
            for k, v in x.items():
                pkl_path = path.parent / (str(path.stem) + f"_{k}.pkl")
                v.to_pickle(pkl_path)

    if "R" in used_formats:
        if isinstance(x, _pd.DataFrame):
            _rdf(x,
                 path if path_has_suffix else path.with_suffix(".R"),
                 dfname
                 )
        elif isinstance(x, dict):
            # use dict key as postfix
            for k, v in x.items():
                r_path = path.parent / (str(path.stem) + f"_{k}.R")
                _rdf(v, r_path, dfname = k)


# ------------------------------------
# LaTeX stuff
# ------------------------------------
# Thanks PyLaTeX guys
_latex_special_chars = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\^{}",
    "\\": r"\textbackslash{}",
    "\n": "\\newline%\n",
    "-": r"{-}",
    "\xA0": "~",  # Non-breaking space
    "[": r"{[}",
    "]": r"{]}",
}


def _latex_escape(s):
    """
    latex_escape from PyLaTeX

    s: a str or something coercible to it
    >>> print(latex_escape("asd_foo_bar"))
    """
    string = str(s)
    return "".join(_latex_special_chars.get(c, c) for c in string)


def latex_table(
    tab,
    label: str = "",
    caption: str = "",
    position: str | None = None,
    float_format: str = "%.1f",
    column_format: str | None = None,
):
    """Print a LaTeX table

    Print a pd.DataFrame or inheriting object with to_latex method with
    sensible defaults.

    Parameters
    ----------
    tab:
        something with .to_latex method
    label: str
        posta dopo "fig:" in LaTeX
    caption: str
        caption tabella LaTeX
    position: str
        lettere posizionamento tabella (ad esempio https://stackoverflow.com/questions/1673942)

    """
    if (label == "") or (not isinstance(label, str)):
        msg = "Please provide a label for the table."
        raise ValueError(msg)
    caption = (
        label.capitalize().replace("_", " ") if caption == "" else caption
    )
    latex_caption = _latex_escape(caption)
    latex_label = "tab:" + label
    if isinstance(tab, _pd.DataFrame):
        tab.columns.name = None
    if (column_format is None) and isinstance(tab, _pd.DataFrame):
        ncols = tab.shape[1]
        column_format = "".join(["l"] + ["r"] * ncols)
    # per avere il centering è necessario impostare lo stile
    # https://pandas.pydata.org/docs/reference/api/pandas.io.formats.style.Styler.to_latex.html
    content = tab.to_latex(
        # fissi
        na_rep="",
        index=True,
        index_names=False,
        escape=True,
        # position_float='centering', # one day. maybe.
        # variabili
        label=latex_label,
        caption=latex_caption,
        position=position,
        float_format=float_format,
        column_format=column_format,
    )
    print(content)


def export_tables(tabs_dict: dict[str, _pd.DataFrame],
                  outfile: str | _Path = "outputs/tables.xlsx"):
    """Latex print and excel Export a dict of tables (caption as key)

    Parameters
    ----------
    tabs_dict:
       dict of DataFrame to be exported
    outfile:
       path to the excel file for export

    Examples
    --------
    >>> exported = {"Descrittive": desc_df, "Analisi 1"  : analysis1_df,
    >>>             "Analisi 2"  : analysis2_df}
    >>> export_tables(exported)

    """
    # excel
    export_data(tabs_dict, outfile)
    # latex
    labels = []
    for caption, tab in tabs_dict.items():
        lab = _fix_varnames(caption)
        labels.append(lab)
        latex_table(tab, label = lab, caption = caption)
    # return latex references
    refs = ["\ref{tab:" + lab + "}" for lab in labels]
    return refs
