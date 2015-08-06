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
        template_str = re.sub('[\{\}\n]', '', template_str)
        parameter_list = re.split('\|', template_str)
        self.title = parameter_list.pop(0)
        for parameter in parameter_list:
            data = re.split('=', parameter)
            if len(data) == 1:
                self.parameters.append({'key': None, 'value': data[0]})
            else:
                self.parameters.append({'key': data[0], 'value': data[1]})

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