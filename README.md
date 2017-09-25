# Neko language statistics tool for Python projects.
Following instruments is able to calulate some word-metrics for python project.

### Usage
`python3 -m nekolrep <PATH_TO_GITHUB_REPO>`

See builtin help for arguments.

### Installation
`python3 setup.py install` or alternatively `pip3 install .`

### Dependencies
Python3, `nltk` -- Natural Language Toolkit, `GitPython` -- git library

### Features
CLI tool, presenting reports in different formats (plain text, csv, json) over statistics of natural language words in Python project.
This includes statistics over most common verbs or nouns in function names or identifiers (use -l to narrow down to local only).
