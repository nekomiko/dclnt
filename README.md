# Natural language statistics tool for Python projects.
Following instruments is able to calulate some word-metrics for python project.
### Usage
Statistics is calculated by PyWordStat class like following:
```
django_stat = PyWordStat("lib/python3.5/site-packages/django")
print(django_stat.get_top_verbs())
```

### Features
This tool is able to deliver following information:
* `get_top_verbs` -- statistics of most common verbs in function names in project
* `get_top_functions_names` -- statistics of most common function names in project
* `get_all_verbs` -- list of all verbs occuring in function names of project
* `get_all_function_names` -- list of all function names in project

### Dependencies
Python3, `nltk` -- Natural Language Toolkit
