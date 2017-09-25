import ast
import os
from itertools import chain
from logging import debug

from git import Repo, GitCommandError

from .util import get_top
from . import pystat


class BaseWordStat:
    '''Common interface for statistics calculation
    self.get_tree_nodes should be implemented by subclass
    self.stat should point to object implementing
    interface similar to pystat module'''
    def get_tree_nodes():
        raise NotImplementedError

    def get_sample_generic(self, sample_sort="func", ps=None, param={}):
        '''Generic interface to all statistics (word lists)
        sample_sort: type of sample
            func - get sample of function names
            name - get sample of identifiers
        ps: part of speech to filter
            VB - verbs
            NN - nouns
        params: list of additinal parameters and flags
            locals - view only local variables'''
        tree_nodes = self.get_tree_nodes()
        if sample_sort == "func":
            if ps is not None:
                return self.stat.get_func_sample(tree_nodes, ps)
            else:
                return self.stat.get_func_all(tree_nodes)
        elif sample_sort == "name":
            if ps is not None:
                return self.stat.get_name_sample(tree_nodes, ps, "locals" in param)
            else:
                return self.stat.get_name_all(tree_nodes, "locals" in param)

    def get_top_generic(self, sample_sort, ps=None, param={}, top_size=10):
        return get_top(self.get_sample_generic(sample_sort, ps, param),
                       top_size)


class LocalPyWordStat(BaseWordStat):
    '''Calculates statistics for path of python project'''

    def __init__(self, path):
        '''path: path to python project for which statistics calculated'''
        self.path = path
        self.stat = pystat  

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
        '''Returns parsed AST of from python file'''
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

    def get_tree_nodes(self):
        if not hasattr(self, '_trees_cache'):
            self._trees_cache = self.get_trees()
        return chain(*(ast.walk(t) for t in self._trees_cache))


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
