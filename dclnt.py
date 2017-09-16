import ast
import os
import collections
from itertools import chain

from nltk import pos_tag, download, data


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


def is_verb(word):
    if not word:
        return False
    pos_info = pos_tag([word])
    return pos_info[0][1] == 'VB'


def get_top(iter, top_size=10):
        return collections.Counter(iter).most_common(top_size)


class PyWordStat:
    '''Calculates statistics for python project
    given as a directory on disk'''

    def __init__(self, path):
        '''path: path to python project for which calculate statistics'''
        self.path = path

    def get_trees(self, with_filenames=False, with_file_content=False):
        '''Returns list of abstract syntax trees
        for every .py file in self.path.
        If any of boolean parameters are true
        returns list of tuples in order (file_name, file_content, tree)
        with_filenames: include file_name
        with_file_content: include file content'''
        filenames = []
        trees = []
        for dirname, dirs, files in os.walk(self.path, topdown=True):
            for file in files:
                if file.endswith('.py'):
                    filenames.append(os.path.join(dirname, file))
                    # if len(filenames) == 100:
                    #    break
        print('total %s files' % len(filenames))
        for filename in filenames:
            with open(filename, 'r', encoding='utf-8') as attempt_handler:
                main_file_content = attempt_handler.read()
            try:
                tree = ast.parse(main_file_content)
            except SyntaxError as e:
                print(e)
                tree = None
            if with_filenames or with_file_content:
                t_tree = (tree,)
                if with_file_content:
                    t_tree = (main_file_content, ) + t_tree
                if with_filenames:
                    t_tree = (filename, ) + t_tree
                trees.append(t_tree)
            else:
                trees.append(tree)
        print('trees generated')
        return trees

    def _trees(self):
        # Caching
        if not hasattr(self, '_trees_cache'):
            self._trees_cache = [t for t in self.get_trees() if t]
        return self._trees_cache

    def _tree_nodes(self):
        return chain(*(ast.walk(t) for t in self._trees()))

    def get_all_names(self):
        '''Returns list of all identifiers names in project'''
        return [node.id for node in self._tree_nodes() if is_name(node)]

    def get_all_words(self):
        '''Returns list of all words occuring in identifiers'''
        function_names = [f for f in self.get_all_names()
                          if not is_magic_method(f)]

        def split_snake_case_name_to_words(name):
            return [n for n in name.split('_') if n]
        return flat([split_snake_case_name_to_words(function_name)
                     for function_name in function_names])

    def get_all_verbs(self):
        '''Returns list of all verbs occuring in
        function names of project'''
        def get_verbs_from_function_name(function_name):
            return [word for word in function_name.split('_')
                    if is_verb(word)]

        func_names = [node.name.lower() for node in self._tree_nodes()
                      if is_func(node) and (not is_magic_method(node.name))]
        print('functions extracted')
        verbs = flat([get_verbs_from_function_name(function_name)
                     for function_name in func_names])
        return verbs

    def get_top_verbs(self, top_size=10):
        '''Returns statistics of most common verbs in function names
        in project'''
        return get_top(self.get_all_verbs(), top_size)

    def get_all_functions_names(self, top_size=10):
        '''Returns list of all function names in project'''
        func = [node.name.lower() for node in self._tree_nodes()
                if is_func(node) and (not is_magic_method(node.name))]
        return func

    def get_top_functions_names(self, top_size=10):
        '''Returns statistics of most common function names
        in project'''
        return get_top(self.get_all_functions_names(), top_size)


def print_proj_stats():
    '''Prints verbs and funcion names statistics for
    predefined set of projects found in current directory'''

    def print_word_stat(words, top_size):
        print('total %s words, %s unique' % (len(words), len(set(words))))
        for word, occurence in get_top(words, top_size):
            print(word, occurence)

    projects = [
            'dclnt',
            'django',
            'flask',
            'pyramid',
            'reddit',
            'requests',
            'sqlalchemy',
    ]
    p_verbs = []
    p_func = []
    for project in projects:
        path = os.path.join('.', project)
        proj_stat = PyWordStat(path)
        p_verbs += proj_stat.get_all_verbs()
        p_func += proj_stat.get_all_functions_names()

    top_size = 25
    print('verbs statistics')
    print_word_stat(p_verbs, top_size)
    print('function name statistics')
    print_word_stat(p_func, top_size)

# Download NLTK package if not installed
if not data.find('taggers/averaged_perceptron_tagger'):
    download('averaged_perceptron_tagger')

if __name__ == "__main__":
    print_proj_stats()
