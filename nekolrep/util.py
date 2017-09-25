import collections


# Trivial helper functions.
def flat(_list):
    """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in _list], [])


def get_top(_iter, top_size=10):
    '''Count most common entries of _iter'''
    return collections.Counter(_iter).most_common(top_size)
