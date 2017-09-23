# Natural language statistics tool for Python projects.
Following instruments is able to calulate some word-metrics for python project.

### Usage
Statistics are calculated by PyWordStat class like following:
```
from dclnt.dclnt import PyWordStatLocal
django_stat = PyWordStat("lib/python3.5/site-packages/django")
print(django_stat.get_func_sample("VB"))
```

### Dependencies
Python3, `nltk` -- Natural Language Toolkit
