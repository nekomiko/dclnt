import json
import csv
import io

from .nekolrep import BaseWordStat, RemotePyWordStat
from .nekolrep import get_top


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
