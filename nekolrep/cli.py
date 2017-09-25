import sys
import argparse

from .nekolrep import ReportGenerator, RemotePyWordStat
from nltk import download, data

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
