import defusedxml
from defusedxml import minidom


class AbbyyXML:
    def __init__(self, xml_string):
        defusedxml.defuse_stdlib()
        self.dom_obj = minidom.parseString(xml_string)

    def get_text(self):
        return self.process_document()

    def process_document(self):
        page = self.dom_obj.getElementsByTagName("page")
        return self.process_page(page[0])

    @staticmethod
    def _process_child_items_with_function(child_name: str,
                                           child_xml,
                                           child_handler_function,
                                           append_new_line: bool = True):
        childes = child_xml.getElementsByTagName(child_name)
        childes_string = []
        for child in childes:
            childes_string.append(child_handler_function(child))
        if append_new_line:
            childes_string.append("\n")
        return "".join(childes_string)

    def process_page(self, page_xml):
        return self._process_child_items_with_function("block", page_xml, self.process_block,
                                                       append_new_line=False)

    def process_block(self, block_xml):
        return self._process_child_items_with_function("text", block_xml, self.process_text,
                                                       append_new_line=True)

    def process_text(self, text_xml):
        return self._process_child_items_with_function("par", text_xml, self.process_par,
                                                       append_new_line=False)

    def process_par(self, par_xml):
        return self._process_child_items_with_function("line", par_xml, self.process_line,
                                                       append_new_line=True)

    def process_line(self, line_xml):
        return self._process_child_items_with_function("formatting", line_xml,
                                                       self.process_formatting,
                                                       append_new_line=False)

    def process_formatting(self, formatting_xml):
        return self._process_child_items_with_function("charParams", formatting_xml,
                                                       self.process_char, append_new_line=False)

    @staticmethod
    def process_char(char_xml):
        return char_xml.childNodes[0].data
