# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
import json

def substitute_ht(re_ht):
    print(re_ht.group(1) + '$' + re_ht.group(2))
    return re_ht.group(1) + '$' + re_ht.group(2)

json_data=open("dump/ht.json", encoding="utf8").read()
site = pywikibot.Site()
data = json.loads(json_data)
lemmas = data['*'][0]['*']

for i, lemma in enumerate(lemmas):
    lemma['a']['title'] = lemma['a']['title'].replace('_', ' ')
    if lemma['a']['nstext'] == '(Article)':
        page = pywikibot.Page(site, lemma['a']['title'])
    else:
        page = pywikibot.Page(site, lemma['a']['nstext'] + ':' + lemma['a']['title'])
    fit = re.search('(\{\{HT\|uc1.)(b\d{6}(?:\|US)?(?:\|\|\d{1,4})?(?:\|US\|\d{1,4})?\}\})', page.text)
    print(i, "/", len(lemmas))
    print(fit)
    if fit:
        print(lemma['a']['title'])
        page.text = re.sub('(\{\{HT\|uc1.)(b\d{6}(?:\|US)?(?:\|\|\d{1,4})?(?:\|US\|\d{1,4})?\}\})', substitute_ht, page.text)
        page.save('automatische Konvertierung: {{HT|uc1.b######}} -> {{HT|uc1.$b######}}', botflag= True)
