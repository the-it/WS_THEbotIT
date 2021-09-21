import re
from typing import List

from tools._typing import TemplatePositionDict


class TemplateFinderException(Exception):
    pass


class TemplateFinder():
    def __init__(self, text_to_search: str):
        self.text = text_to_search

    def get_positions(self, template_name: str) -> List[TemplatePositionDict]:
        templates: List[TemplatePositionDict] = []
        for start_position_template in \
                self.get_start_positions_of_regex(r"\{\{" + template_name, self.text):
            pos_start_brackets = \
                self.get_start_positions_of_regex(r"\{\{", self.text[start_position_template + 2:])
            pos_start_brackets.reverse()
            pos_end_brackets = \
                self.get_start_positions_of_regex(r"\}\}", self.text[start_position_template + 2:])
            pos_end_brackets.reverse()
            open_brackets = 1
            while pos_end_brackets:
                if pos_start_brackets and (pos_end_brackets[-1] > pos_start_brackets[-1]):
                    open_brackets += 1
                    pos_start_brackets.pop(-1)
                else:
                    open_brackets -= 1
                    if open_brackets == 0:
                        # detected end of the template
                        end_position_template = pos_end_brackets[-1]
                        # add offset for start and end brackets
                        end_position_template += 4
                        # add start position (end only searched after)
                        end_position_template += start_position_template
                        templates.append({"pos": (start_position_template, end_position_template),
                                          "text": self.text[start_position_template:
                                                            end_position_template]})
                        break
                    pos_end_brackets.pop(-1)
            else:
                raise TemplateFinderException(f"No end of the template found for {template_name}")
        return templates

    @staticmethod
    def get_start_positions_of_regex(regex_pattern: str, text: str) -> List[int]:
        list_of_positions: List[int] = []
        for match in re.finditer(regex_pattern, text):
            list_of_positions.append(match.regs[0][0])  # type: ignore # false positive, there is the attribute regs
        return list_of_positions
