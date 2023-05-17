import os as _os
import pandas as _pd
import zipfile as _zipfile
import tempfile as _tempfile

def data_import(fpaths):
    '''
    import data from several filepaths (supported formats: .csv .xls .xlsx .zip) and return a dict of DataFrame
    '''
    # import ipdb
    # ipdb.set_trace()
    accepted_fpaths = [f for f in fpaths
                       if _os.path.splitext(f)[1].lower() in {".csv", ".xls", ".xlsx", ".zip"}]
    rval = {}
    for fpath in accepted_fpaths:
        fname = _os.path.splitext(_os.path.basename(fpath))[0]
        fext = _os.path.splitext(fpath)[1].lower()
        if fext == '.csv':
            dfname = fname
            data = _pd.read_csv(fpath)
            if dfname not in rval.keys():  #check for duplicates
                rval[dfname] = data
            else:
                raise Warning("{0} is probably duplicated, skipping to avoid overwriting ".format(dfname))
        elif fext in {'.xls', '.xlsx'}:
            data = _pd.read_excel(fpath, None) # import all the sheets as a dict of DataFrame
            data = {"{0}_{1}".format(fname, k): v for k, v in data.items()} # add xlsx to sheet names
            rval.update(data)
        elif fext == '.zip': # unzip in temporary directory and go by recursion
            with _tempfile.TemporaryDirectory() as tempdir:
                with _zipfile.ZipFile(fpath) as myzip:
                    myzip.extractall(tempdir)
                    zipped_fpaths = [_os.path.join(tempdir, f) for f in _os.listdir(tempdir)]
                    zipped_data = data_importer(zipped_fpaths)
            # prepend zip name to fname (as keys) and update results
            zipped_data = { "{0}_{1}".format(fname, k) : v for k, v in zipped_data.items()}
            rval.update(zipped_data)
        else:
            raise Warning("Format not supported for {0}. It must be a .csv, .xls, .xlsx, .zip. Ignoring it.".format(f))
    if len(rval):
        return(rval)
    else:
        raise ValueError("No data to be imported.")
        
def data_export(dfs, outfile): 
    '''
    export a dict of DataFrame as a single excel file

    dfs: dict of pandas.DataFrame
    outfile: outfile path
    '''
    with _pd.ExcelWriter(outfile) as writer:
        for k,v in dfs.items():
            v.to_excel(writer, sheet_name = k)



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
