from nltk import pos_tag
import collections
import ast


# Trivial helper functions.
def flat(_list):
    """ [(1,2), (3,4)] -> [1, 2, 3, 4]"""
    return sum([list(item) for item in _list], [])


def is_magic_method(f):
    return f.startswith('__') and f.endswith('__')


def is_func(node):
    return isinstance(node, ast.FunctionDef)


def is_name(node):
    return isinstance(node, ast.Name)


def check_word_ps(word, ps=None):
    '''Checks if word belongs to specified part of speech
    VB - verb
    NN - noun'''
    if not word:
        return False
    pos_info = pos_tag([word])
    if ps is None:
        return True
    return pos_info[0][1] == ps


def get_top(_iter, top_size=10):
    '''Count most common entries of _iter'''
    return collections.Counter(_iter).most_common(top_size)
