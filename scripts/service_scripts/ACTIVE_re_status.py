import re
from datetime import datetime, timedelta

from pywikibot import Page
from tools.catscan import PetScan
from tools.bots import CanonicalBot

class ReStatus(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'REStatus'

    def run(self):
        fertig = self.get_sum_of_cat(['Fertig RE'])
        korrigiert = self.get_sum_of_cat(['Teilkorrigiert RE', 'Korrigiert RE'])
        unkorrigiert = self.get_sum_of_cat(['Unkorrigiert RE'])
        self.userpage_THE_IT(korrigiert)
        self.history(fertig, korrigiert, unkorrigiert)

    def userpage_THE_IT(self, korrigiert):
        status_string = []

        if korrigiert[0] > 15e6:
            status_string.append('<span style="background:red">{:,}</span>'.format(korrigiert[0]))
        else:
            status_string.append('{:,}'.format(korrigiert[0]))
        if korrigiert[1] > 4e3:
            status_string.append('<span style="background:red">{:,}</span>'.format(korrigiert[1]))
        else:
            status_string.append('{:,}'.format(korrigiert[1]))

        list_of_lemmas = self.petscan(['Teilkorrigiert RE', 'Korrigiert RE'])
        date_page = Page(self.wiki, list_of_lemmas[0]['title'])
        date_of_first = str(date_page.oldest_revision.timestamp)[0:10]
        gap = datetime.now() - datetime.strptime(date_of_first, '%Y-%m-%d')
        if gap > timedelta(days = 2*365):
            status_string.append('<span style="background:red">{}</span>'.format(date_of_first))
        else:
            status_string.append('{}'.format(date_of_first))

        user_page = Page(self.wiki, 'Benutzer:THE IT/Werkstatt')
        temp_text = user_page.text
        temp_text = re.sub("<!--RE-->.*<!--RE-->", '<!--RE-->{}<!--RE-->'.format(' ■ '.join(status_string)), temp_text)
        user_page.text = temp_text
        user_page.save('todo RE aktualisiert')

    def history(self, fertig, korrigiert, unkorrigiert):
        page = Page(self.wiki, 'Benutzer:THEbotIT/' + self.botname)
        temp_text = page.text
        composed_text = ''.join(['|-\n', '|', self.timestamp_start.strftime('%Y%m%d-%H%M'),
                                 '||', str(unkorrigiert[1]), '||', str(unkorrigiert[0]), '||',
                                 str(int(unkorrigiert[0] / unkorrigiert[1])),
                                 '||', str(korrigiert[1]), '||', str(korrigiert[0]), '||',
                                 str(int(korrigiert[0] / korrigiert[1])),
                                 '||', str(fertig[1]), '||', str(fertig[0]), '||', str(int(fertig[0] / fertig[1])),
                                 '\n<!--new line-->'])
        temp_text = re.sub('<!--new line-->', composed_text, temp_text)
        page.text = temp_text
        page.save('new dataset', botflag=True)

    def get_sum_of_cat(self, cats):
        list_of_lemmas = self.petscan(cats)
        byte_sum = 0
        for lemma in list_of_lemmas:
            byte_sum += int(lemma['len'])
        return byte_sum, len(list_of_lemmas)

    def petscan(self, categories):
        self.searcher = PetScan()
        for category in categories:
            self.searcher.add_positive_category(category)
        self.searcher.set_logic_union()
        self.logger.debug(self.searcher)
        return self.searcher.run()