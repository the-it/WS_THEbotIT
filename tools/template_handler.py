__author__ = 'Erik Sommer'

import re

regex_title = '\A[^\|]*'
regex_no_key = '\A[^\|]*'
regex_template = '\A\{\{.*?\}\}'
regex_interwiki = '\A\[\[.*?\]\][^|\}]*'
regex_key = '\A[^\|=\.\{]*=[^\|]*'
regex_key_embedded_template_or_link = '\A([^\|=]*) ?= ?([^\|\[\{]|(\[\[)[^\|\]]*(\|.*?)*?(\]\])|(\{\{)[^\|\}]*(\|.*?)*?(\}\}))*'
regex_template_link = '\A[^\|]*(\{\{|\[\[)[^\|]*\|'


class TemplateHandler:
    """

    """
    def __init__(self, template_str=''):
        '''

        :param template_str:
        :return:
        '''
        self.title = ''
        self.parameters = []
        if template_str:
            self._process_template_str(template_str)

    def _process_template_str(self, template_str):
        template_str = re.sub('\n', '', template_str)  #get rid of all linebreaks
        template_str = template_str[2:-2]  #get rid of the surrounding brackets
        self.title = re.search(regex_title, template_str).group()  #extract the title
        template_str = re.sub(regex_title +'\|', '', template_str)  #get rid of the title

        while template_str:  #analyse the arguments
            if template_str[0] == '{':  #argument is a template itself
                template_str = self._save_argument(regex_template, template_str, False)
            elif template_str[0] == '[':  #argument is a link in the wiki
                template_str = self._save_argument(regex_interwiki, template_str, False)
            elif re.match(regex_key, template_str):  #argument with a key
                if re.match(regex_template_link, template_str): #an embedded template or link with a key
                    template_str = self._save_argument(regex_key_embedded_template_or_link, template_str, True)
                else:  # a normal argument with a key
                    template_str = self._save_argument(regex_key, template_str, True)
            else:  # an argument without a key
                template_str = self._save_argument(regex_no_key, template_str, False)

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
        return ret_str.join(list_for_template)

    def update_parameters(self, dict_parameters):
        self.parameters = dict_parameters

    def set_title(self, title):
        self.title = title

    @staticmethod
    def _cut_spaces(raw_string):
        return re.sub("(\A[ ]|[ ]\Z)", "", raw_string)

    def _save_argument(self, search_pattern, template_str, has_key):
        par_template = re.search(search_pattern, template_str).group()
        if has_key is True:
            par_template = re.search("\A([^\=]*)[ ]?=[ ]?(.*)\Z", par_template)
            self.parameters.append({'key': self._cut_spaces(par_template.group(1)),
                                    'value': self._cut_spaces(par_template.group(2))})
        else:
            self.parameters.append({'key': None, 'value': self._cut_spaces(par_template)})
        return re.sub(search_pattern + "\|?", "", template_str)
