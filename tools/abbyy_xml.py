__author__ = 'erik'

from xml.dom import minidom

class AbbyyXML:
    def __init__(self, xml_string):
        self.dom_obj = minidom.parseString(xml_string)

    def getText(self):
        return self.processDocument()

    def processDocument(self):
        page = self.dom_obj.getElementsByTagName("page")
        return self.processPage(page[0])

    def processPage(self, page_xml):
        blocks = page_xml.getElementsByTagName("block")
        blocks_string = []
        for block in blocks:
            blocks_string.append(self.processBlock(block))
        return "".join(blocks_string)

    def processBlock(self, block_xml):
        try:
            text = block_xml.getElementsByTagName("text")
            return self.processText(text[0])+"\n"
        except:
            return ""

    def processText(self, text_xml):
        pars = text_xml.getElementsByTagName("par")
        pars_string = []
        for par in pars:
            pars_string.append(self.processPar(par))
        return "".join(pars_string)

    def processPar(self, par_xml):
        lines = par_xml.getElementsByTagName("line")
        line_string = []
        for line in lines:
            line_string.append(self.processLine(line))
        line_string.append("\n")
        return "".join(line_string)

    def processLine(self, line_xml):
        formattings = line_xml.getElementsByTagName("formatting")
        formatting_string = []
        for formatting in formattings:
            formatting_string.append(self.processFormatting(formatting))
        formatting_string.append("\n")
        return "".join(formatting_string)

    def processFormatting(self, formatting_xml):
        char_params = formatting_xml.getElementsByTagName("charParams")
        chars_string = []
        for char_param in char_params:
            chars_string.append(self.processChar(char_param))
        return "".join(chars_string)

    def processChar(self, char_xml):
        return char_xml.childNodes[0].data



