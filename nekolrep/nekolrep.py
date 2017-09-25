import ast
import os
import sys
import argparse
import collections
from itertools import chain
import json
import csv
import io
from logging import debug

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


class ReportGenerator:
    '''Report generator for BaseWordStat'''
    def __init__(self, word_stat):
        if isinstance(word_stat, BaseWordStat):
            self.word_stat = word_stat
        elif isinstance(word_stat, str):
            self.word_stat = RemotePyWordStat(word_stat)

    def generate(self, format="console", sample_sort="func",
                 ps="VB", param={}, top_size=10):
        '''Generator of all reports'''
        words = list(self.word_stat.get_sample_generic(sample_sort, ps, param))
        if format == "console":
            output_l = []
            out_s = 'total {} words, {} unique'
            output_l.append(out_s.format(len(words), len(set(words))))
            for word, occurence in get_top(words, top_size):
                output_l.append("{} {}".format(word, occurence))
            output_l.append("")
            return "\n".join(output_l)
        if format == "json":
            json_summ = {"total": len(words), "unique": len(set(words))}
            json_stat = get_top(words, top_size)
            json_dict = {"summary": json_summ, "statistics": json_stat}
            return json.dumps(json_dict)
        if format == "csv":
            output = io.StringIO()
            csvdata = get_top(words, top_size)
            writer = csv.writer(output)
            writer.writerows(csvdata)
            return output.getvalue()


def parse_args():
    '''Parses argruments of report generator'''
    parser = argparse.ArgumentParser(description="NekoLRep cli")
    path_help = "Link to git repo or local filepath."
    parser.add_argument("path", help=path_help)
    type_help = '''Type of report:
    `func` over function names, `name` over all identifiers'''
    parser.add_argument("-t", dest="type", help=type_help)
    word_help = '''Report over specific type of words (parts of speech):
    `noun` - nouns, `verb` - verbs'''
    parser.add_argument("-w", dest="word", help=word_help)
    help_locals = "Report over local variables (only with -t name)"
    parser.add_argument("-l", dest="locals", action="store_true",
                        help=help_locals)
    help_format = "Report output format: console, json, csv"
    parser.add_argument("-f", dest="format", help=help_format)
    help_output = "Output file, stdout if none"
    parser.add_argument("-o", dest="output", help=help_output)
    help_size = "Size of the top"
    parser.add_argument("-s", dest="top_size", help=help_size)
    return parser.parse_args().__dict__


def get_report_param_from_args(args):
    def get_arg(key, default=None, choice=None):
        res = default
        if args[key] is not None:
            if choice is None:
                res = args[key]
            elif args[key] in choice:
                res = args[key]
        return res

    '''Converts cli arguments to parameters for ReportGenerator'''
    path = get_arg("path", "")
    sample_sort = get_arg("type", "func", ["func", "name"])
    ps = get_arg("word", None, ["noun", "verb"])
    word_map = {"noun": "NN", "verb": "VB"}
    ps = word_map.get(ps)
    param = []
    if sample_sort == "name":
        if args["locals"]:
            param = ["locals"]
    format = get_arg("format", "console", ["console", "json", "csv"])
    output = get_arg("output")
    top_size = 10
    if args["top_size"] is not None:
        try:
            top_size = int(args["top_size"])
        except ValueError:
            pass
    return (path, [format, sample_sort, ps, param, top_size], output)


def main():
    args = parse_args()
    path, rep_params, output = get_report_param_from_args(args)
    rep_gen = ReportGenerator(RemotePyWordStat(path))
    if output:
        f = open(output, "w")
    else:
        f = sys.stdout
    f.write(rep_gen.generate(*rep_params))
    if f is not sys.stdout:
        f.close()


def download_nltk_dependency():
    # Download NLTK package if not installed
    if not data.find('taggers/averaged_perceptron_tagger'):
        download('averaged_perceptron_tagger')

if __name__ == "__main__":
    # print_proj_stats()
    download_nltk_dependency()
    main()
