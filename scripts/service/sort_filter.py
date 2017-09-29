# -*- coding: utf-8 -*-
import sys

sys.path.append('../../')
from tools.catscan import PetScan
import re
import pywikibot


class SortFilter:
    def filter(self, list_to_process):
        titles = []
        for page in list_to_process:
            # searching for all special cases
            match = re.search(
                "[ÁáĆćÉéÍíŃńÓóŚśÚúÝýŹźǾǿÀàÈèÌìÒòÙùÂâĈĉÊêĜĝĤĥÎîĴĵÔôŝŜÛûÄäËëÏïÖöÜüÿÃãÑñÕõÅåÇçŞşǍǎČčĎďĚěǦǧǏǐĽľŇňǑǒŘřŠšŤťǓǔŽžŁłŐőŰűØøĀāĒēĪīŌōŪūȲȳĂăĔĕĞğĬĭŎŏŬŭßÆæŒœÐðÞþ]",
                page['a']["title"])
            if match is not None:
                titles.append(page['a']["title"])
        print('all pages for sort lockup')
        titles = self.search_for_sort(titles)
        return titles

    @staticmethod
    def search_for_sort(title_of_pages):
        site = pywikibot.Site('de', 'wikisource')
        result = []
        i = 1
        j = 0
        for title in title_of_pages:
            print(title)
            print(str(i) + '/' + str(len(title_of_pages)))
            print('found ' + str(j))
            i += 1
            page = pywikibot.Page(site, title)
            text = page.text
            match = re.search('{{SORTIERUNG:.*}}', text)
            if match is None:
                result.append(title)
                j += 1
        return result

    def run(self):
        searcher = PetScan()
        searcher.add_positive_category("Werke")
        searcher.set_timeout(240)
        print('start catscan')
        # searcher.max_age(12)
        sites_for_filter = searcher.run
        print('ready for filtering')
        missing_sort = self.filter(sites_for_filter)
        print('done filtering')
        file = open('text_for_sort.txt', 'w', encoding="utf-8")
        for line in missing_sort:
            file.write('* ' + line + '\n')


if __name__ == "__main__":
    run = SortFilter()
    run.run()
