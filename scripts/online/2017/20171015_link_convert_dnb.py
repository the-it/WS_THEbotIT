# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
from pywikibot import Page, Site
from pywikibot.pagegenerators import LinksearchPageGenerator, SearchPageGenerator

wiki = Site()

searcher = SearchPageGenerator('insource:http://nbn-resolving.de/urn:nbn:de:101', site=wiki, namespaces=[0])
regex = re.compile('\[http:\/\/nbn-resolving.de\/urn:nbn:de:101:(\d)-(\d{10,13}) DNB]')


def convert_link(hit):
    return '{{{{DNB|{}-{}}}}}'.format(hit.group(1), hit.group(2))


for idx, page in enumerate(searcher):
    print(idx, page)
    temp_text = page.text
    if regex.search(temp_text):
        temp_text = regex.subn(lambda x: convert_link(x), temp_text)
        print('url_found')
    if page.text != temp_text:
        page.text = temp_text[0]
        try:
            page.save(botflag=True, summary='http://nbn-resolving.de/urn:nbn:de:101: -> {{DNB|}}')
        except Exception as exception:
            print(exception)
            continue
