import ast
import os
from itertools import chain
from logging import debug

from git import Repo, GitCommandError
from .util import flat, is_name, is_magic_method, \
        check_word_ps, is_func, get_top


class BaseWordStat:
    '''Common interface for statistics calculation.
    Assumes _tree_nodes method returns iterator of AST nodes'''

    def get_name_all(self, _locals=False):
        '''Returns generator of all identifiers names in project,
        local_asg: optionally only local variables'''
        def local_filter(node):
            return isinstance(node.ctx, ast.Store)

        def always_true(node):
            return True

        filter_names = local_filter if _locals else always_true
        return (node.id for node in self._tree_nodes()
                if is_name(node) and filter_names(node))

    def extract_words_from_ids(self, ident, ps):
        '''Extracts words by splitting identifiers
        and filters part of speech specified by `ps`'''
        all_names = (f for f in ident
                     if not is_magic_method(f))

        def split_and_check(name):
            return [word for word in name.split('_')
                    if word and check_word_ps(word, ps)]
        return flat([split_and_check(name) for name in all_names])

    def get_name_sample(self, ps=None, _locals=False):
        '''Get names of identifiers, filter out specified
        part of speech(`ps`), local variables (`_locals`)'''
        return self.extract_words_from_ids(self.get_name_all(_locals), ps)

    def get_func_all(self):
        '''Get iterator of all nonmagic functions'''
        return (node.name.lower() for node in self._tree_nodes()
                if is_func(node) and (not is_magic_method(node.name)))

    def get_func_sample(self, ps=None):
        '''Returns list of all `ps` part of speech occuring
        as word in function names of project'''
        return self.extract_words_from_ids(self.get_func_all(), ps)

    def get_top_func_all(self, top_size=10):
        '''Returns statistics of most common function names
        in project'''
        return get_top(self.get_all_func(), top_size)

    def get_sample_generic(self, sample_sort="func", ps=None, param={}):
        '''Generic interface to all statistics (word lists)'''
        if sample_sort == "func":
            if ps is not None:
                return self.get_func_sample(ps)
            else:
                return self.get_func_all()
        elif sample_sort == "name":
            if ps is not None:
                return self.get_name_sample(ps, "locals" in param)
            else:
                return self.get_name_all("locals" in param)

    def get_top_generic(self, sample_sort, ps=None, param={}, top_size=10):
        '''Generic interface to all statistics'''
        return get_top(self.get_sample_generic(sample_sort, ps, param),
                       top_size)


class LocalPyWordStat(BaseWordStat):
    '''Calculates statistics for python project
    given as a directory on disk'''

    def __init__(self, path):
        '''path: path to python project for which calculate statistics'''
        self.path = path

    def get_project_files(self, ext='.py'):
        '''Walks trough `self.path` and returns list of all files
        which ends with `ext`'''
        filenames = []
        for dirname, dirs, files in os.walk(self.path, topdown=True):
            for file in files:
                if file.endswith(ext):
                    filenames.append(os.path.join(dirname, file))
        return filenames

    def parse_file(self, filename):
        '''Returns parsed AST of python file'''
        tree = None
        with open(filename, 'r', encoding='utf-8') as attempt_handler:
            main_file_content = attempt_handler.read()
        try:
            tree = ast.parse(main_file_content)
        except SyntaxError as e:
            debug(e)
            tree = None
        return tree

    def get_trees(self):
        '''Returns list of abstract syntax trees
        for every .py file in self.path.'''
        filenames = self.get_project_files()
        debug('total {} files'.format(len(filenames)))
        trees = (self.parse_file(filename) for filename in filenames)
        trees = [t for t in trees if t]
        debug('trees generated')
        return trees

    def _trees(self):
        if not hasattr(self, '_trees_cache'):
            self._trees_cache = self.get_trees()
        return self._trees_cache

    def _tree_nodes(self):
        return chain(*(ast.walk(t) for t in self._trees()))


class RemotePyWordStat(LocalPyWordStat):
    '''Python project statistics class with remote repo support'''
    def __init__(self, repo_path):
        if repo_path.startswith(("http://", "https://", "ssh://")):
            repo_path = repo_path.strip("/")
            path = os.path.join(os.getcwd(), repo_path.split("/")[-1])
            try:
                Repo.clone_from(repo_path, path)
            except GitCommandError:
                debug("{} already exists, skipping".format(path))
        else:
            path = repo_path
        super().__init__(path)
