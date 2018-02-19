import re

REGEX_TITLE = r'\A[^\|]*'
REGEX_NO_KEY = r'\A[^\|]*'
REGEX_TEMPLATE = r'\A\{\{.*?\}\}'
REGEX_INTERWIKI = r'\A\[\[.*?\]\][^|\}]*'
REGEX_KEY = r'\A[^\|=\.\{]*=[^\|]*'
REGEX_KEY_EMBEDDED_TEMPLATE_OR_LINK = \
    r'\A([^\|=]*) ?= ?([^\|\[\{]|(\[\[)[^\|\]]*(\|.*?)*?(\]\])|(\{\{)[^\|\}]*(\|.*?)*?(\}\})|(\[.*?\]))*'
REGEX_TEMPLATE_LINK = r'\A[^\|]*(\{\{|\[\[)[^\|]*\|'


class TemplateHandler:
    def __init__(self, template_str=''):
        '''

        :param template_str:
        :return:
        '''
        self.title = ''
        self.parameters = []
        if template_str:
            self._process_template_str(template_str)

    def _process_template_str(self, template_str: str):
        template_str = re.sub('\n', '', template_str)  # get rid of all linebreaks
        template_str = template_str[2:-2]  # get rid of the surrounding brackets
        self.title = re.search(REGEX_TITLE, template_str).group()  # extract the title
        template_str = re.sub(self.title + r'\|?', '', template_str)  # get rid of the title

        while template_str:  # analyse the arguments
            if template_str[0] == '{':  # argument is a template itself
                template_str = self._save_argument(REGEX_TEMPLATE, template_str, False)
            elif template_str[0] == '[':  # argument is a link in the wiki
                template_str = self._save_argument(REGEX_INTERWIKI, template_str, False)
            elif re.match(REGEX_KEY, template_str):  # argument with a key
                if re.match(REGEX_TEMPLATE_LINK, template_str):  # an embedded template or link with a key
                    template_str = self._save_argument(REGEX_KEY_EMBEDDED_TEMPLATE_OR_LINK, template_str, True)
                else:  # a normal argument with a key
                    template_str = self._save_argument(REGEX_KEY, template_str, True)
            else:  # an argument without a key
                template_str = self._save_argument(REGEX_NO_KEY, template_str, False)

    def get_parameterlist(self):
        return self.parameters

    def get_parameter(self, key):
        return [item for item in self.parameters if item["key"] == key][0]

    def get_str(self, str_complex=True):
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
        return re.sub(r"(\A[ ]|[ ]\Z)", "", raw_string)

    def _save_argument(self, search_pattern, template_str, has_key):
        par_template = re.search(search_pattern, template_str).group()
        if has_key is True:
            par_template = re.search(r"\A([^\=]*)[ ]?=[ ]?(.*)\Z", par_template)
            self.parameters.append({'key': self._cut_spaces(par_template.group(1)),
                                    'value': self._cut_spaces(par_template.group(2))})
        else:
            self.parameters.append({'key': None, 'value': self._cut_spaces(par_template)})
        return re.sub(search_pattern + r"\|?", "", template_str)


class TemplateFinderException(Exception):
    pass


class TemplateFinder(object):
    def __init__(self, text_to_search: str):
        self.text = text_to_search

    def get_positions(self, template_name: str):
        templates = list()
        for start_position_template in self.get_start_positions_of_regex(r"\{\{" + template_name, self.text):
            pos_start_brackets = self.get_start_positions_of_regex(r"\{\{", self.text[start_position_template + 2:])
            pos_start_brackets.reverse()
            pos_end_brackets = self.get_start_positions_of_regex(r"\}\}", self.text[start_position_template + 2:])
            pos_end_brackets.reverse()
            open_brackets = 1
            while pos_end_brackets:
                if pos_start_brackets and (pos_end_brackets[-1] > pos_start_brackets[-1]):
                    open_brackets += 1
                    pos_start_brackets.pop(-1)
                else:
                    open_brackets -= 1
                    if open_brackets == 0:
                        end_position_template = pos_end_brackets[-1]  # detected end of the template
                        end_position_template += 4  # add offset for start and end brackets
                        end_position_template += start_position_template  # add start position (end only searched after)
                        templates.append({"pos": (start_position_template, end_position_template),
                                          "text": self.text[start_position_template:end_position_template]})
                        break
                    pos_end_brackets.pop(-1)
            else:
                raise TemplateFinderException("No end of the template found for {}".format(template_name))
        return templates

    @staticmethod
    def get_start_positions_of_regex(regex_pattern: str, text: str):
        list_of_positions = list()
        for match in re.finditer(regex_pattern, text):
            list_of_positions.append(match.regs[0][0])
        return list_of_positions
