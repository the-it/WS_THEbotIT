import re
from abc import abstractmethod
from datetime import datetime, timedelta
from logging import Logger
from operator import itemgetter

from pywikibot import Page, Site

from scripts.service.ws_re.data_types import RePage
from tools.bots import CanonicalBot
from tools.catscan import PetScan
from tools.template_handler import TemplateHandler


class ReScannerTask(object):
    def __init__(self, wiki: Site, debug: bool, logger: Logger):
        self.reporter_page = None
        self.wiki = wiki
        self.debug = debug
        self.logger = logger

    def __del__(self):
        self.finish_task()

    def preprocess_lemma(self, re_page: RePage):
        self.text = page.text
        self.pretext = page.text

    def postprocess_lemma(self, re_page: RePage):
        page.text = self.text
        return self.text != self.pretext

    @abstractmethod
    def task(self):
        pass

    def process_lemma(self, re_page: RePage):
        self.preprocess_lemma(re_page)
        self.task()
        return self.postprocess_lemma(re_page)

    def load_task(self):
        self.logger.info('opening task {}'.format(self.get_name()))

    def finish_task(self):
        self.logger.info('closing task {}'.format(self.get_name()))

    def get_name(self):
        return re.search("(.{4})Task", str(self.__class__)).group(1)


class ENUUTask(ReScannerTask):
    def __init__(self, wiki: Site, debug: bool, logger: Logger):
        ReScannerTask.__init__(self, wiki, debug, logger)
        self.load_task()

    def task(self):
        self.text = re.sub(r'\n*\{\{REDaten.*?\n\}\}\s*', lambda x: self.replace_re(x), self.text, flags=re.DOTALL)
        self.text = re.sub(r'\n*\{\{REAutor.*?\}\}\s*', lambda x: self.replace_re(x), self.text, flags=re.DOTALL)
        self.text = re.sub(r'\n*\{\{REAbschnitt.*?\}\}\s*', lambda x: self.replace_re(x), self.text, flags=re.DOTALL)
        self.text = self.text.rstrip()
        if self.text[0] == '\n':
            self.text = self.text[1:]

    @staticmethod
    def replace_re(hit: re):
        return '\n' + hit.group(0).strip(" \n\t") + '\n'


