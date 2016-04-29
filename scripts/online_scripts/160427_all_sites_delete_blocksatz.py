# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan.catscan import CatScan
import re
import requests
import pywikibot

searcher_index = CatScan()
searcher_index.add_namespace('Seite')
searcher_index.set_logic_union()
searcher_index.set_timeout(240)
searcher_index.add_yes_template("BlockSatzStart")
print(searcher_index)
list_of_pages = searcher_index.run()
wiki = pywikibot.Site()

for idx, page in enumerate(list_of_pages):
    #{"page_id":400467,"page_latest":"20160418082344","page_len":2017,"page_namespace":102,"page_title":"Sterbeurkunde_Pedro_Montt_Montt_(1849–1910).jpg"}
    print('{}/{} {}'.format(idx + 1, len(list_of_pages), page['page_title']))
    page = pywikibot.Page(wiki, "Seite:"+page["page_title"])
    temp_text = page.text
    regex_head = re.compile("\A<noinclude>.*?<\/noinclude>[^\Z]", re.DOTALL)
    regex_foot = re.compile("[^\A]<noinclude>.*?<\/noinclude>\Z", re.DOTALL)
    if regex_head.search(temp_text) and regex_foot.search(temp_text):
        head = regex_head.search(temp_text).group(0)
        foot = regex_foot.search(temp_text).group(0)
        head_str = re.sub("\{\{BlockSatzStart\}\}", "", head)
        foot_str = re.sub("\{\{BlockSatzEnd\}\}", "", foot)
        temp_text = regex_head.sub(head_str, temp_text)
        temp_text = regex_foot.sub(foot_str, temp_text)
        page.text = temp_text
        page.save(summary='bot edit: BlockSatz vom Namensraum Seite entfernen.', botflag=True)
