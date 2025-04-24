"""
Class and utilities for randomization

The main class is List which produces a blocked randomizzation list with
optional stratification by several factors.
"""

from pylbmisc.r import expand_grid as _expand_grid
import numpy as _np
import pandas as _pd
from itertools import permutations as _permutations
from itertools import repeat as _repeat
from pathlib import Path as _Path
from pprint import pp as _pp
from pprint import pformat as _pformat


class List:
    """Stratified/blocked randomization list generation

    Examples
    --------
    >>> # i centri debbono essere il PRIMO criterio di stratificazione
    >>> # altrimenti l'aggiunta di centri in corso dello studio può incasinare
    >>> # la randomizzazione (delle liste gia fatte)
    >>> strata = {"centres": ["ausl_re", "ausl_mo"],
    ...           "agecl": ["<18", "18-65", ">65"]}
    >>> a = lb.rand.List(seed=354, n = 100, strata=strata)
    >>> a.stats()
    >>> a.to_txt() # <- in "/tmp"
    >>> a.to_csv() # <- in "/tmp"
    """

    def __init__(self,
                 seed=None,
                 groups=["Control", "Experimental"],  # example 1:1 ratio with
                 reps=[1, 2, 3],                      # blocks 2, 4 or 6
                 n=100,                               # trial sample size
                 strata={"centres": ["ausl_re"]}):
        if seed is None:
            msg = "Must specify a seed."
            raise ValueError(msg)
        self._rng = _np.random.default_rng(seed=seed)
        self._n = n
        self._strata_df = _expand_grid(strata)
        # sample blocks to be permuted eg [["C", "T"], ["C", "T", "C", "T"],
        # ["C", "T", "C", "T", "C", "T"]]
        blocks = []
        for rep in reps:
            blocks.append(groups * rep)
        # Actual length: eg [2, 4, 6]
        self._blocks_len = [len(b) for b in blocks]
        # Pool of all the permutations to be used to pick one
        pool = []
        for block in blocks:
            # do permutations, use set to remove duplicates and list to sort
            unique_block_perms = list(set(_permutations(block)))
            unique_block_perms.sort()
            pool.append(unique_block_perms)
        self._pool = pool
        # Actually generate and store the randomization list
        randlist = []
        for _, row in self._strata_df.iterrows():
            randlist.append({
                "strata": row,
                "rl": self._generate_strata_list()})
        self._randlist = randlist

    def _generate_strata_list(self):
        actual_n = 0
        block_id = 0
        unit_id = 0
        strata_randlist = []
        while (actual_n < self._n):
            # increase counter of randomized blocks
            block_id += 1
            # select a random len
            block_sel = int(self._rng.integers(len(self._blocks_len)))
            # obtain the actual len
            block_dim = self._blocks_len[block_sel]
            # how many permutations are available for a given dim
            n_avail = len(self._pool[block_sel])
            chosen_block = int(self._rng.integers(n_avail))  # chose one
            sampled_block = self._pool[block_sel][chosen_block]   # which one
            actual_n += block_dim                       # add to sample size
            for b_id, b_dim, trt in zip(_repeat(block_id),  # create the df
                                        _repeat(block_dim),
                                        sampled_block):
                unit_id += 1
                strata_randlist.append({
                    "unit": unit_id,
                    "block": b_id,
                    "block_dim": b_dim,
                    "trt": trt
                })
        return _pd.DataFrame(strata_randlist)

    def stats(self):
        """Print stats of the randomization list"""
        stratas_stats = []  # list of dicts
        for stratalist in self._randlist:
            strata = stratalist["strata"]
            rl = stratalist["rl"]
            strata_string = "_".join(strata.to_list())
            rval = {
                "strata": strata_string,
                "n": rl.shape[0],
                "n_blocks": len(rl.block.unique()),
                "overall_balance": len(rl.trt.value_counts().unique()) == 1,
                "block_balance": _pd.crosstab(rl.block, rl.trt).apply(
                    # all the rows must have the same frequencies
                    axis="columns",  # apply the function by row
                    func=lambda x: len(x.unique()) == 1,  # check row same freq
                    ).all()}  # return True if all check are ok
            stratas_stats.append(rval)
        stratas_stats = _pd.DataFrame(stratas_stats)
        with _pd.option_context("display.max_rows", None,
                                "display.max_columns", None):
            print(stratas_stats)

    def __repr__(self):
        with _pd.option_context("display.max_rows", None,
                                "display.max_columns", None):
            return _pformat(self._randlist, indent=0, sort_dicts=False)

    def to_txt(self,
               fpath: str | _Path = _Path("/tmp/randomization_list.txt")
               ) -> None:
        """Export randomization list to text file

        param:
        fpath: file path
        """
        with _Path(fpath).open("w") as f:
            # print all the rows thanks
            with _pd.option_context("display.max_rows", None,
                                    "display.max_columns", None):
                for stratalist in self._randlist:
                    print("-" * 82, file=f)
                    _pp(stratalist["strata"], stream=f)
                    print("", file=f)
                    _pp(stratalist["rl"], stream=f)
                    print("", file=f)

    def to_csv(self, dpath: str | _Path = "/tmp/"
               ) -> None:
        """Export randomization lists to csv(s) in a directory

        param:
        dpath: the directory path
        """
        dpath = _Path(dpath)
        for stratalist in self._randlist:
            strata = stratalist["strata"]
            strata_string = "_".join(strata.to_list())
            actual_path = dpath / f"{strata_string}.csv"
            stratalist["rl"].to_csv(actual_path, index=False)


if __name__ == "__main__":
    # i centri debbono essere il PRIMO criterio di stratificazione altrimenti
    # l'aggiunta di centri in corso dello studio può incasinare la
    # randomizzazione (delle liste gia fatte)
    strata = {"centres": ["ausl_re", "ausl_mo", "ausl_bo"],
              "agecl": ["lt_18", "18_65", "gt_65"]}
    a = List(seed=354, strata=strata)
    a.stats()
    a.to_txt()  #<- in /tmp
    a.to_csv()  #<- in /tmp
