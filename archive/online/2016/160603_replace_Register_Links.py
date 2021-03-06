# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re



fit_numbers = re.compile("(?:''')?(\d{1,3}[a-z]?\))") #matches all numbers
fit_numbers_not_linked = re.compile(" (?:''')?(\d{1,3}[a-z]?\))") #matches only the numbers no already linked
fit_keyword = re.compile("^(?:''')?(?:\[\[re:)?(?:''')?([A-Za-z][äÄöÖüÜßa-zè\(\)\?]{1,20})(?:''')?[,\| ]?")  #matches all keywords
fit_keyword_not_linked = re.compile("^(?:''')?([A-Za-z][äÄöÖüÜßa-zè\(\)\?]{1,20})(?:''')?")

def convert_one_link(hit, keyword):
    if re.search("'''.*'''", hit.group(0)):
        return "'''" + '[[re:' + keyword + '|' + hit.group(1) + ']]' + "'''"
    else:
        return '[[re:' + keyword + '|' + hit.group(1) + ']]'

def convert_numbers(hit, keyword):
    offset = len(hit.group(0)) - len(hit.group(1))

    return hit.group(0)[0:offset] + '[[re:' + keyword + ' ' + hit.group(1)[0:-1] +'|' + hit.group(1) + ']]'

def convert_line(line):
    if fit_keyword.search(line):
        keyword = fit_keyword.search(line).group(1)
        count =  fit_numbers.findall(line)
        if len(count) <= 1:
            line = fit_keyword_not_linked.sub(lambda x: convert_one_link(x, keyword), line)
        else:
            line = fit_numbers_not_linked.sub(lambda x: convert_numbers(x, keyword), line)

    return line

if __name__ == "__main__":
    with open('dump/Regist_convert.txt', mode='w', encoding='utf8') as writepointer:
        with open('dump/Register.txt', encoding='utf8') as filepointer:
            lines = filepointer.readlines()
            for line in lines:
                writepointer.write(convert_line(line))