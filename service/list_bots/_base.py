import re

from typing_extensions import Optional

from tools.template_finder import TemplateFinder, TemplateFinderException
from tools.template_handler import TemplateHandlerException, TemplateHandler

_SPACE_REGEX = re.compile(r"\s+")


def _strip_spaces(raw_string: str):
    return _SPACE_REGEX.subn(raw_string.strip(), " ")[0]


def get_single_page_info(info: str, template_str: str, extractor: TemplateHandler,
                         info_dict: dict):
    try:
        info_dict[info] = _strip_spaces(extractor.get_parameter(template_str)["value"])
    except TemplateHandlerException:
        info_dict[info] = ""


def get_page_infos(text: str, template_name: str, property_mapping: dict[str, str]) -> dict:
    template_finder = TemplateFinder(text)
    try:
        text_daten = template_finder.get_positions(template_name)
    except TemplateFinderException as error:
        raise ValueError(f"Error in processing {template_name} template.") from error
    if len(text_daten) != 1:
        raise ValueError(f"No or more then one {template_name} template found.")
    template_extractor = TemplateHandler(text_daten[0].text)
    return_dict: dict[str, str] = {}
    for key, value in property_mapping.items():
        get_single_page_info(key, value, template_extractor, return_dict)
    return return_dict


def is_empty_value(key: str, dict_to_check: dict) -> bool:
    return (key not in dict_to_check) or (not dict_to_check[key])


def has_value(key: str, dict_to_check: dict) -> bool:
    return not is_empty_value(key, dict_to_check)


def assign_value(key: str, value: Optional[str], dict_to_assign: dict):
    if value:
        dict_to_assign[key] = value
    else:
        dict_to_assign[key] = ""
