import argparse
from ..dnd import ita2eng as _ita2eng
from ..dnd import eng2ita as _eng2ita

def ita2eng():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("term", type=str, help="italian term to translate")
    args = argparser.parse_args()
    ita = args.term
    _ita2eng(ita)

def eng2ita():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("term", type=str, help="english term to translate")
    args = argparser.parse_args()
    eng = args.term
    _eng2ita(eng)
