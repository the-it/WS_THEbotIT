import re
from datetime import datetime, timedelta
from logging import Logger
from operator import itemgetter
from pywikibot import Page, Site
from tools.bots import CanonicalBot
from tools.catscan import PetScan
from tools.template_handler import TemplateHandler

class ReScannerTask():
    def __init__(self, wiki:Site, debug:bool, logger:Logger):
        self.reporter_page = None
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.text = ''
        self.task_name = 'basic_task'
        self.changed = False

    def __del__(self):
        self.finish_task()

    def preprocess_lemma(self, page:Page):
        self.logger.info('task {}'.format(self.task_name))
        self.text = page.text
        self.pretext = page.text
        self.changed = False

    def postprocess_lemma(self, page:Page):
        page.text = self.text

    def load_task(self):
        self.logger.info('opening {}'.format(self.task_name))

    def finish_task(self):
        self.logger.info('closing {}'.format(self.task_name))

    def text_changed(self):
        return self.text != self.pretext

    def get_name(self):
        return self.task_name


class ENÜU_Task(ReScannerTask):
    def __init__(self, wiki:Site, debug:bool, logger:Logger):
        ReScannerTask.__init__(self, wiki, debug, logger)
        self.task_name = 'ENÜU'
        self.load_task()

    def process_lemma(self, page:Page):
        self.preprocess_lemma(page)
        self.text = re.sub(r'\n*\{\{REDaten.*?\n\}\}\n*', lambda x: self.replace_re(x), self.text, flags=re.DOTALL)
        self.text = re.sub(r'\n*\{\{RENachtrag.*?\n\}\}\n*', lambda x: self.replace_re(x, True), self.text,
                           flags=re.DOTALL)
        self.text = re.sub(r'\n*\{\{REAutor.*?\}\}\n*', lambda x: self.replace_re(x, True), self.text,
                           flags=re.DOTALL)
        self.text = re.sub(r'\n*\{\{REAbschnitt.*?\}\}\n*', lambda x: self.replace_re(x, True), self.text,
                           flags=re.DOTALL)
        self.text = self.text.rstrip()
        self.postprocess_lemma(page)
        return self.text_changed()

    def replace_re(self, hit:re, leading_lf:bool=False):
        if leading_lf:
            return '\n' + hit.group(0).strip() + '\n'
        else:
            return hit.group(0).strip() + '\n'

