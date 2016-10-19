import re
import datetime

from pywikibot import Page
from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution
from tools.bots import BotExeption

class RowBasic():
    def __str__(self):
        return self.build_row()

    def __init__(self, wiki):
        self.wiki = wiki
        self.today = datetime.datetime.now()

    def build_row(self):
        raise BotExeption

class RowBearbeitungen(RowBasic):
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

class RowSeitenstatistik(RowBasic):
    def build_row(self):
        list_sites_stats = []
        list_sites_stats.append(self.get_all_sites())
        list_sites_stats.append(self.get_sites_in_cat(
                ['Fertig', 'Korrigiert', 'Unkorrigiert', 'Unvollständig', 'Teilkorrigiert', 'Sofort fertig'],
                namespace='Seite'))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Fertig', 'Korrigiert', 'Unkorrigiert', 'Unvollständig', 'Teilkorrigiert', 'Sofort fertig'],
                namespace='Article'))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Werke']))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Zeitschriftenartikel']))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Gedicht'], depth=4))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Märchen', 'Kunstmärchen', 'Sage', 'Fabel', 'Sagenballade', 'Reimfabel', 'Schwank'], depth=4))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Rechtstext'], depth=2))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Darstellung'], depth=0))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Brief'], depth=2))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Biographie', 'Autobiographie', 'Tagebuch'], depth=0))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Lexikon'], depth=0))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Drama'], depth=1))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Roman'], depth=1))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Reisebericht'], depth=0))
        list_sites_stats.append(self.get_sites_in_cat(
                [], any_template=['Themendaten', 'Ortsdaten']))
        list_sites_stats.append(self.get_sites_in_cat(
                ['Autoren'], namespace='Article', any_template=['Personendaten']))
        return '|-\n| {} || '.format(self.today.strftime('%Y-%m-%d')) + ' || '.join(list_sites_stats)

    def get_all_sites(self):
        dummypage = Page(self.wiki, 'Benutzer:THEbotIT/dummy')
        dummypage.text = '{{subst:NUMBEROFARTICLES}}'
        dummypage.save('get_new_number')
        del dummypage
        dummypage = Page(self.wiki, 'Benutzer:THEbotIT/dummy')
        return '{}'.format(dummypage.text)

    def get_sites_in_cat(self, list_of_cat, namespace=None, depth=None, any_template=[]):
        searcher = PetScan()
        for cat in list_of_cat:
            searcher.add_positive_category(cat)
        for cat in any_template:
            searcher.add_any_template(cat)
        searcher.set_logic_union()
        if namespace:
            searcher.add_namespace(namespace)
        if depth:
            searcher.set_search_depth(depth)
        list_of_lemmas = searcher.run()
        return '{0:,}'.format(len(list_of_lemmas)).replace(',', '.')

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
        #self.new_row(str(RowBearbeitungen(self.wiki)), 'BEARBEITUNGEN')
        self.new_row(str(RowSeitenstatistik(self.wiki)), 'SEITENSTATISTIK')
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

