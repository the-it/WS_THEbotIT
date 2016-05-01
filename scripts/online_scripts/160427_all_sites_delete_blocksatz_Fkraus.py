# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
import re
import requests
import pywikibot
import time
import json

response = requests.get(url="https://petscan.wmflabs.org/?language=de&project=wikisource&combination=union&ns%5B102%5D=1&templates_yes=BlockSatzStart&output_compatability=quick-intersection&sortorder=descending&format=json&doit=1",
                        headers={'User-Agent': 'Python-urllib/3.1'}, timeout=60)
response_byte = response.content
list_of_pages = json.loads(response_byte.decode("utf8"))['pages']
wiki = pywikibot.Site()

for idx, page in enumerate(list_of_pages):
    print('{}/{} {}'.format(idx + 1, len(list_of_pages), page['page_title']))
    page = pywikibot.Page(wiki, "Seite:"+page["page_title"])
    temp_text = page.text
    regex_head = re.compile("\A<noinclude>.*?<\/noinclude>[^\Z]", re.DOTALL)
    regex_foot = re.compile("[^\A]<noinclude>.*?<\/noinclude>\Z", re.DOTALL)
    regex_block_start = re.compile("\{\{BlockSatzStart\}\}")
    regex_block_end = re.compile("\{\{BlockSatzEnd\}\}")
    if regex_head.search(temp_text) and regex_foot.search(temp_text):
        head = regex_head.search(temp_text).group(0)
        foot = regex_foot.search(temp_text).group(0)
        if regex_block_start.search(head) and regex_block_end.search(foot):
            head_str = regex_block_start.sub("", head)
            foot_str = regex_block_end.sub("", foot)
            temp_text = regex_head.sub(head_str, temp_text)
            temp_text = regex_foot.sub(foot_str, temp_text)
            page.text = temp_text
            try:
                page.save(summary='bot edit: BlockSatz vom Namensraum Seite entfernen.', botflag=True)
            except:
                time.sleep(10)