class RERE_Task(ReScannerTask):
    def __init__(self, wiki: Site, debug: bool, logger: Logger):
        ReScannerTask.__init__(self, wiki, debug, logger)
        self.load_task()

    def task(self):
        self.text = re.sub(r'\{\{RE\|.{0,200}\}\}(?=\n| |\[)', lambda x: self.replace_re_redaten(x), self.text)
        self.text = re.sub(r'\{\{RE\/Platzhalter\|.{0,200}\}\}(?=\n| |\[)',
                           lambda x: self.replace_replatz_redatenplatz(x), self.text)
        self.text = re.sub(r'\{\{RENachtrag\|.{0,200}\}\}(?=\n| |\[)', lambda x: self.replace_renachtrag(x), self.text)
        self.text = re.sub(r'\{\{RENachtrag unfrei\|.{0,200}\}\}(?=\n| |\[)',
                           lambda x: self.replace_renachtrag_unfrei(x), self.text)

    def replace_re_redaten(self, hit: re):
        old_template = TemplateHandler(hit.group(0))
        old_parameters = old_template.get_parameterlist()
        new_parameters = list()
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_END', old_parameters, 2))
        self.set_off(new_parameters)
        if old_parameters[0]['value'][0] == 'S':
            new_parameters.append({'key': 'VORGÄNGER', 'value': ''})
            new_parameters.append({'key': 'NACHFOLGER', 'value': ''})
        else:
            new_parameters.append(self.get_parameter_if_possible('VORGÄNGER', old_parameters, 3))
            new_parameters.append(self.get_parameter_if_possible('NACHFOLGER', old_parameters, 4))
        new_parameters.append(self.get_parameter_if_possible('SORTIERUNG', old_parameters, 6))
        new_parameters.append(self.get_parameter_if_possible('KORREKTURSTAND', old_parameters, 7))
        new_parameters.append(self.get_parameter_if_possible('WIKIPEDIA', old_parameters, 8))
        new_parameters.append(self.get_parameter_if_possible('WIKISOURCE', old_parameters, 9))
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_START', old_parameters, 10))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_END', old_parameters, 11))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append(self.get_parameter_if_possible('GND', old_parameters, 12))
        new_template = TemplateHandler()
        new_template.set_title('REDaten')
        new_template.update_parameters(new_parameters)
        return new_template.get_str(str_complex=True)

    def replace_replatz_redatenplatz(self, hit: re):
        self.logger.info('Found re/Platzhalter')
        old_template = TemplateHandler(hit.group(0))
        old_parameters = old_template.get_parameterlist()
        new_parameters = list()
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_END', old_parameters, 2))
        self.set_off(new_parameters)
        if old_parameters[0]['value'][0] == 'S':
            new_parameters.append({'key': 'VORGÄNGER', 'value': ''})
            new_parameters.append({'key': 'NACHFOLGER', 'value': ''})
        else:
            new_parameters.append(self.get_parameter_if_possible('VORGÄNGER', old_parameters, 3))
            new_parameters.append(self.get_parameter_if_possible('NACHFOLGER', old_parameters, 4))
        new_parameters.append(self.get_parameter_if_possible('SORTIERUNG', old_parameters, 6))
        new_parameters.append(self.get_parameter_if_possible('GEMEINFREI', old_parameters, 7))
        new_parameters.append(self.get_parameter_if_possible('WIKIPEDIA', old_parameters, 8))
        new_parameters.append(self.get_parameter_if_possible('WIKISOURCE', old_parameters, 9))
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_START', old_parameters, 10))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_END', old_parameters, 11))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append(self.get_parameter_if_possible('GND', old_parameters, 12))
        new_template = TemplateHandler()
        new_template.set_title('REDaten/Platzhalter')
        new_template.update_parameters(new_parameters)
        return new_template.get_str(str_complex=True)

    def replace_renachtrag(self, hit: re):
        self.logger.info('Found RENachtrag')
        old_template = TemplateHandler(hit.group(0).strip())
        old_parameters = old_template.get_parameterlist()
        new_parameters = list()
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append({'key': 'SPALTE_END', 'value': ''})
        new_parameters.append({'key': 'VORGÄNGER', 'value': ''})
        new_parameters.append({'key': 'NACHFOLGER', 'value': ''})
        new_parameters.append(self.get_parameter_if_possible('SORTIERUNG', old_parameters, 3))
        if re.search('\|KORREKTURSTAND=[Ff]ertig', self.text):
            new_parameters.append({'key': 'KORREKTURSTAND', 'value': 'fertig'})
        else:
            new_parameters.append({'key': 'KORREKTURSTAND', 'value': ''})
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_START', old_parameters, 2))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append({'key': 'EXTSCAN_END', 'value': ''})
        new_parameters.append(self.get_parameter_if_possible('ÜBERSCHRIFT', old_parameters, 4))
        if new_parameters[-1]['value'] == 'Ü':
            new_parameters[-1]['value'] = 'ON'
        new_template = TemplateHandler()
        new_template.set_title('RENachtrag')
        new_template.update_parameters(new_parameters)
        return new_template.get_str(str_complex=True)

    def replace_renachtrag_unfrei(self, hit: re):
        self.logger.info('Found RENachtrag unfrei')
        old_template = TemplateHandler(hit.group(0).strip())
        old_parameters = old_template.get_parameterlist()
        new_parameters = list()
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append({'key': 'SPALTE_END', 'value': ''})
        new_parameters.append({'key': 'VORGÄNGER', 'value': ''})
        new_parameters.append({'key': 'NACHFOLGER', 'value': ''})
        new_parameters.append({'key': 'SORTIERUNG', 'value': ''})
        try:
            deathyear = int(old_parameters[4]['value'])
            new_parameters.append({'key': 'GEMEINFREI', 'value': str(deathyear + 71)})
        except:
            new_parameters.append({'key': 'GEMEINFREI', 'value': ''})
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_START', old_parameters, 2))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append({'key': 'EXTSCAN_END', 'value': ''})
        new_parameters.append(self.get_parameter_if_possible('ÜBERSCHRIFT', old_parameters, 5))
        if new_parameters[-1]['value'] == 'Ü':
            new_parameters[-1]['value'] = 'ON'
        new_template = TemplateHandler()
        new_template.set_title('RENachtrag/Platzhalter')
        new_template.update_parameters(new_parameters)
        return new_template.get_str(str_complex=True)

    @staticmethod
    def get_parameter_if_possible(name, old_parameters, old_position):
        if len(old_parameters) >= old_position + 1:
            return {'key': name, 'value': old_parameters[old_position]['value']}
        else:
            return {'key': name, 'value': ''}

    @staticmethod
    def set_off(template_list):
        if template_list[-1]['value'] == '':
            template_list[-1]['value'] = 'OFF'

    def devalidate_ext_scan(self, template_list):
        if not re.search(r'\{\{RE(?:IA|WL)[^\}]*?\}\}', template_list[-1]['value']):
            if template_list[-1]['value'] != '':
                self.logger.error('Extern Scan devalidated: {}'.format(template_list[-1]['value']))
            template_list[-1]['value'] = ''


class ReScanner(CanonicalBot):
    bot_name = 'ReScanner'

    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.lemma_list = None
        self.new_data_model = datetime(year=2016, month=11, day=8, hour=11)
        self.timeout = timedelta(seconds=60)  # bot should run only one minute ... don't do anything at the moment
        self.tasks = [ENÜUTask]
        if self.debug:
            self.tasks = self.tasks + []

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if not self.data:
            self.data = {}
        return self

    def compile_lemma_list(self):
        self.logger.info('Compile the lemma list')
        searcher = PetScan()
        searcher.add_any_template('REDaten')

        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
            searcher.add_positive_category('Fertig RE')
            searcher.add_positive_category('Korrigiert RE')
            searcher.add_positive_category('RE:Platzhalter')
            searcher.set_logic_union()
        self.logger.info('[{url} {url}]'.format(url=searcher))
        raw_lemma_list = searcher.run()
        # all items which wasn't process before
        new_lemma_list = [x['nstext'] + ':' + x['title'] for x in raw_lemma_list if
                          x['nstext'] + ':' + x['title'] not in list(self.data.keys())]
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=itemgetter(1))]
        self.lemma_list = new_lemma_list + old_lemma_list  # first iterate new items then the old ones (oldest first)

    def task(self):
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(self.wiki, self.debug, self.logger))
        self.compile_lemma_list()
        self.logger.info('Start processing the lemmas.')
        for lemma in self.lemma_list:
            list_of_done_tasks = []
            page = Page(self.wiki, lemma)
            self.logger.info('Process {}'.format(page))
            for task in active_tasks:
                if task.process_lemma(page):
                    list_of_done_tasks.append(task.get_name())
                    self.logger.info('Änderungen durch Task {} durchgeführt'.format(task.get_name()))
                    page.save('RE Scanner hat folgende Aufgaben bearbeitet: {}'.format(', '.join(list_of_done_tasks)),
                              botflag=True)
            self.data[lemma] = datetime.now().strftime('%Y%m%d%H%M%S')
            if self._watchdog():
                break
        for task in self.tasks:
            del task
        return True


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReScanner(wiki=wiki, debug=True) as bot:
        bot.run()
