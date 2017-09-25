import ast
from nltk import pos_tag
from .util import flat


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


def get_name_all(tree_nodes, _locals=False):
    '''Returns generator of all identifiers names in project,
     _locals: only local variables'''
    def local_filter(node):
        return isinstance(node.ctx, ast.Store)

    def always_true(node):
        return True

    filter_names = local_filter if _locals else always_true
    return (node.id for node in tree_nodes
            if is_name(node) and filter_names(node))


def extract_words_from_ids(ident, ps):
    '''Extracts words by splitting identifiers
    and filters part of speech specified by `ps`'''
    all_names = (f for f in ident
                 if not is_magic_method(f))

    def split_and_check(name):
        return [word for word in name.split('_')
                if word and check_word_ps(word, ps)]
    return flat([split_and_check(name) for name in all_names])


def get_name_sample(tree_nodes, ps=None, _locals=False):
    '''Returns list of all `ps` part of speech occuring
    as word in identifiers or only local variables (`_locals`)'''
    return extract_words_from_ids(get_name_all(tree_nodes, _locals), ps)


def get_func_all(tree_nodes):
    '''Get iterator of all nonmagic functions'''
    return (node.name.lower() for node in tree_nodes
            if is_func(node) and (not is_magic_method(node.name)))


def get_func_sample(tree_nodes, ps=None):
    '''Returns list of all `ps` part of speech occuring
    as word in function names of project'''
    return extract_words_from_ids(get_func_all(tree_nodes), ps)
