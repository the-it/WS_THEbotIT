# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
from tools.template_handler import TemplateHandler
import re
import requests
import pywikibot

def substitute_sperrsatz(template):
    handler = TemplateHandler(template.group(0))
    handler.set_title('SperrSchrift')
    parameters = handler.get_parameterlist()
    parameters.append({'key': 'satz', 'value': '1'})
    handler.update_parameters(parameters)
    return handler.get_str(str_complex=False)


searcher_catscan = PetScan()
searcher_catscan.add_namespace(0)
searcher_catscan.add_namespace('Seite')
searcher_catscan.add_namespace('Index')
searcher_catscan.add_yes_template('Sperrsatz')
sites = searcher_catscan.run()
site = pywikibot.Site()

for lemma in sites:
    if lemma['a']['nstext'] == '(Article)':
        page = pywikibot.Page(site, lemma['a']['title'])
    else:
        page = pywikibot.Page(site, lemma['a']['nstext'] + ':' + lemma['a']['title'])
    test_for_fit = re.search('Sperrsatz', page.text)
    if test_for_fit:
        try:
            page.text = re.sub('\{\{Sperrsatz(?:\{\{.*?\}\}|.)*?\}\}', substitute_sperrsatz, page.text)
            page.save(summary='bot edit: Vereinheitlichung der Vorlage Sperrsatz zu SperrSchrift', botflag=True, )
        except:
            print(lemma)