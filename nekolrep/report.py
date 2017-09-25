import json
import csv
import io

from .nekolrep import BaseWordStat, RemotePyWordStat
from .util import get_top


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
        top_words = get_top(words, top_size)
        if format == "console":
            output_l = []
            out_s = 'total {} words, {} unique'
            output_l.append(out_s.format(len(words), len(set(words))))
            for word, occurence in top_words:
                output_l.append("{} {}".format(word, occurence))
            return "\n".join(output_l)
        if format == "json":
            json_summ = {"total": len(words), "unique": len(set(words))}
            json_stat = top_words
            json_dict = {"summary": json_summ, "statistics": json_stat}
            return json.dumps(json_dict)
        if format == "csv":
            output = io.StringIO()
            csvdata = top_words
            writer = csv.writer(output)
            writer.writerows(csvdata)
            return output.getvalue()
