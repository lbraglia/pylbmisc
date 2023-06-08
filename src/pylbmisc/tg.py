def chat2df(fpath):
    '''

    fpath: Path to a json export of a telegram chat
    '''
    with fpath.open() as f:
        js = json.load(f)
        msg = js["messages"]
        return pd.DataFrame(msg)
