import re
from typing import List

from tools._typing import TemplateParameterDict, TemplateParameterList

REGEX_TITLE = r"\A[^\|]+"
REGEX_NO_KEY = r"\A[^\|]*"
REGEX_TEMPLATE = r"\A\{\{.*?\}\}"
REGEX_INTERWIKI = r"\A\[\[.*?\]\][^|\}]*"
REGEX_KEY = r"\A[^\|=\.\{]*=[^\|]*"
REGEX_KEY_EMBEDDED_TEMPLATE_OR_LINK = \
    r"\A([^\|=]*) ?= ?" \
    r"([^\|\[\{]|(\[\[)[^\|\]]*(\|.*?)*?(\]\])|(\{\{)[^\|\}]*(\|.*?)*?(\}\})|(\[.*?\]))*"
REGEX_TEMPLATE_LINK = r"\A[^\|]*(\{\{|\[\[)[^\|]*\|"


class TemplateHandlerException(Exception):
    pass


class TemplateHandler:
    def __init__(self, template_str: str = ''):
        self.title: str = ''
        self.parameters: TemplateParameterList = []
        if template_str:
            self._process_template_str(template_str)

    def _process_template_str(self, template_str: str):
        template_str = re.sub("\n", '', template_str)  # get rid of all linebreaks
        template_str = template_str[2:-2]  # get rid of the surrounding brackets
        match = re.search(REGEX_TITLE, template_str)
        if match:
            self.title = match.group()  # extract the title
        else:
            raise TemplateHandlerException("First Character is |, there is no title")
        template_str = re.sub(self.title + r"\|?", '', template_str)  # get rid of the title

        while template_str:  # analyse the arguments
            if template_str[0] == "{":  # argument is a template itself
                template_str = self._save_argument(REGEX_TEMPLATE, template_str, False)
            elif template_str[0] == "[":  # argument is a link in the wiki
                template_str = self._save_argument(REGEX_INTERWIKI, template_str, False)
            elif re.match(REGEX_KEY, template_str):  # argument with a key
                # an embedded template or link with a key
                if re.match(REGEX_TEMPLATE_LINK, template_str):
                    template_str = self._save_argument(REGEX_KEY_EMBEDDED_TEMPLATE_OR_LINK,
                                                       template_str, True)
                else:  # a normal argument with a key
                    template_str = self._save_argument(REGEX_KEY, template_str, True)
            else:  # an argument without a key
                template_str = self._save_argument(REGEX_NO_KEY, template_str, False)

    def get_parameterlist(self) -> TemplateParameterList:
        return self.parameters

    def get_parameter(self, key) -> TemplateParameterDict:
        return [item for item in self.parameters if item["key"] == key][0]

    def get_str(self, str_complex: bool = True) -> str:
        list_for_template: List[str] = ["{{" + self.title]
        for parameter in self.parameters:
            if parameter["key"]:
                list_for_template.append(f"|{parameter['key']}={parameter['value']}")
            else:
                list_for_template.append(f"|{parameter['value']}")
        list_for_template.append("}}")
        if str_complex:
            ret_str = "\n"
        else:
            ret_str = ''
        return ret_str.join(list_for_template)

    def update_parameters(self, dict_parameters: TemplateParameterList):
        self.parameters = dict_parameters

    def set_title(self, title: str):
        self.title = title

    @staticmethod
    def _cut_spaces(raw_string: str) -> str:
        return re.sub(r"(\A | \Z)", "", raw_string)

    def _save_argument(self, search_pattern: str, template_str: str, has_key: bool) -> str:
        par_template_match = re.search(search_pattern, template_str)
        if par_template_match:
            par_template = par_template_match.group()
            if has_key is True:
                par_template_match = re.search(r"\A([^=]*) ?= ?(.*)\Z", par_template)
                if par_template_match:
                    self.parameters.append({"key": self._cut_spaces(par_template_match.group(1)),
                                            "value": self._cut_spaces(par_template_match.group(2))})
            else:
                self.parameters.append({"key": None, "value": self._cut_spaces(par_template)})
        else:
            raise TemplateHandlerException(f"Cannot save {template_str} "
                                           f"with pattern {search_pattern}, should not happen.")
        return re.sub(search_pattern + r"\|?", "", template_str)
