import re
import datetime

from pywikibot import Page
from tools.catscan import PetScan
from tools.bots import CanonicalBot
from tools.bots import BotExeption


class RowBasic():
    def __str__(self):
        return self.build_row()

    def __init__(self, wiki, logger):
        self.wiki = wiki
        self.logger = logger
        self.today = datetime.datetime.now()

    def build_row(self):
        raise BotExeption("Class {} should implement the method build_row()".format(self))

    def get_sites_in_cat(self, list_of_cat, namespace=None, depth=None, any_template: list = None, union=False):
        # pylint: disable=too-many-arguments
        searcher = PetScan()
        for cat in list_of_cat:
            searcher.add_positive_category(cat)
        if any_template:
            for cat in any_template:
                searcher.add_any_template(cat)
        if union:
            searcher.set_logic_union()
        if namespace:
            searcher.add_namespace(namespace)
        if depth:
            searcher.set_search_depth(depth)
        self.logger.info(searcher)
        list_of_lemmas = searcher.run()
        del searcher
        return '{0:,}'.format(len(list_of_lemmas)).replace(',', '.')

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
        self.logger.info('Searchstrings for genre')
        list_sites_stats = list()
        list_sites_stats.append(self.get_all_sites())
        list_sites_stats.append(self.get_sites_in_cat(['Fertig', 'Korrigiert', 'Unkorrigiert',
                                                       'Unvollständig', 'Teilkorrigiert', 'Sofort fertig'],
                                                      namespace='Seite', union=True))
        list_sites_stats.append(self.get_sites_in_cat(['Fertig', 'Korrigiert', 'Unkorrigiert',
                                                       'Unvollständig', 'Teilkorrigiert', 'Sofort fertig'],
                                                      namespace='Article', union=True))
        list_sites_stats.append(self.get_sites_in_cat(['Werke']))
        list_sites_stats.append(self.get_sites_in_cat(['Zeitschriftenartikel']))
        list_sites_stats.append(self.get_sites_in_cat(['Gedicht'], depth=4))
        list_sites_stats.append(self.get_sites_in_cat(['Märchen', 'Sage', 'Fabel',
                                                       'Sagenballade', 'Reimfabel', 'Schwank'],
                                                      depth=4, union=True))
        list_sites_stats.append(self.get_sites_in_cat(['Rechtstext'], depth=2))
        list_sites_stats.append(self.get_sites_in_cat(['Darstellung'], depth=0))
        list_sites_stats.append(self.get_sites_in_cat(['Brief'], depth=2))
        list_sites_stats.append(self.get_sites_in_cat(['Biographie', 'Autobiographie', 'Tagebuch'],
                                                      depth=0, union=True))
        list_sites_stats.append(self.get_sites_in_cat(['Lexikon'], depth=0))
        list_sites_stats.append(self.get_sites_in_cat(['Drama'], depth=1))
        list_sites_stats.append(self.get_sites_in_cat(['Roman'], depth=1))
        list_sites_stats.append(self.get_sites_in_cat(['Reisebericht'], depth=0))
        list_sites_stats.append(self.get_sites_in_cat([], any_template=['Themendaten', 'Ortsdaten']))
        list_sites_stats.append(self.get_sites_in_cat(['Autoren'], namespace='Article', any_template=['Personendaten']))
        return '|-\n| {} || '.format(self.today.strftime('%Y-%m-%d')) + ' || '.join(list_sites_stats)

    def get_all_sites(self):
        dummypage = Page(self.wiki, 'Benutzer:THEbotIT/dummy')
        dummypage.text = '{{subst:NUMBEROFARTICLES}}'
        dummypage.save('get_new_number')
        del dummypage
        dummypage = Page(self.wiki, 'Benutzer:THEbotIT/dummy')
        return '{}'.format(dummypage.text)


class RowBearbeitungsstand(RowBasic):
    def build_row(self):
        self.logger.info('Searchstrings for Bearbeitungsstand')
        list_sites_stats = []
        # Werke
        counter_werke = self.get_sites_in_cat(['Werke'])
        list_sites_stats.append(counter_werke)
        for cat in [['Fertig'], ['Korrigiert'], ['Teilkorrigiert'], ['Unkorrigiert'], ['Unvollständig']]:
            counter_werke_sub = self.get_sites_in_cat(['Werke'] + cat)
            list_sites_stats.append(counter_werke_sub)
            list_sites_stats.append(self.make_percent(counter_werke_sub, counter_werke))
        counter_werke_sub = int(self.get_sites_in_cat(['Werke', 'Korrekturprobleme']).replace('.', ''))
        counter_werke_sub += int(self.get_sites_in_cat(['Werke', 'Scanfehler']).replace('.', ''))
        counter_werke_sub += int(self.get_sites_in_cat(['Werke', 'Ohne Quelle']).replace('.', ''))
        list_sites_stats.append('{0:,}'.format(counter_werke_sub).replace(',', '.'))
        list_sites_stats.append(self.make_percent(str(counter_werke_sub), counter_werke))
        # Seite
        all_sites = self.get_sites_in_cat(['Fertig', 'Korrigiert', 'Unkorrigiert',
                                           'Unvollständig', 'Teilkorrigiert', 'Sofort fertig'],
                                          namespace='Seite', union=True)
        list_sites_stats.append(all_sites)
        for cat in [['Fertig'], ['Korrigiert'], ['Unkorrigiert']]:
            counter_site_sub = self.get_sites_in_cat(cat, namespace='Seite')
            list_sites_stats.append(counter_site_sub)
            list_sites_stats.append(self.make_percent(str(counter_site_sub), all_sites))

        return '|-\n| {} || '.format(self.today.strftime('%Y-%m-%d')) + ' || '.join(list_sites_stats)

    @staticmethod
    def make_percent(counter: str, denominator: str):
        counter = float(counter.replace('.', ''))
        denominator = float(denominator.replace('.', ''))
        return "{:10.2f}".format(counter/denominator * 100.0)


class WsStatus(CanonicalBot):
    bot_name = 'WsStatus'

    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.text = None
        self.stat_page = None

    def task(self):
        if self.debug:
            lemma = 'Benutzer:THEbotIT/' + self.bot_name
        else:
            lemma = 'WS:Statistik'
        self.load_text_from_site(lemma)
        #self.new_row(str(RowSeitenstatistik(self.wiki, self.logger)), 'SEITENSTATISTIK')
        self.new_row(str(RowBearbeitungsstand(self.wiki, self.logger)), 'BEARBEITUNGSSTAND')
        self.save_text_to_site()
        return True

    def new_row(self, row, placeholder):
        self.text = re.sub('<!--BOT:{}-->'.format(placeholder), '<!--BOT:{}-->\n{}'.format(placeholder, row), self.text)

    def load_text_from_site(self, lemma):
        self.logger.info('Load text from {}'.format(lemma))
        self.stat_page = Page(self.wiki, lemma)
        self.text = self.stat_page.text

    def save_text_to_site(self):
        self.stat_page.text = self.text
        self.stat_page.save('new dataset', botflag=True)
