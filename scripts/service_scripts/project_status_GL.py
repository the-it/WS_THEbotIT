__author__ = 'erik'

import sys
import os
import pywikibot
from pywikibot.data.api import LoginManager
import re

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan import CatScan
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password

class GLStatus(CanonicalBot):
    def __init__(self, wiki):
        CanonicalBot.__init__(self, wiki)
        self.botname = 'GLStatus'

    def run(self):
        all = self.petscan([''], pages=True)
        fertig = self.petscan(['Fertig'], pages=True)
        korrigiert = self.petscan(['Korrigiert'], pages=True)
        unkorrigiert = self.petscan(['Unkorrigiert'], pages=True)
        articles = self.petscan([])
        if __debug__:
            lemma = 'Benutzer:THEbotIT/' + self.botname
        else:
            lemma = 'Die Gartenlaube'
        page = pywikibot.Page(self.wiki, lemma)
        temp_text = page.text
        composed_text = ''.join(['<!--new line: Liste wird von einem Bot aktuell gehalten.-->\n|-\n', '|', self.timestamp_start.strftime('%d.%m.%Y'),
                         '|| ', str(all),
                         ' || ', str(korrigiert), ' (', str(round((korrigiert/all)*100, 2)).replace('.', ','), ' %)',
                         ' || ', str(fertig), ' (', str(round((fertig/all)*100, 2)).replace('.', ','), ' %)',
                         ' || ', str(unkorrigiert), ' (', str(round((unkorrigiert/all)*100, 2)).replace('.', ','), ' %)',
                         ' || ', str(articles), ' (', str(round((articles/17500)*100, 2)).replace('.', ','), ' %)', ' ||'])
        temp_text = re.sub('<!--new line: Liste wird von einem Bot aktuell gehalten.-->', composed_text, temp_text)
        page.text = temp_text
        page.save('new dataset', botflag=True)

    def send_log_to_wiki(self):
        pass

    def petscan(self, categories, pages=False):
        self.searcher = CatScan()
        if pages:
            self.searcher.add_namespace('Seite')
        else:
            self.searcher.add_namespace('Article')
        self.searcher.set_search_depth(5)
        self.searcher.add_positive_category('Die Gartenlaube')
        for category in categories:
            self.searcher.add_positive_category(category)
        return len(self.searcher.run())

if __name__ == "__main__":
    with open('../password.pwd') as password_file:
        password = load_password(password_file)
        wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()
    bot = GLStatus(wiki)
    with SaveExecution(bot):
        bot.run()
