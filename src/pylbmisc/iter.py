"""Some iterators remembering R"""

from typing import Any as _Any
from typing import Iterator as _Iterator


def unique(x) -> _Iterator[_Any]:
    '''
    return a stream of unique items contained in x
    '''
    seen = set()
    for item in x:
        if item in seen:
            pass
        else:
            seen.add(item)
            yield item


# minor diffs from 1.10 of python cookbook
def duplicated(x) -> _Iterator[bool]:
    '''
    return a stream of logical value (already seen element)
    '''
    seen = set()
    for item in x:
        if item in seen:
            yield True
        else:
            seen.add(item)
            yield False


if __name__ == "__main__":
    alist = [1, 2, 1, 3]
    print(list(duplicated(alist)))
