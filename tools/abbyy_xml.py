__author__ = 'erik'

from xml.dom import minidom

class AbbyyXML:
    def __init__(self, xml_string):
        self.dom_obj = minidom.parseString(xml_string)

    def getText(self):
        try:
            return_text = self.processChar(self.dom_obj.childNodes)
        except:
            return_text = ''
        return return_text


    def processChar(self, char_xml):
        return char_xml[0].childNodes[0].data



