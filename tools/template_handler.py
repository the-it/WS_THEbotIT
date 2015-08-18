__author__ = 'Erik Sommer'

import re

class TemplateHandler:
    """

    """
    def __init__(self, template_str = ''):
        self.title = ''
        self.parameters = []
        if template_str:
            self._process_template_str(template_str)

    def _process_template_str(self, template_str):
        template_str = re.sub('\n', '', template_str)
        template_str = template_str[2:-2]
        self.title = re.search('[^\|]*', template_str).group()
        template_str = re.sub('\A[^\|]*\|', '', template_str)
        while template_str:
            if template_str[0] == '{': #argument is a template itself
                par_template = re.search('\A\{\{[^}]*\}\}', template_str).group()
                self.parameters.append({'key': None, 'value': par_template})
                template_str = re.sub('\A\{\{[^}]*\}\}\|?', '', template_str)
            elif re.match('\A[^\|]*\=[^\|]*', template_str):   #normal argument with a key
                if re.match('\A[^\{\{\|]*\=\{\{.*?\}\}', template_str): #an embedded template with a key
                    par_template = re.search('\A[^\{\{\|]*\=\{\{.*?\}\}', template_str).group()
                    par_template = re.split('=', par_template)
                    self.parameters.append({'key': par_template[0], 'value': par_template[1]})
                    template_str = re.sub('\A[^\{\{\|]*\=\{\{.*?\}\}\|?', '', template_str)
                else:   # a normal argument
                    par_template = re.search('\A[^\|]*\=[^\|]*', template_str).group()
                    par_template = re.sub('\|', '', par_template)
                    par_template = re.split('\=', par_template)
                    self.parameters.append({'key': par_template[0], 'value': par_template[1]})
                    template_str = re.sub('\A[^\|]*\=[^\|]*\|?', '', template_str)
            else: # an argument without a key
                par_template = re.search('\A[^\|]*', template_str).group()
                par_template = re.sub('\|', '', par_template)
                self.parameters.append({'key': None, 'value': par_template})
                template_str = re.sub('\A[^\|]*\|?', '', template_str)

    def get_parameterlist(self):
        return self.parameters

    def get_parameter(self, key):
        return [item for item in self.parameters if item["key"] == key][0]

    def get_str(self, str_complex = True):
        list_for_template = ['{{' + self.title]
        for parameter in self.parameters:
            if parameter['key']:
                list_for_template.append('|' + parameter['key'] + '=' + parameter['value'])
            else:
                list_for_template.append('|' + parameter['value'])
        list_for_template.append('}}')
        if str_complex:
            ret_str = '\n'
        else:
            ret_str = ''
        something = ret_str.join(list_for_template)
        return ret_str.join(list_for_template)

    def update_parameters(self, dict_parameters):
        self.parameters = dict_parameters

    def set_title(self, title):
        self.title = title