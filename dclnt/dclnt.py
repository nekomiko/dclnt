import ast
import os
import collections
from itertools import chain

from nltk import pos_tag, download, data
from git import Repo, GitCommandError


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


# def is_noun(word):
#    return check_word_ps(word, "NN")


# def is_verb(word):
#    return check_word_ps(word, "VB")


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
    return collections.Counter(_iter).most_common(top_size)


class BaseWordStat:
    '''Common interface for statistics calculation.
    Assumes _tree_nodes method returns iterator of AST nodes'''
    def get_name_all(self, local_asg=False):
        '''Returns generator of all identifiers names in project,
        optionally only assignments'''
        def asg_filter(node):
            return isinstance(node.ctx, ast.Store)

        def always_true(node):
            return True
        if local_asg:
            filter_names = asg_filter
        else:
            filter_names = always_true
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

    def get_name_sample(self, ps=None, local_asg=False):
        return self.extract_words_from_ids(self.get_name_all(local_asg), ps)

    def get_func_all(self):
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

    def get_sample_generic(self, sample_sort, ps=None, param={}):
        if sample_sort == "func_split":
            return self.get_func_sample(ps)
        elif sample_sort == "name_split":
            return self.get_name_sample(ps, "local" in param)
        elif sample_sort == "func_whole":
            return self.get_func_all()

    def get_top_generic(self, sample_sort, ps=None, param={}, top_size=10):
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
            print(e)
            tree = None
        return tree

    def get_trees(self):
        '''Returns list of abstract syntax trees
        for every .py file in self.path.'''
        filenames = self.get_project_files()
        print('total {} files'.format(len(filenames)))
        trees = (self.parse_file(filename) for filename in filenames)
        trees = [t for t in trees if t]
        print('trees generated')
        return trees

    def _trees(self):
        # Caching
        if not hasattr(self, '_trees_cache'):
            self._trees_cache = self.get_trees()
        return self._trees_cache

    def _tree_nodes(self):
        return chain(*(ast.walk(t) for t in self._trees()))


class RemotePyWordStat(LocalPyWordStat):
    def __init__(self, repo_path):
        if repo_path.startswith("http://") or \
                repo_path.startswith("https://") or \
                repo_path.startswith("ssh://"):
            repo_path = repo_path.strip("/")
            path = os.path.join(os.getcwd(), repo_path.split("/")[-1])
            try:
                Repo.clone_from(repo_path, path)
            except GitCommandError:
                print("{} already exists, skipping".format(path))
        else:
            path = repo_path
        super().__init__(path)


class ReportGenerator:
    def __init__(self, word_stat):
        if isinstance(word_stat, BaseWordStat):
            self.word_stat = word_stat
        elif isinstance(word_stat, str):
            self.word_stat = RemotePyWordStat(word_stat)

    def generate(self, format="console", sample_sort="func_split",
                 ps="VB", param={}, top_size=10):
        words = list(self.word_stat.get_sample_generic(sample_sort, ps, param))
        if format == "console":
            out_s = 'total {} words, {} unique'
            print(out_s.format(len(words), len(set(words))))
            for word, occurence in get_top(words, top_size):
                print(word, occurence)


def print_proj_stats():
    '''Prints verbs and funcion names statistics for
    predefined set of projects found in current directory'''

    project = 'django'
    path = os.path.join('.', project)
    proj_rep = ReportGenerator(path)
    proj_rep.generate("console", "func_split", "VB")
    proj_rep.generate("console", "func_whole")
    proj_rep.generate("console", "name_split", "NN", ["local"])

# Download NLTK package if not installed
if not data.find('taggers/averaged_perceptron_tagger'):
    download('averaged_perceptron_tagger')

if __name__ == "__main__":
    print_proj_stats()
