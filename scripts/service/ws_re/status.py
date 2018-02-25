import re
from datetime import datetime

from pywikibot import Page, Site
from tools.catscan import PetScan
from tools.bots import CanonicalBot


class ReStatus(CanonicalBot):
    bot_name = 'REStatus'

    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)

    def task(self):
        fertig = self.get_sum_of_cat(['RE:Fertig'],
                                     ['RE:Teilkorrigiert', 'RE:Korrigiert', 'RE:Unkorrigiert', 'RE:Unvollständig'])
        korrigiert = self.get_sum_of_cat(['RE:Teilkorrigiert', 'RE:Korrigiert'],
                                         ['RE:Unkorrigiert', 'RE:Unvollständig'])
        unkorrigiert = self.get_sum_of_cat(['RE:Unkorrigiert', 'RE:Unvollständig'], [])
        self.user_page_the_it(korrigiert)
        self.history(fertig, korrigiert, unkorrigiert)
        return True

    @staticmethod
    def make_color(min_value, max_value, value):
        if value > min_value:
            if value < max_value:
                color = (1 - (value - min_value) / (max_value - min_value)) * 255
            else:
                color = 0
        else:
            color = 255
        return str(hex(int(color)))[2:].zfill(2)

    def user_page_the_it(self, korrigiert):
        status_string = []

        color = self.make_color(20e6, 22e6, korrigiert[0])
        status_string.append('<span style="background:#FF{}{}">{}</span>'.format(color, color, korrigiert[0]))
        color = self.make_color(5.0e3, 5.25e3, korrigiert[1])
        status_string.append('<span style="background:#FF{}{}">{}</span>'.format(color, color, korrigiert[1]))

        list_of_lemmas = self.petscan(['RE:Teilkorrigiert', 'RE:Korrigiert'], ['RE:Unkorrigiert', 'RE:Unvollständig'])
        date_page = Page(self.wiki, list_of_lemmas[0]['title'])
        date_of_first = str(date_page.oldest_revision.timestamp)[0:10]
        gap = datetime.now() - datetime.strptime(date_of_first, '%Y-%m-%d')
        color = self.make_color(3 * 365, 3.5 * 365, gap.days)
        status_string.append('<span style="background:#FF{}{}">{}</span>'.format(color, color, date_of_first))

        user_page = Page(self.wiki, 'Benutzer:THE IT/Werkstatt')
        temp_text = user_page.text
        temp_text = re.sub("<!--RE-->.*<!--RE-->", '<!--RE-->{}<!--RE-->'.format(' ■ '.join(status_string)), temp_text)
        user_page.text = temp_text
        user_page.save('todo RE aktualisiert')

    def history(self, fertig, korrigiert, unkorrigiert):
        page = Page(self.wiki, 'Benutzer:THEbotIT/' + self.bot_name)
        temp_text = page.text
        composed_text = ''.join(['|-\n', '|', self.timestamp.start.strftime('%Y%m%d-%H%M'),
                                 '||', str(unkorrigiert[1]), '||', str(unkorrigiert[0]), '||',
                                 str(int(unkorrigiert[0] / unkorrigiert[1])),
                                 '||', str(korrigiert[1]), '||', str(korrigiert[0]), '||',
                                 str(int(korrigiert[0] / korrigiert[1])),
                                 '||', str(fertig[1]), '||', str(fertig[0]), '||', str(int(fertig[0] / fertig[1])),
                                 '\n<!--new line-->'])
        temp_text = re.sub('<!--new line-->', composed_text, temp_text)
        page.text = temp_text
        page.save('new dataset', botflag=True)

    def get_sum_of_cat(self, cats, negacats):
        list_of_lemmas = self.petscan(cats, negacats)
        byte_sum = 0
        for lemma in list_of_lemmas:
            byte_sum += int(lemma['len'])
        return byte_sum, len(list_of_lemmas)

    def petscan(self, categories, negative_categories):
        searcher = PetScan()
        for category in categories:
            searcher.add_positive_category(category)
        for neg_category in negative_categories:
            searcher.add_negative_category(neg_category)
        searcher.set_logic_union()
        self.logger.debug(searcher)
        return searcher.run()


if __name__ == "__main__":
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReStatus(wiki=WIKI, debug=True) as bot:
        bot.run()
