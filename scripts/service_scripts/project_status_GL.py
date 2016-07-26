__author__ = 'erik'

import sys
import os
from pywikibot.data.api import LoginManager
import pywikibot
import re

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password

class GLStatus(CanonicalBot):
    def __init__(self, wiki):
        CanonicalBot.__init__(self, wiki)
        self.botname = 'GLStatus'

    def run(self):
        if __debug__:
            lemma = 'Benutzer:THEbotIT/' + self.botname
        else:
            lemma = 'Die Gartenlaube'
        page = pywikibot.Page(self.wiki, lemma)
        temp_text = page.text

        all = self.petscan([])
        fertig = self.petscan(['Fertig'])
        korrigiert = self.petscan(['Korrigiert'])
        unkorrigiert = self.petscan(['Unkorrigiert'])
        articles = self.petscan([], article=True)

        temp_text = self.projektstand(temp_text, all, fertig, korrigiert, unkorrigiert, articles)
        temp_text = self.alle_seiten(temp_text, all)
        temp_text = self.korrigierte_seiten(temp_text, korrigiert)
        temp_text = self.fertige_seiten(temp_text, fertig)
        for year in range(1853, 1900):
            temp_text = self.year(year, temp_text)

        page.text = temp_text
        page.save('new dataset', botflag=True)

    def to_percent(self, counter, denominator):
        return ' ({0:.2f} %)'.format(round((counter/denominator)*100, 2)).replace('.', ',')

    def projektstand(self, temp_text, all, fertig, korrigiert, unkorrigiert, articles):
        composed_text = ''.join(['<!--new line: Liste wird von einem Bot aktuell gehalten.-->\n|-\n', '|', self.timestamp_start.strftime('%d.%m.%Y'),
                         '|| ', str(all),
                         ' || ', str(korrigiert), self.to_percent(korrigiert, all),
                         ' || ', str(fertig), self.to_percent(fertig, all),
                         ' || ', str(unkorrigiert), self.to_percent(unkorrigiert, all),
                         ' || ', str(articles), self.to_percent(articles, 17500), ' ||'])
        return re.sub('<!--new line: Liste wird von einem Bot aktuell gehalten.-->', composed_text, temp_text)

    def alle_seiten(self, temp_text, all):
        all = self.petscan([''])
        composed_text = ''.join(['<!--GLStatus:alle_Seiten-->', str(all), '<!---->'])
        temp_text = re.sub('<!--GLStatus:alle_Seiten-->\d{5}<!---->', composed_text, temp_text)
        return temp_text

    def korrigierte_seiten(self, temp_text, korrigiert):
        composed_text = ''.join(['<!--GLStatus:korrigierte_Seiten-->', str(korrigiert), '<!---->'])
        temp_text = re.sub('<!--GLStatus:korrigierte_Seiten-->\d{5}<!---->', composed_text, temp_text)
        return temp_text

    def fertige_seiten(self, temp_text, fertig):
        composed_text = ''.join(['<!--GLStatus:fertige_Seiten-->', str(fertig), '<!---->'])
        temp_text = re.sub('<!--GLStatus:fertige_Seiten-->\d{4,5}<!---->', composed_text, temp_text)
        return temp_text

    def year(self, year, temp_text):
        fertig = self.petscan(['Fertig'], year=year)
        korrigiert = self.petscan(['Korrigiert'], year=year)
        rest = self.petscan([], not_categories=['Fertig', 'Korrigiert'], year=year)
        alle = fertig + korrigiert + rest
        regex = re.compile('<!--GLStatus:' + str(year) + '-->.*?<!---->')
        if rest > 0:
            temp_text = regex.sub('<!--GLStatus:{year}-->|span style="background-color:#4876FF; font-weight: bold"|ca. {percent} % korrigiert oder fertig<!---->'
                                  .format(year=year,
                                          percent=str(round(((fertig + korrigiert) / alle) * 100, 1)).replace('.', ',')), temp_text)
        elif korrigiert > 0:
            temp_text = regex.sub('<!--GLStatus:{year}-->|span style="background-color:#F7D700; font-weight: bold"|{percent_fertig} % fertig, Rest korrigiert<!---->'
                                  .format(year=year,
                                          percent_fertig = str(round(((fertig) / alle) * 100, 1)).replace('.', ',')), temp_text)
        else:
            temp_text = regex.sub('<!--GLStatus:{year}-->|span style="background-color:#00FF00; font-weight: bold"|Fertig<!---->'
                                  .format(year = year), temp_text)
        return temp_text

    def petscan(self, categories, not_categories = [], article=False, year=None):
        searcher = PetScan()
        if article:
            searcher.add_namespace('Article')
        else:
            searcher.add_namespace('Seite')
        searcher.set_search_depth(5)
        if year:
            searcher.add_positive_category('Die Gartenlaube (' + str(year) +')' )
        else:
            searcher.add_positive_category('Die Gartenlaube')
        for category in categories:
            searcher.add_positive_category(category)
        for category in not_categories:
            searcher.add_negative_category(category)
        self.logger.debug(str(searcher))
        return len(searcher.run())

if __name__ == "__main__":
    with open('../password.pwd') as password_file:
        password = load_password(password_file)
        wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()
    bot = GLStatus(wiki)
    with SaveExecution(bot):
        bot.run()
