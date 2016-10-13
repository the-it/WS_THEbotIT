import re
import datetime

from pywikibot import Page
from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution


class RowBearbeitungen():
    def __str__(self):
        return self.build_row()

    def __init__(self, wiki):
        self.wiki = wiki
        self.today = datetime.datetime.now()

    def build_row(self):
        return '|-\n| {} || {} ||  ||  ||  ||'.format(self.today.strftime('%Y-%m-%d'),
                                                                      self.get_wiki_bearbeitungen())

    def get_wiki_bearbeitungen(self):
        dummypage = Page(self.wiki, 'Benutzer:THEbotIT/dummy')
        dummypage.text = '{{subst:NUMBEROFEDITS}}'
        dummypage.save('get_new_number')
        del dummypage
        dummypage = Page(self.wiki, 'Benutzer:THEbotIT/dummy')
        return dummypage.text

class WsStatus(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'WsStatus'
        self.text = None
        self.stat_page = None

    def run(self):
        if self.debug:
            lemma = 'Benutzer:THEbotIT/' + self.botname
        else:
            lemma = 'WS:Statistik'
        self.load_text_from_site(lemma)
        self.new_row(str(RowBearbeitungen(self.wiki)), 'BEARBEITUNGEN')
        self.save_text_to_site()

    def new_row(self, row, placeholder):
        self.text = re.sub('<!--BOT:{}-->'.format(placeholder), '<!--BOT:{}-->\n{}'.format(placeholder, row), self.text)

    def load_text_from_site(self, lemma):
        self.logger.info('Load text from {}'.format(lemma))
        self.stat_page = Page(self.wiki, lemma)
        self.text = self.stat_page.text

    def save_text_to_site(self):
        self.stat_page.text = self.text
        self.stat_page.save('new dataset', botflag=True)

