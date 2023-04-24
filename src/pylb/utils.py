import argparse

def argparser(opts):
    'Helper function for argument parsing.'
    parser = argparse.ArgumentParser()
    defaults = {}
    for i in opts:
        optname = i[0]
        optdescription = i[1]
        optdefault = i[2]
        opttype = i[3]
        # create help string and add argument to parsing
        help_string = '{0} (default: {1})'.format(optdescription,
                                                  str(optdefault))
        parser.add_argument('--' + optname, help = help_string, type = str)
    # do parsing
    args = vars(parser.parse_args()) #vars to change to a dict
    # defaults settings and types management
    for i in opts:
        optname = i[0]
        optdescription = i[1]
        optdefault = i[2]
        opttype = i[3]
        # se il valore è a none in args impostalo al valore di default
        # specificato
        if (args[optname] is None):
            args[optname] = optdefault
        # se il tipo è logico sostituisci un valore possibile true con
        # l'equivalente python
        if (opttype == bool):
            # mv to character if not already (not if used optdefault)
            args[optname] = str(args[optname])
            true_values = ('true', 'True', 'TRUE', 't', 'T', '1', 'y', 'Y',
                           'yes', 'Yes', 'YES') 
            if (args[optname] in true_values):
                args[optname] = 'True'
            else:
                args[optname] = ''
        # converti il tipo a quello specificato
        args[optname] = opttype(args[optname])
    return(args)


def __test(opts):
    args = argparser(opts)
    print(args)

if __name__ == '__main__':
    opts = (
        ('download', 'a True default', True, bool),
        ('another_option', 'a false default', False, bool),
        ('years', 'integer: years to be downloaded (PagesList)', 1998, int),
        ('eds', 'str: edition/s to be downloaded (comma separated)',
         'SE,SSE', str), 
    )
    __test(opts)
