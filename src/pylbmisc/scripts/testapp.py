from ..utils import argparser


def main():
    '''
    A test cli app with argparsing:
    usage pylbtestapp --dirs .. --lists .. --outfile ..
    '''
    opts = (
        # (param, help, default, type)
        # --dirs
        ('dirs', 'str: comma separated list of exercise source directories', '~/src/pypkg/exercises/db', str),
        # --lists
        ('lists', 'str: comma separated list of file with lists of source directories', None, str),
        # --outfile
        ('outfile', 'str:  sqlite3 db to save', '~/.exercises.db', str),
    )

    args = argparser(opts)
    dirs = args['dirs']
    dirs = dirs.split(',')
    lists = args['lists']
    lists = lists.split(',')
    outfile = args['outfile']
    print({"dirs": dirs, "lists": lists, "outfile": outfile})
    return 0
