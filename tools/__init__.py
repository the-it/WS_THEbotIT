class ToolException(Exception):
    pass


__all__ = ['ToolException', 'catscan', 'template_handler', 'abbyy_xml', 'bots', 'date_conversion',
           'make_html_color']


def make_html_color(min_value, max_value, value):
    if max_value >= min_value:
        color = (1 - (value - min_value) / (max_value - min_value)) * 255
    else:
        color = ((value - max_value) / (min_value - max_value)) * 255
    color = max(0, min(255, color))
    return str(hex(round(color)))[2:].zfill(2).upper()
