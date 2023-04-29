import os
import pandas as pd
from zipfile import ZipFile
from tempfile import TemporaryDirectory

def data_importer(fpaths):
    '''
    import data from several filepaths (supported formats: .csv .xls .xlsx .zip) and return a dict of DataFrame
    '''
    # import ipdb
    # ipdb.set_trace()
    accepted_fpaths = [f for f in fpaths
                       if os.path.splitext(f)[1].lower() in {".csv", ".xls", ".xlsx", ".zip"}]
    rval = {}
    for fpath in accepted_fpaths:
        fname = os.path.splitext(os.path.basename(fpath))[0]
        fext = os.path.splitext(fpath)[1].lower()
        if fext == '.csv':
            dfname = fname
            data = pd.read_csv(fpath)
            if dfname not in rval.keys():  #check for duplicates
                rval[dfname] = data
            else:
                raise Warning("{0} is probably duplicated, skipping to avoid overwriting ".format(dfname))
        elif fext in {'.xls', '.xlsx'}:
            data = pd.read_excel(fpath, None) # import all the sheets as a dict of DataFrame
            data = {"{0}_{1}".format(fname, k): v for k, v in data.items()} # add xlsx to sheet names
            rval.update(data)
        elif fext == '.zip': # unzip in temporary directory and go by recursion
            with TemporaryDirectory() as tempdir:
                with ZipFile(fpath) as myzip:
                    myzip.extractall(tempdir)
                    zipped_fpaths = [os.path.join(tempdir, f) for f in os.listdir(tempdir)]
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
        
def export_data(dfs, outfile): 
    '''
    export a dict of DataFrame as a single excel file

    dfs: dict of pandas.DataFrame
    outfile: outfile path
    '''
    with pd.ExcelWriter(outfile) as writer:
        for k,v in dfs.items():
            v.to_excel(writer, sheet_name = k)

# res = data_importer(['/tmp/asd.csv', '/tmp/bar.csv', '/tmp/ajeje.zip', '/tmp/test.xlsx'])

# len(res)

# df = pd.read_excel("/tmp/test.xlsx", None)
# for k, v in df.items():
#     print(type(v))
