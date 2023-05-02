def unique(x):
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
def duplicated(x):
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
            
if __name__ == '__main__':
    l = [1,2,1,3]
    print(list(duplicated(l)))
