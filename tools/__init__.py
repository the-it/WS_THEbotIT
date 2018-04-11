class ToolException(Exception):
    pass


__all__ = ['ToolException', 'catscan', 'template_handler', 'abbyy_xml', 'bots', 'date_conversion',
           'make_html_color']


def make_html_color(min_value, max_value, value):
    if max_value > min_value:
        if value > min_value:
            if value < max_value:
                color = (1 - (value - min_value) / (max_value - min_value)) * 255
            else:
                color = 0
        else:
            color = 255
    else:
        if value > max_value:
            if value < min_value:
                color = ((value - max_value) / (min_value - max_value)) * 255
            else:
                color = 255
        else:
            color = 0
    return str(hex(round(color)))[2:].zfill(2).upper()