class RERE_Task(ReScannerTask):
    def __init__(self, wiki:Site, debug:bool, logger:Logger):
        ReScannerTask.__init__(self, wiki, debug, logger)
        self.task_name = 'RERE'
        self.load_task()

    def process_lemma(self, page:Page):
        self.preprocess_lemma(page)
        self.text = re.sub(r'\{\{RE\|.{0,200}\}\}(?:\n|\[\[)', lambda x: self.replace_re_redaten(x), self.text)
        self.text = re.sub(r'\{\{RE/Platzhalter\|.{0,200}\}\}\n', lambda x: self.replace_replatz_redatenplatz(x), self.text)
        self.text = re.sub(r'\{\{RENachtrag\|.{0,200}\}\}[ \n]*', lambda x: self.replace_renachtrag(x), self.text)
        self.text = re.sub(r'\{\{RENachtrag unfrei\|.{0,200}\}\}[ \n]*', lambda x: self.replace_renachtrag_unfrei(x), self.text)
        self.postprocess_lemma(page)
        return self.text_changed()

    def replace_re_redaten(self, hit:re):
        old_template = TemplateHandler(hit.group(0))
        old_parameters = old_template.get_parameterlist()
        new_parameters = []
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_END', old_parameters, 2))
        self.set_off(new_parameters)
        if old_parameters[0]['value'][0] == 'S':
            new_parameters.append({'key':'VORGÄNGER','value': ''})
            new_parameters.append({'key':'NACHFOLGER','value': ''})
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

    def replace_replatz_redatenplatz(self, hit:re):
        self.logger.info('Found RE/Platzhalter')
        old_template = TemplateHandler(hit.group(0))
        old_parameters = old_template.get_parameterlist()
        new_parameters = []
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_END', old_parameters, 2))
        self.set_off(new_parameters)
        if old_parameters[0]['value'][0] == 'S':
            new_parameters.append({'VORGÄNGER': ''})
            new_parameters.append({'NACHFOLGER': ''})
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

    def replace_renachtrag(self, hit:re):
        self.logger.info('Found RENachtrag')
        old_template = TemplateHandler(hit.group(0).strip())
        old_parameters = old_template.get_parameterlist()
        new_parameters = []
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append({'key':'SPALTE_END', 'value':''})
        new_parameters.append({'key':'VORGÄNGER', 'value':''})
        new_parameters.append({'key':'NACHFOLGER', 'value':''})
        new_parameters.append(self.get_parameter_if_possible('SORTIERUNG', old_parameters, 3))
        if re.search('\|KORREKTURSTAND=[Ff]ertig', self.text):
            new_parameters.append({'key':'KORREKTURSTAND', 'value':'fertig'})
        else:
            new_parameters.append({'key': 'KORREKTURSTAND', 'value': ''})
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_START', old_parameters, 2))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append({'key':'EXTSCAN_END', 'value':''})
        new_parameters.append(self.get_parameter_if_possible('ÜBERSCHRIFT', old_parameters, 4))
        if new_parameters[-1]['value'] == 'Ü':
            new_parameters[-1]['value'] = 'ON'
        new_template = TemplateHandler()
        new_template.set_title('RENachtrag')
        new_template.update_parameters(new_parameters)
        return new_template.get_str(str_complex=True)

    def replace_renachtrag_unfrei(self, hit:re):
        self.logger.info('Found RENachtrag unfrei')
        old_template = TemplateHandler(hit.group(0).strip())
        old_parameters = old_template.get_parameterlist()
        new_parameters = []
        new_parameters.append(self.get_parameter_if_possible('BAND', old_parameters, 0))
        new_parameters.append(self.get_parameter_if_possible('SPALTE_START', old_parameters, 1))
        new_parameters.append({'key':'SPALTE_END', 'value':''})
        new_parameters.append({'key':'VORGÄNGER', 'value':''})
        new_parameters.append({'key':'NACHFOLGER', 'value':''})
        new_parameters.append({'key': 'SORTIERUNG', 'value': ''})
        try:
            deathyear = int(old_parameters[4]['value'])
            new_parameters.append({'key': 'GEMEINFREI', 'value': str(deathyear+71)})
        except:
            new_parameters.append({'key':'GEMEINFREI', 'value':''})
        new_parameters.append(self.get_parameter_if_possible('EXTSCAN_START', old_parameters, 2))
        self.devalidate_ext_scan(new_parameters)
        new_parameters.append({'key':'EXTSCAN_END', 'value':''})
        new_parameters.append(self.get_parameter_if_possible('ÜBERSCHRIFT', old_parameters, 5))
        if new_parameters[-1]['value'] == 'Ü':
            new_parameters[-1]['value'] = 'ON'
        new_template = TemplateHandler()
        new_template.set_title('RENachtrag/Platzhalter')
        new_template.update_parameters(new_parameters)
        return new_template.get_str(str_complex=True)

    def get_parameter_if_possible(self, name, old_parameters, old_position):
        if len(old_parameters) >= old_position + 1:
            return{'key': name, 'value': old_parameters[old_position]['value']}
        else:
            return {'key': name, 'value': ''}

    def set_off(self, template_list):
        if template_list[-1]['value'] == '':
            template_list[-1]['value'] = 'OFF'

    def devalidate_ext_scan(self, template_list):
        if not re.search(r'\{\{RE(?:IA|WL)[^\}]*?\}\}', template_list[-1]['value']):
            if template_list[-1]['value'] != '':
                self.logger.error('Extern Scan devalidated: {}'.format(template_list[-1]['value']))
            template_list[-1]['value'] = ''


class ReScanner(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'ReScanner'
        self.lemma_list = None
        self.new_data_model = datetime(year=2016, month=11, day=1, hour=15)
        self.timeout = timedelta(seconds=40000)
        self.tasks = [RERE_Task,
                      ENÜU_Task]
        if self.debug:
            self.tasks = self.tasks + []

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if self.data_outdated():
            self.data = None
            self.logger.warning('The data is thrown away. It is out of date')
        if not self.data:
            self.data = {}

    def compile_lemma_list(self):
        self.logger.info('Compile the lemma list')
        searcher = PetScan()
        searcher.add_any_template('RE')
        searcher.add_any_template('RE/Platzhalter')
        #searcher.add_any_template('REDaten')
        #searcher.add_any_template('REDaten/Platzhalter')
        #searcher.add_any_template('RENachtrag unfrei')

        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
            #searcher.add_positive_category('Fertig RE')
            #searcher.add_positive_category('Korrigiert RE')
            #searcher.add_positive_category('RE:Platzhalter')
            #searcher.set_logic_union()
        self.logger.info('[{url} {url}]'.format(url=searcher))
        raw_lemma_list = searcher.run()
        # all items which wasn't process before
        new_lemma_list = [x['nstext'] + ':' + x['title'] for x in raw_lemma_list if x['nstext'] + ':' + x['title'] not in list(self.data.keys())]
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=itemgetter(1))]
        return new_lemma_list + old_lemma_list

    def run(self):
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(self.wiki, self.debug, self.logger))
        self.lemma_list = self.compile_lemma_list()
        self.logger.info('Start processing the lemmas.')
        for lemma in set(self.lemma_list):
            changed = False
            list_of_done_tasks = []
            page = Page(self.wiki, lemma)
            self.logger.info('Process {}'.format(page))
            for task in active_tasks:
                if task.process_lemma(page):
                    changed = True
                    list_of_done_tasks.append(task.get_name())
            self.data[lemma] = datetime.now().strftime('%Y%m%d%H%M%S')
            if changed:
                self.logger.info('Änderungen auf der Seite {} durchgeführt'.format(page))
                page.save('RE Scanner hat folgende Aufgaben bearbeitet: {}'.format(', '.join(list_of_done_tasks)), botflag=True)
            if self._watchdog():
                break
        for task in self.tasks:
            del task
