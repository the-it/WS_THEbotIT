__author__ = 'erik'

from tools.catscan import CatScan
import os
import pywikibot
import re
from tools.date_conversion import DateConversion

class AuthorList:
    def __init__(self, age):
        self.last_run = age

    def run(self):
        searcher = CatScan()
        # is there pre rawdata?
        if os.path.isfile('raw_data.json') is True:
            #import database
            searcher.max_age(self.last_run + 1) #all changes from age + 1 hour
        else:  #creating database
            searcher.set_timeout(120)
            pass
        searcher.add_namespace(0) # search in main namespace
        searcher.add_positive_category('Autoren')
        searcher.add_yes_template('Personendaten')
        result = searcher.run()
        pass
        site = pywikibot.Site()
        going_on = False
        for i in result:
            if i['a']['title'] == 'Friedrich_Koldewey':
                going_on = True
            print(i['a']['title'])
            if going_on:
                page = pywikibot.Page(site, i['a']['title'])
                findings = re.search('\|[ ]?GEBURTSDATUM=.*\n', page.text)
                converter = DateConversion(findings.group()[14:-1])
                findings2 = re.search('\|[ ]?STERBEDATUM=.*\n', page.text)
                converter2 = DateConversion(findings2.group()[13:-1])
                try:
                    str(converter)
                    str(converter2)
                except Exception as e:
                    with open('output.txt', 'a') as fobj:
                        fobj.write(i['a']['title'] + '\n')
                        fobj.write(str(e) + '\n')

if __name__ == "__main__":
    run = AuthorList(1000000)
    run.run()