# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
import re
import pywikibot
import roman

def build_arg(searcher):
    arg1 = ''                   #building the 'band' information
    if searcher.group(2):
        arg1 += 'S '
    arg1 += searcher.group(3)
    if searcher.group(4):
        arg1 += ' A'
    if searcher.group(5):
        arg1 += (',' + searcher.group(5))
    arg2 = searcher.group(6)    #add the page
    arg3 = searcher.group(7)    #add the file typ
    return (arg1, arg2, arg3)

def decide_REIA_or_REWL(re_sub):
    test1 = re_sub.group(0)
    searcher = FIT.search(re_sub.group(0))
    (arg1, arg2, arg3) = build_arg(searcher)
    if searcher.group(1) == 'archive':  # archive
        return '{{REIA|%s|%s}}' % (arg1, arg2)
    else: # wikilivre
        arabic = roman.fromRoman(searcher.group(3))
        subl = searcher.group(2)
        app = searcher.group(4)
        halfband = searcher.group(5)
        if  (app is None) and (subl is None) and (arabic < 12): # all between I and XI
            return '{{REIA|%s|%s}}' % (arg1, arg2)
        # I A,1 and II A,1
        elif (subl is None) and (app == 'A') and (arabic < 3) and (halfband == '1'):
            return '{{REIA|%s|%s}}' % (arg1, arg2)
        # S I, S II, S III
        elif (subl == 'S') and (app is None) and (arabic < 4) and (halfband is None):
            return '{{REIA|%s|%s}}' % (arg1, arg2)
        else: # rest
            return '{{REWL|%s|%s}}' % (arg1, arg2)

WIKI = pywikibot.Site()

REGEX = r'''http:\/\/           # searching for a http://-address
            .*?                 # some characters in between   UNGREEDY (hier kam es beim Durchlauf zu einem Error
                                # beim nächsten mal die Anzahl der Zeichen begrenzen)
            (wikilivres|archive)# hit(1) for deciding whether a wikilivre or an archive address
            .*?                 # some characters in between   UNGREEDY
            \/Pauly-Wissowa     #
            [ _]?(S)?[ _]?      # hit(2) for a possible subblement letter
            ([IVX]{1,5}),?      # hit(3) for roman letters between one and 5 times
            [ _]?(A)?           # hit(4) for a possible append letter
            ([12])?,?           # hit(5) for a possible 1 or 2
            [ _]0{0,3}(\d{1,4}) # hit(6) for the page
            \.(jpg|png)         # hit(7) for the picture typ'''

FIT = re.compile(REGEX, re.VERBOSE)

LEMMA_SEARCHER = PetScan()
LEMMA_SEARCHER.add_positive_category('Paulys Realencyclopädie der classischen Altertumswissenschaft')
#lemma_searcher.add_no_template('REIA') # sadly I have to look on all 18.000 re-sites
LEMMA_SEARCHER.set_timeout(90)
lemmas = LEMMA_SEARCHER.run()

for i, _ in enumerate(lemmas):
    lemmas[i] = lemmas[i]['a']['title']

for idx, lemma in enumerate(lemmas):
    if lemma[0:3] == 're:':
        print(idx, '/', len(lemmas), lemma)
        page = pywikibot.Page(WIKI, lemma)
        searcher = FIT.search(page.text)
        if searcher:
            print('#######', lemma)
            temp = FIT.sub(lambda x: decide_REIA_or_REWL(x), page.text)
            page.text = temp
            test1 = 3
            page.save(summary='Umwandlung von Scanlinks zu {{REIA}} und {{REWL}}',
                      botflag=True, asynchronous=True)
