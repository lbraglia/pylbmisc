import argparse
from ..dnd import srd


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("srd", type=str, help="srd term to be printed")
    args = argparser.parse_args()
    srd(args.srd)
