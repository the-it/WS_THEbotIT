# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
from pywikibot import Page, Site
from pywikibot.pagegenerators import LinksearchPageGenerator, SearchPageGenerator

wiki = Site()

searcher = SearchPageGenerator('insource:http://www.ub.uni-bielefeld.de/diglib', site=wiki)

print(type(searcher))

for idx, page in enumerate(searcher):
    print(idx, page)
    temp_text = page.text
    if re.search('\[http:\/\/www.ub.uni\-bielefeld.de', temp_text):
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/aufkl\/journalfranken\/journalfranken.htm UB Bielefeld\]', '{{Bielefeld|2096404}}', temp_text)
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/2006\/fontane_gedichte\/ UB Bielefeld\]', '{{Bielefeld|1682441}}', temp_text)
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/2005\/muehsam_erde\/ Digitale Drucke der Uni Bielefeld\]',
                           '{{Bielefeld|1660345}}', temp_text)
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/aufkl/browse\/neuethalia\/11792.html Uni Bielefeld\]',
                           '{{Bielefeld|2300223_001}}', temp_text)
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/aufkl\/browse\/neuethalia\/21792.html Uni Bielefeld\]',
                           '{{Bielefeld|2300223_002}}', temp_text)
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/aufkl\/browse\/neuethalia\/11793.html Uni Bielefeld\]',
                           '{{Bielefeld|2300223_003}}', temp_text)
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/aufkl\/browse\/neuethalia\/21793.html Uni Bielefeld\]',
                           '{{Bielefeld|2300223_004}}', temp_text)
        temp_text, bla = re.subn('\[http:\/\/www.ub.uni\-bielefeld.de\/diglib\/aufkl\/thalia\/thalia.htm UB Bielefeld\]',
                           '{{Bielefeld|1944380}}', temp_text)
    if page.text != temp_text:
        page.text = temp_text
        try:
            page.save(botflag=True, summary='http://www.ub.uni-bielefeld.de/ -> Bielefeld')
        except Exception as exception:
            print(exception)
            continue


