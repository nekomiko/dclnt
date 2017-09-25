from nekolrep.nekolrep import ReportGenerator
import os


def print_proj_stats():
    '''Prints verbs and funcion names statistics for
    predefined project found in current directory'''

    project = 'nekolrep'
    path = os.path.join('.', project)
    proj_rep = ReportGenerator(path)
    print(proj_rep.generate("json", "func", "VB"))
    print(proj_rep.generate("csv", "func"))
    print(proj_rep.generate("console", "name", "NN", ["locals"]))

if __name__ == "__main__":
    print_proj_stats()
