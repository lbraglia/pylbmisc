import argparse
import subprocess

from datetime import date
from pathlib import Path

oggi = date.today()


def main():
    '''Crea un file di appunti con la data di oggi e il
    formato specificato come primo parametro'''

    parser = argparse.ArgumentParser()
    parser.add_argument("fmt")
    args = parser.parse_args()

    # arguments checking
    prefix = oggi.isoformat()

    # gogogo
    outfile = Path(prefix + "." + args.fmt)
    subprocess.run(["touch", outfile])
    subprocess.Popen(["emacs", outfile])
    return
